from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    # Account management
    path('accounts/', views.account_list, name='account_list'),
    path('accounts/create/', views.account_create, name='account_create'),
    path('accounts/<uuid:account_id>/', views.account_detail, name='account_detail'),
    
    # Transactions
    path('accounts/<uuid:account_id>/transaction/create/', views.transaction_create, name='transaction_create'),
    path('accounts/<uuid:account_id>/import/', views.transaction_import, name='transaction_import'),
    path('process-statement/<uuid:document_id>/', views.process_statement, name='process_statement'),
    
    # Separate property claims
    path('accounts/<uuid:account_id>/claim/create/', views.claim_create, name='claim_create'),
    path('claims/<uuid:claim_id>/', views.claim_detail, name='claim_detail'),
    path('claims/<uuid:claim_id>/recalculate/', views.claim_recalculate, name='claim_recalculate'),
    
    # NEW: PDF Export
    path('claims/<uuid:claim_id>/export/', views.export_claim_pdf, name='claim_export_pdf'),
    
    # Summary and analytics
    path('summary/', views.financial_summary, name='financial_summary'),
    path('api/balance-chart/<uuid:account_id>/', views.balance_chart_data, name='balance_chart_data'),
]