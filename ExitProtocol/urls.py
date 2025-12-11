from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # App URLs
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('cases/', include('cases.urls', namespace='cases')),
    path('finance/', include('finance.urls', namespace='finance')),
    path('evidence/', include('evidence.urls', namespace='evidence')),
    path('communication/', include('communication.urls', namespace='communication')),
    path('subscription/', include('subscriptions.urls')),
    
    # Core (Dashboard)
    path('', include('core.urls', namespace='core')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)