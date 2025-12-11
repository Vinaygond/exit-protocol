"""
URL Configuration for Core App
"""
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('switch-case/<uuid:case_id>/', views.switch_case, name='switch_case'),
    path('health/', views.health_check, name='health_check'),
    path('legal-directory/', views.legal_directory, name='legal_directory'),
]