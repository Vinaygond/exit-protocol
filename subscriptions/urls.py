from django.urls import path
from . import views

app_name = 'subscriptions'

urlpatterns = [
    path('pricing/', views.pricing_page, name='pricing'),
    path('upgrade/mock/', views.upgrade_success, name='mock_upgrade'), # Temp link for demo
]