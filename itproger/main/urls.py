# main/urls.py
from django.urls import path
from . import views 

urlpatterns = [
    # 🚀 ВИПРАВЛЕННЯ 1: Додаємо порожній шлях, який веде на role_assignment_view
    path('', views.role_assignment_view, name='home'), 
    
    # Залишаємо assignment/ для внутрішньої логіки та навігації
    path('assignment/', views.role_assignment_view, name='role_assignment'),
    
    # ... інші маршрути ...
    path('reports/', views.page_two_view, name='page_two'),
    path('profil/', views.page_three_view, name='page_three'),
    path('settings/', views.page_four_view, name='page_four'),
]