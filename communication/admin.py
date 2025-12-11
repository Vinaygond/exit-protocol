from django.contrib import admin

# Register your models here.
from .models import Message, MessageRecipient, MessageTemplate, CommunicationLog, BIFFAnalysis



admin.site.register(Message)
admin.site.register(MessageRecipient)
admin.site.register(MessageTemplate)
admin.site.register(CommunicationLog)
admin.site.register(BIFFAnalysis)