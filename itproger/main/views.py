# main/views.py
import json
from django.shortcuts import render, redirect
from django.db import IntegrityError
from .models import UserList, DictPos, RoleD, Dictapplic, GroupD, UserRole 

# ====================================================================
# ФУНКЦІЯ 1: ГОЛОВНА СТОРІНКА (data_view.html) - Автозаповнення
# ====================================================================

def role_assignment_view(request):
    """ Отримує дані користувачів та посад, формує JSON для JavaScript. """
    
    user_data = UserList.objects.select_related('id_pos').all()
    
    user_list_json = [
        {
            'id_user': user.id_user, 
            'Prizvische': user.prizvische,
            'Name': user.name,
            'Father_Name': user.father_name,
            'Position': user.id_pos.name_pos if user.id_pos else 'Не визначено',
        }
        for user in user_data
    ]
    
    json_data = json.dumps(user_list_json, ensure_ascii=False)

    context = {
        'user_data_json': json_data
    }
    
    return render(request, 'main/data_view.html', context)

# ====================================================================
# ФУНКЦІІ 2, 3: СТОРІНКА ЗВІТІВ (tabl_d.html) / СХЕМА (schem.html)
# ====================================================================

def page_two_view(request):
    """ Реалізує фільтрацію користувачів за додатками та назвою ролі. """
    selected_apps = request.GET.getlist('app_filter') 
    role_query = request.GET.get('role_filter', '').strip() 

    # Використовуємо select_related та prefetch_related для оптимізації SQL-запитів
    # 
    users_queryset = UserList.objects.select_related('id_pos').prefetch_related(
        'userrole_set__id_role__id_group__id_app'
    ).all()

    if selected_apps:
        users_queryset = users_queryset.filter(
            userrole_set__id_role__id_group__id_app__app_name__in=selected_apps
        ).distinct()

    if role_query:
        users_queryset = users_queryset.filter(
            userrole_set__id_role__name__icontains=role_query
        ).distinct()

    report_data = []
    for user in users_queryset:
        pib = f"{user.prizvische} {user.name} {user.father_name}"
        position_name = user.id_pos.name_pos if user.id_pos else 'Не визначено'
        
        roles_for_display = []
        for user_role_entry in user.userrole_set.all():
            role = user_role_entry.id_role
            app = role.id_group.id_app
            
            matches_app = not selected_apps or app.app_name in selected_apps
            matches_role = not role_query or role_query.lower() in role.name.lower()
            
            if matches_app and matches_role:
                roles_for_display.append({
                    'application': app.app_name,
                    'role_name': role.name
                })
        
        if roles_for_display:
            report_data.append({
                'id_user': user.id_user,
                'pib': pib,
                'position': position_name,
                'roles_data': roles_for_display
            })

    return render(request, 'main/tabl_d.html', {'report_data': report_data})


def page_three_view(request):
    """Рендеринг сторінки 'Схема'."""
    return render(request, 'main/schem.html', {})

# ====================================================================
# ФУНКЦІЯ 4: ПРОФІЛЬ ТА ЗАПИТ РОЛІ (you_user.html)
# ====================================================================

def page_four_view(request):
    """ Формує дані для індивідуальних профілів користувачів ХАЕС. """
    
    # Отримуємо всіх користувачів для випадаючого списку
    all_users = UserList.objects.select_related('id_pos').all().values(
        'id_user', 'prizvische', 'name', 'father_name', 'id_pos__name_pos'
    )
    
    # Створюємо словник ролей для кожного користувача для JS
    # 
    user_roles_map = {}
    all_assignments = UserRole.objects.select_related('id_role__id_group__id_app', 'id_user').all()
    
    for assignment in all_assignments:
        u_id = str(assignment.id_user.id_user)
        if u_id not in user_roles_map:
            user_roles_map[u_id] = []
        
        user_roles_map[u_id].append({
            'app': assignment.id_role.id_group.id_app.app_name,
            'role': assignment.id_role.name
        })

    context = {
        'all_users': all_users,
        'user_roles_json': json.dumps(user_roles_map, ensure_ascii=False)
    }
    return render(request, 'main/you_user.html', context)