from django.contrib import admin

# Register your models here.
from .models import EvidenceDocument, EvidenceVersion, EvidenceAccessLog, EvidenceCollection



admin.site.register(EvidenceDocument)
admin.site.register(EvidenceVersion)
admin.site.register(EvidenceAccessLog)
admin.site.register(EvidenceCollection)