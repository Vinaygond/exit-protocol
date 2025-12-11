from django.contrib import admin

# Register your models here.
from .models import Case, CaseParty, CaseNote, CaseTimeline



admin.site.register(Case)
admin.site.register(CaseParty)
admin.site.register(CaseNote)
admin.site.register(CaseTimeline)