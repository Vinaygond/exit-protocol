from django.urls import path
from . import views

app_name = 'communication'

urlpatterns = [
    # Messaging
    path('', views.message_list, name='message_list'),
    path('compose/', views.message_compose, name='message_compose'),
    path('message/<uuid:message_id>/', views.message_detail, name='message_detail'),
    path('message/<uuid:message_id>/reply/', views.message_reply, name='message_reply'),
    
    # Tools
    path('biff-generator/', views.biff_generator, name='biff_generator'),
]