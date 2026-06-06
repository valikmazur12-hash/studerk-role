import json
import threading
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from .models import UserList, DictPos, RoleD, Dictapplic, GroupD, UserRole, Department
from django.contrib import messages
from django.db import connection  
from django.core.mail import send_mail
from django.conf import settings  
from django.core.signing import Signer, BadSignature    

# ====================================================================
# АВТЕНТИФІКАЦІЯ ТА АВТОРИЗАЦІЯ (ВХІД / РЕЄСТРАЦІЯ / ВИХІД)
# ====================================================================

def login_view(request):
    """ Контролер входу в систему за логіном і паролем """
    if request.user.is_authenticated:
        return redirect('index')
        
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('index')
    else:
        form = AuthenticationForm()
    return render(request, 'main/login.html', {'form': form})


def register_view(request):
    """ Контролер форми реєстрації з авто-інкрементом ID (211, 212...) та захистом кодом """
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        # 1. ЖОРСТКИЙ ЗАХИСТ: Перевірка секретного коду (чисто як захисний інвайт від сторонніх)
        custom_id = request.POST.get('custom_id', '').strip()
        if custom_id != '221223':
            messages.error(request, 'Помилка: Невірний секретний код доступу СІТ! Реєстрація заблокована.')
            form = UserCreationForm(request.POST)
            return render(request, 'main/register.html', {'form': form})
            
        # 2. Стандартна валідація користувача Django
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            default_dep = Department.objects.filter(id_dep=1).first() or Department.objects.first()
            if not default_dep:
                default_dep = Department.objects.create(name_dep="Служба інформаційних технологій")
            
            # 🚀 ОНОВЛЕНО: Розумний пошук посади за замовчуванням, щоб не ставити Директора
            default_pos = DictPos.objects.filter(name_pos__icontains='розробник').first() or \
                          DictPos.objects.filter(name_pos__icontains='інженер').first() or \
                          DictPos.objects.filter(id_pos=103).first() or \
                          DictPos.objects.first()
            
            # 🚀 ОНОВЛЕНО: НЕ передаємо id_user вручну! База сама поставить авто-інкремент (211, 212, 213...)
            new_profile = UserList.objects.create(
                auth_user=user,
                id_pos=default_pos,
                id_dep=default_dep,
                prizvische=request.POST.get('prizvische', user.username),
                name=request.POST.get('name', ''),
                father_name=request.POST.get('father_name', ''),
                date_begin='2026-06-05'
            )
            
            # 🚀 ВІДПРАВКА ЛИСТА ПРО РЕЄСТРАЦІЮ
            try:
                subject = 'STUDERK: Успішна реєстрація нового співробітника СІТ'
                message = (
                    f"Вітаємо! У системі STUDERK створено новий профіль через захищений інвайт.\n\n"
                    f"Співробітник: {new_profile.prizvische} {new_profile.name}\n"
                    f"Логін в системі: {user.username}\n"
                    f"Присвоєно системний ID в БД: {new_profile.id_user}\n"
                )
                # Виставляємо fail_silently=False, щоб бачити помилки в логах сервера, якщо пошта ляже
                send_mail(subject, message, settings.EMAIL_HOST_USER, ['valikmazur12@gmail.com'], fail_silently=False)
            except Exception as mail_err:
                print(f"!!! Помилка відправки пошти при реєстрації: {mail_err}")
            
            messages.success(request, f'Користувача {user.username} успішно зареєстровано! Системний ID: {new_profile.id_user}')
            login(request, user)
            return redirect('index')
        else:
            messages.error(request, 'Помилка реєстрації. Перевірте правильність введення даних.')
    else:
        form = UserCreationForm()
    return render(request, 'main/register.html', {'form': form})


def logout_view(request):
    """ Вихід із системи та очищення сесії """
    logout(request)
    return redirect('login')


# ====================================================================
# ФУНКЦІОНАЛЬНІ СТОРІНКИ СИСТЕМИ
# ====================================================================

