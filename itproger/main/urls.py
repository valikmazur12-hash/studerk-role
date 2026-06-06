from django.urls import path
from . import views

urlpatterns = [
    # Головна сторінка: призначена і для імені 'index', і для імені 'role_assignment'
    path('', views.role_assignment_view, name='index'),
    path('role-assignment/', views.role_assignment_view, name='role_assignment'),
    path('confirm-role/<str:token>/', views.confirm_role_view, name='confirm_role'),
    
    # Сторінка 2 (Таблиці / Звіти): підтримує обидва імені для зворотної сумісності
    path('tables/', views.page_two_view, name='tables'),
    path('page-two/', views.page_two_view, name='page_two'),
    
    # Сторінка 3 (Ієрархічна схема додатків)
    path('schema/', views.page_three_view, name='schema'),
    path('page-three/', views.page_three_view, name='page_three'),
    
    # Сторінка 4 (Експрес-аудит профілю користувача)
    path('profile/', views.page_four_view, name='profile'),
    path('page-four/', views.page_four_view, name='page_four'),
    
    # Уніфіковані шляхи автентифікації СІТ
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
]