from django.urls import path
from . import views

app_name = 'evidence'

urlpatterns = [
    # Document Management
    path('', views.evidence_list, name='evidence_list'),
    path('upload/', views.evidence_upload, name='evidence_upload'),
    path('document/<uuid:document_id>/', views.evidence_detail, name='evidence_detail'),
    path('document/<uuid:document_id>/download/', views.evidence_download, name='evidence_download'),
    
    # Collections
    path('collections/', views.collection_list, name='collection_list'),
    path('collections/create/', views.collection_create, name='collection_create'),
]