@login_required(login_url='login')
def role_assignment_view(request):
    """ ФУНКЦІЯ 1: ГОЛОВНА СТОРІНКА - Генерує токен та надсилає лист у фоновому потоці (без таймаутів) """
    
    if request.method == 'POST':
        user_id = request.POST.get('id_user') or request.POST.get('user') or request.POST.get('user_id')
        role_id = request.POST.get('id_role') or request.POST.get('role') or request.POST.get('role_id')
        
        if user_id and role_id:
            try:
                user_obj = UserList.objects.get(pk=user_id)
                role_obj = RoleD.objects.get(pk=role_id)
                
                # Попередня перевірка: чи немає такої ролі вже в базі
                with connection.cursor() as cursor:
                    try:
                        cursor.execute('SELECT 1 FROM "User_role" WHERE id_user = %s AND id_role = %s', [user_id, role_id])
                        exists = cursor.fetchone()
                    except:
                        cursor.execute('SELECT 1 FROM user_role WHERE id_user = %s AND id_role = %s', [user_id, role_id])
                        exists = cursor.fetchone()
                
                if exists:
                    messages.warning(request, f'Співробітник {user_obj.prizvische} вже має роль "{role_obj.name}".')
                    return redirect('index')

                # Створюємо захищений тимчасовий токен
                signer = Signer()
                token = signer.sign(f"{user_id}:{role_id}")
                confirm_link = request.build_absolute_uri(f"/confirm-role/{token}/")
                
                # Текст листа
                subject = '🔐 STUDERK: Запит на підтвердження матричної ролі'
                message = (
                    f"У системі розмежування ролей STUDERK сформовано запит на нові права доступу.\n\n"
                    f"Співробітник: {user_obj.prizvische} {user_obj.name} (ID: {user_obj.id_user})\n"
                    f"Посада підрозділу: {user_obj.id_pos.name_pos if user_obj.id_pos else 'Не вказано'}\n"
                    f"Матрична роль: {role_obj.name}\n\n"
                    f"👉 ЩОБ ПІДТВЕРДИТИ ПРИЗНАЧЕННЯ ТА ВНЕСТИ ДАНІ В БАЗУ, КЛІКНІТЬ ЗА ПОСИЛАННЯМ:\n"
                    f"{confirm_link}\n\n"
                    f"Якщо ви не здійснювали цю дію на сайті, просто проігноруйте цей лист."
                )

                # 🚀 ВНУТРІШНЯ ФУНКЦІЯ ДЛЯ ФОНОВОГО ПОТОКУ
                def send_email_bg(sub, msg, from_mail, to_mail):
                    try:
                        send_mail(sub, msg, from_mail, to_mail, fail_silently=False)
                        print(f"✅ Фоновий лист для {user_obj.prizvische} успішно надіслано через SMTP!")
                    except Exception as mail_err:
                        # Помилка запишеться в логи Render, але користувач на сайті її не побачить і сайт не впаде
                        print(f"!!! Помилка фонової відправки пошти: {mail_err}")

                # 🚀 ЗАПУСКАЄМО ПАРАЛЕЛЬНИЙ ПОТІК (Thread)
                # Код нижче виконається миттєво, а відправка листа піде «своєю дорогою» паралельно
                thread = threading.Thread(
                    target=send_email_bg, 
                    args=(subject, message, settings.EMAIL_HOST_USER, ['valikmazur12@gmail.com'])
                )
                thread.daemon = True  # Дозволяємо потоку працювати незалежно
                thread.start()

                # Миттєво повертаємо успіх на екран користувачу
                messages.success(request, f'Запит для {user_obj.prizvische} успішно сформовано! Перевірте пошту valikmazur12@gmail.com для активації.')
                
            except Exception as e:
                messages.error(request, f'Помилка обробки запиту: {e}')
        else:
            messages.error(request, 'Помилка: Форма не передала ID користувача або ролі.')
                
        return redirect('index')

    # GET логіка автозаповнення (без змін)
    user_data = UserList.objects.select_related('id_pos').all()
    user_list_json = [
        {
            'id_user': user.id_user, 
            'Prizvische': str(user.prizvische) if user.prizvische else '',
            'Name': str(user.name) if user.name else '',
            'Father_Name': str(user.father_name) if user.father_name else '',
            'Position': str(user.id_pos.name_pos) if user.id_pos else 'Не визначено',
        }
        for user in user_data
    ]
    context = {'user_data_json': json.dumps(user_list_json, ensure_ascii=False)}
    return render(request, 'main/data_view.html', context)


# 🚀 НОВА ФУНКЦІЯ: Обробляє клік із листа і тільки тепер робить запис у PostgreSQL
def confirm_role_view(request, token):
    """ Контролер, який активується ТІЛЬКИ при переході за посиланням з листа """
    signer = Signer()
    try:
        # Розшифровуємо секретний токен назад у ID юзера та ролі
        data = signer.unsign(token)
        user_id, role_id = data.split(':')
        
        user_obj = UserList.objects.get(pk=user_id)
        role_obj = RoleD.objects.get(pk=role_id)
        
        created = False
        # Використовуємо наш Raw SQL хак, оскільки в User_role немає стовпця 'id'
        with connection.cursor() as cursor:
            try:
                cursor.execute('SELECT 1 FROM "User_role" WHERE id_user = %s AND id_role = %s', [user_id, role_id])
                exists = cursor.fetchone()
            except:
                cursor.execute('SELECT 1 FROM user_role WHERE id_user = %s AND id_role = %s', [user_id, role_id])
                exists = cursor.fetchone()
                
            if not exists:
                try:
                    cursor.execute('INSERT INTO "User_role" (id_user, id_role) VALUES (%s, %s)', [user_id, role_id])
                except:
                    cursor.execute('INSERT INTO user_role (id_user, id_role) VALUES (%s, %s)', [user_id, role_id])
                created = True
        
        if created:
            messages.success(request, f'🎉 Авторизація успішна! Роль "{role_obj.name}" офіційно активована для {user_obj.prizvische}.')
        else:
            messages.warning(request, f'Цей співробітник вже отримав роль "{role_obj.name}" раніше.')
            
    except BadSignature:
        messages.error(request, 'Помилка безпеки: Посилання підроблене, недійсне або його термін дії закінчився!')
    except Exception as e:
        messages.error(request, f'Критична помилка активації права: {e}')
        
    return redirect('index')


