from django.urls import path
from . import views

app_name = 'cases'

urlpatterns = [
    # Core Case Management
    path('', views.case_list, name='case_list'),
    path('select/', views.select_case, name='select_case'),
    path('create/', views.case_create, name='case_create'),
    path('<uuid:case_id>/', views.case_detail, name='case_detail'),
    path('<uuid:case_id>/edit/', views.case_update, name='case_update'),

    # Sub-features
    path('<uuid:case_id>/notes/add/', views.note_create, name='note_create'),
    path('<uuid:case_id>/timeline/', views.timeline_list, name='timeline_list'),
    path('<uuid:case_id>/timeline/add/', views.timeline_create, name='timeline_create'),
]