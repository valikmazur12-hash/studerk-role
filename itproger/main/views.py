import json
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from .models import UserList, DictPos, RoleD, Dictapplic, GroupD, UserRole, Department
from django.contrib import messages
from django.db import connection  # 🚀 Пряме підключення до ядра БД для обходу відсутнього 'id'

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
    """ Контролер форми реєстрації нового користувача підрозділу """
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            default_dep = Department.objects.first()
            default_pos = DictPos.objects.first()
            
            if not default_dep:
                default_dep = Department.objects.create(name_dep="Служба інформаційних технологій")
            
            UserList.objects.create(
                auth_user=user,
                id_pos=default_pos,
                id_dep=default_dep,
                prizvische=request.POST.get('prizvische', user.username),
                name=request.POST.get('name', ''),
                father_name=request.POST.get('father_name', ''),
                date_begin='2026-06-05'
            )
            
            messages.success(request, f'Користувача {user.username} успішно зареєстровано в системі STUDERK!')
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
    """ ФУНКЦІЯ 1: ГОЛОВНА СТОРІНКА (data_view.html) - Автозаповнення """
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
    json_data = json.dumps(user_list_json, ensure_ascii=False)

    context = {
        'user_data_json': json_data
    }
    return render(request, 'main/data_view.html', context)


@login_required(login_url='login')
def page_two_view(request):
    """ ФУНКЦІЯ 2: СТОРІНКА ЗВІТІВ (tabl_d.html) """
    
    # 1. Створюємо пули додатків, груп та ролей, обходячи внутрішні баги зв'язків
    apps_pool = {a.id_applic: a.app_name for a in Dictapplic.objects.all()}
    groups_pool = {g.id_group: g.id_app_id for g in GroupD.objects.all()}
    roles_pool = {}
    for r in RoleD.objects.all():
        roles_pool[r.id_role] = {
            'name': r.name,
            'app_name': apps_pool.get(groups_pool.get(r.id_group_id), 'Без додатка')
        }
        
    # 2. ХАК: Витягуємо зв'язки з проміжної таблиці через RAW SQL без згадки поля "id"
    user_roles_relations = []
    with connection.cursor() as cursor:
        try:
            cursor.execute('SELECT id_user, id_role FROM "User_role"')
            user_roles_relations = cursor.fetchall()
        except:
            # Резервний варіант на випадок автоматичного нижнього регістру таблиць в pgAdmin
            cursor.execute('SELECT id_user, id_role FROM user_role')
            user_roles_relations = cursor.fetchall()

    # Групуємо ролі по ID користувачів
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

    # 3. Формуємо фінальний звіт
    users_queryset = UserList.objects.select_related('id_pos').all()
    report_data = []
    for user in users_queryset:
        p_prizv = str(user.prizvische) if user.prizvische else ""
        p_name = str(user.name) if user.name else ""
        p_fath = str(user.father_name) if user.father_name else ""
        
        pib = f"{p_prizv} {p_name} {p_fath}".strip()
        if not pib:
            pib = user.auth_user.username if user.auth_user else f"Користевач ID {user.id_user}"
            
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
    
    # Наповнюємо мапу ролей для JS скриптів профілю
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