@login_required(login_url='login')
def page_two_view(request):
    """ ФУНКЦІЯ 2: СТОРІНКА ЗВІТІВ (tabl_d.html) """
    apps_pool = {a.id_applic: a.app_name for a in Dictapplic.objects.all()}
    groups_pool = {g.id_group: g.id_app_id for g in GroupD.objects.all()}
    roles_pool = {}
    for r in RoleD.objects.all():
        roles_pool[r.id_role] = {
            'name': r.name,
            'app_name': apps_pool.get(groups_pool.get(r.id_group_id), 'Без додатка')
        }
        
    user_roles_relations = []
    with connection.cursor() as cursor:
        try:
            cursor.execute('SELECT id_user, id_role FROM "User_role"')
            user_roles_relations = cursor.fetchall()
        except:
            cursor.execute('SELECT id_user, id_role FROM user_role')
            user_roles_relations = cursor.fetchall()

    user_to_roles_map = {}
    for u_id, r_id in user_roles_relations:
        if u_id not in user_to_roles_map:
            user_to_roles_map[u_id] = []
        role_info = roles_pool.get(r_id)
        if role_info:
            user_to_roles_map[u_id].append({
                'application': str(role_info['app_name']),
                'role_name': str(role_info['name'])
            })

    users_queryset = UserList.objects.select_related('id_pos').all()
    report_data = []
    for user in users_queryset:
        p_prizv = str(user.prizvische) if user.prizvische else ""
        p_name = str(user.name) if user.name else ""
        p_fath = str(user.father_name) if user.father_name else ""
        
        pib = f"{p_prizv} {p_name} {p_fath}".strip()
        if not pib:
            pib = user.auth_user.username if user.auth_user else f"Користувач ID {user.id_user}"
            
        position_name = str(user.id_pos.name_pos) if user.id_pos else 'Не визначено'
        roles_for_display = user_to_roles_map.get(user.id_user, [])
        
        report_data.append({
            'id_user': user.id_user,
            'pib': pib,
            'position': position_name,
            'roles_data': roles_for_display
        })

    return render(request, 'main/tabl_d.html', {'report_data': report_data})


@login_required(login_url='login')
def page_three_view(request):
    """ ФУНКЦІЯ 3: СХЕМА (schem.html) """
    return render(request, 'main/schem.html', {})


@login_required(login_url='login')
def page_four_view(request):
    """ ФУНКЦІЯ 4: ПРОФІЛЬ ТА ЗАПИТ РОЛІ (you_user.html) """
    apps_pool = {a.id_applic: a.app_name for a in Dictapplic.objects.all()}
    groups_pool = {g.id_group: g.id_app_id for g in GroupD.objects.all()}
    roles_pool = {}
    for r in RoleD.objects.all():
        roles_pool[r.id_role] = {
            'name': r.name,
            'app_name': apps_pool.get(groups_pool.get(r.id_group_id), 'Без додатка')
        }

    user_roles_relations = []
    with connection.cursor() as cursor:
        try:
            cursor.execute('SELECT id_user, id_role FROM "User_role"')
            user_roles_relations = cursor.fetchall()
        except:
            cursor.execute('SELECT id_user, id_role FROM user_role')
            user_roles_relations = cursor.fetchall()

    users_raw = UserList.objects.select_related('id_pos').all()
    all_users = []
    user_roles_map = {str(u.id_user): [] for u in users_raw}
    
    for u_id, r_id in user_roles_relations:
        str_u_id = str(u_id)
        if str_u_id in user_roles_map:
            role_info = roles_pool.get(r_id)
            if role_info:
                user_roles_map[str_u_id].append({
                    'app': str(role_info['app_name']),
                    'role': str(role_info['name'])
                })

    for u in users_raw:
        p_prizv = str(u.prizvische) if u.prizvische else ""
        p_name = str(u.name) if u.name else ""
        p_fath = str(u.father_name) if u.father_name else ""
        
        all_users.append({
            'id_user': u.id_user,
            'prizvische': p_prizv if p_prizv else (u.auth_user.username if u.auth_user else "Користувач"),
            'name': p_name,
            'father_name': p_fath,
            'id_pos__name_pos': str(u.id_pos.name_pos) if u.id_pos else 'Не визначено'
        })

    context = {
        'all_users': all_users,
        'user_roles_json': json.dumps(user_roles_map, ensure_ascii=False)
    }
    return render(request, 'main/you_user.html', context)