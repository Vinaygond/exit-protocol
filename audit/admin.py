from django.contrib import admin

# Register your models here.
from .models import AuditLog, DataExport, SystemAlert, ComplianceReport



admin.site.register(AuditLog)
admin.site.register(DataExport)
admin.site.register(SystemAlert)
admin.site.register(ComplianceReport)