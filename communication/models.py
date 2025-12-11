"""
Communication Models for Exit Protocol
Secure messaging with BIFF filtering, delivery tracking & toxicity detection
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid


# -----------------------------------------------------------
# MESSAGE
# -----------------------------------------------------------

class Message(models.Model):
    """Secure messages between case parties with AI-mediated filtering"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey('cases.Case', on_delete=models.CASCADE, related_name='messages')

    # Sender + recipient mapping
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sent_messages'
    )
    recipients = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='received_messages',
        through='MessageRecipient'
    )

    # Content
    subject = models.CharField(max_length=255)
    original_body = models.TextField(help_text='Original message before BIFF filtering')
    processed_body = models.TextField(blank=True, help_text='BIFF-filtered message text')

    # AI filtering metadata
    was_filtered = models.BooleanField(default=False)
    ai_filter_applied = models.BooleanField(default=False)
    ai_filter_timestamp = models.DateTimeField(null=True, blank=True)
    ai_filter_notes = models.TextField(blank=True)

    # Toxicity detection
    toxicity_score = models.FloatField(null=True, blank=True)
    flagged_as_hostile = models.BooleanField(default=False)

    # Delivery tracking
    sent_at = models.DateTimeField(auto_now_add=True)
    is_draft = models.BooleanField(default=False)

    # Threading
    reply_to = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies'
    )
    thread_root = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='thread_messages'
    )

    # Priority
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')

    # Attachments
    attachments = models.ManyToManyField('evidence.EvidenceDocument', blank=True, related_name='messages')

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'messages'
        ordering = ['-sent_at']
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
        indexes = [
            models.Index(fields=['case', 'sent_at']),
            models.Index(fields=['sender', 'sent_at']),
            models.Index(fields=['thread_root', 'sent_at']),
        ]

    def __str__(self):
        return f"{self.subject} • {self.sender}"

    def get_body_to_send(self):
        return self.processed_body if self.was_filtered and self.processed_body else self.original_body

    def mark_as_read_by(self, user):
        MessageRecipient.objects.filter(message=self, recipient=user).update(
            read_at=timezone.now(),
            is_read=True
        )


# -----------------------------------------------------------
# MESSAGE RECIPIENT
# -----------------------------------------------------------

class MessageRecipient(models.Model):
    """Through model for recipient tracking (read receipts + delivery time)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='recipient_links')
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='message_links')

    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'message_recipients'
        unique_together = [['message', 'recipient']]
        indexes = [
            models.Index(fields=['recipient', 'message']),  # performant inbox queries
        ]

    def __str__(self):
        return f"{self.recipient} • {'Read' if self.is_read else 'Unread'}"


# -----------------------------------------------------------
# MESSAGE TEMPLATE
# -----------------------------------------------------------

class MessageTemplate(models.Model):
    """Pre-approved BIFF-compliant templates"""
    TEMPLATE_TYPE_CHOICES = [
        ('pickup_dropoff', 'Pickup/Dropoff Schedule'),
        ('expense_request', 'Expense Request'),
        ('schedule_change', 'Schedule Change Request'),
        ('information_request', 'Information Request'),
        ('document_sharing', 'Document Sharing'),
        ('general', 'General Communication'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    template_type = models.CharField(max_length=30, choices=TEMPLATE_TYPE_CHOICES)

    subject_template = models.CharField(max_length=255)
    body_template = models.TextField(help_text='Use {variables} for dynamic content')

    available_variables = models.JSONField(default=list, help_text='List of allowed variables in this template')

    # Usage + metadata
    is_active = models.BooleanField(default=True)
    usage_count = models.IntegerField(default=0)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'message_templates'
        ordering = ['template_type', 'title']
        verbose_name = 'Message Template'
        verbose_name_plural = 'Message Templates'

    def __str__(self):
        return f"{self.get_template_type_display()} • {self.title}"


# -----------------------------------------------------------
# COMMUNICATION LOG
# -----------------------------------------------------------

class CommunicationLog(models.Model):
    """Logs both platform and external communication events"""
    CHANNEL_CHOICES = [
        ('platform', 'Platform Message'),
        ('email', 'Email'),
        ('phone', 'Phone Call'),
        ('text', 'Text Message'),
        ('in_person', 'In Person'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey('cases.Case', on_delete=models.CASCADE, related_name='comm_logs')

    from_party = models.ForeignKey(
        'cases.CaseParty', on_delete=models.CASCADE, related_name='communications_sent'
    )
    to_party = models.ForeignKey(
        'cases.CaseParty', on_delete=models.CASCADE, related_name='communications_received'
    )

    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    timestamp = models.DateTimeField()
    duration_minutes = models.IntegerField(null=True, blank=True)

    subject = models.CharField(max_length=255, blank=True)
    summary = models.TextField()

    TONE_CHOICES = [
        ('professional', 'Professional'),
        ('neutral', 'Neutral'),
        ('tense', 'Tense'),
        ('hostile', 'Hostile'),
        ('cooperative', 'Cooperative'),
    ]
    assessed_tone = models.CharField(max_length=20, choices=TONE_CHOICES, blank=True)

    related_message = models.ForeignKey(Message, on_delete=models.SET_NULL, null=True, blank=True)

    logged_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    logged_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'communication_logs'
        ordering = ['-timestamp']
        verbose_name = 'Communication Log'
        verbose_name_plural = 'Communication Logs'
        indexes = [
            models.Index(fields=['case', 'timestamp']),
            models.Index(fields=['from_party', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.from_party.user} → {self.to_party.user} via {self.channel}"


# -----------------------------------------------------------
# BIFF ANALYSIS
# -----------------------------------------------------------

class BIFFAnalysis(models.Model):
    """Stores AI BIFF scoring + feedback"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.OneToOneField(Message, on_delete=models.CASCADE, related_name='biff_analysis')

    brief_score = models.IntegerField()
    informative_score = models.IntegerField()
    friendly_score = models.IntegerField()
    firm_score = models.IntegerField()

    overall_score = models.FloatField()
    is_compliant = models.BooleanField()

    issues_found = models.JSONField(default=list)
    improvement_suggestions = models.TextField(blank=True)

    analyzed_at = models.DateTimeField(auto_now_add=True)
    ai_model_version = models.CharField(max_length=50, blank=True)

    class Meta:
        db_table = 'biff_analyses'
        verbose_name = 'BIFF Analysis'
        verbose_name_plural = 'BIFF Analyses'

    def __str__(self):
        return f"{self.message.subject} — BIFF Score {self.overall_score}"
