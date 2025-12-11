"""
Audit and Logging Models for Exit Protocol
Comprehensive audit trail for legal compliance
"""
from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
import uuid
import json


class AuditLog(models.Model):
    """
    Universal audit log for all system actions
    Immutable once created
    """
    ACTION_CHOICES = [
        ('create', 'Created'),
        ('read', 'Viewed'),
        ('update', 'Updated'),
        ('delete', 'Deleted'),
        ('login', 'Logged In'),
        ('logout', 'Logged Out'),
        ('export', 'Exported Data'),
        ('import', 'Imported Data'),
        ('permission_change', 'Permission Changed'),
        ('share', 'Shared'),
        ('calculate', 'Calculation Performed'),
        ('other', 'Other Action'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # User and timestamp
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    # Action details
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    description = models.TextField()
    
    # Affected object (using generic foreign key)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    object_id = models.UUIDField(null=True, blank=True)
    affected_object = GenericForeignKey('content_type', 'object_id')
    
    # Case context (for filtering)
    case = models.ForeignKey(
        'cases.Case',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    
    # Changes (before/after for updates)
    changes = models.JSONField(
        default=dict,
        blank=True,
        help_text='Dictionary of field changes'
    )
    
    # Request context
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, blank=True)
    request_method = models.CharField(max_length=10, blank=True)
    request_path = models.CharField(max_length=512, blank=True)
    
    # Severity level
    SEVERITY_CHOICES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('critical', 'Critical'),
    ]
    severity = models.CharField(
        max_length=10,
        choices=SEVERITY_CHOICES,
        default='info'
    )
    
    class Meta:
        db_table = 'audit_logs'
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['case', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
            models.Index(fields=['content_type', 'object_id']),
        ]
    
    def __str__(self):
        user_str = self.user.email if self.user else 'Anonymous'
        return f"{user_str} - {self.action} - {self.timestamp}"
    
    def save(self, *args, **kwargs):
        """Prevent updates to audit logs"""
        # FIX: Check if this is a new record being added to the DB
        # We cannot check 'if self.pk' because UUIDs are generated before saving
        if not self._state.adding:
            raise ValueError("Audit logs are immutable and cannot be updated")
        super().save(*args, **kwargs)


class DataExport(models.Model):
    """
    Track data exports for compliance
    GDPR and e-discovery requirements
    """
    EXPORT_TYPE_CHOICES = [
        ('case_summary', 'Case Summary'),
        ('financial_report', 'Financial Report'),
        ('evidence_package', 'Evidence Package'),
        ('communications', 'Communications Export'),
        ('full_backup', 'Full Case Backup'),
        ('gdpr_request', 'GDPR Data Export'),
    ]
    
    FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('csv', 'CSV'),
        ('xlsx', 'Excel'),
        ('json', 'JSON'),
        ('zip', 'ZIP Archive'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(
        'cases.Case',
        on_delete=models.CASCADE,
        related_name='exports'
    )
    
    # Export details
    export_type = models.CharField(max_length=30, choices=EXPORT_TYPE_CHOICES)
    export_format = models.CharField(max_length=10, choices=FORMAT_CHOICES)
    
    # File information
    file_path = models.CharField(max_length=512)
    file_size_bytes = models.BigIntegerField(null=True)
    file_hash = models.CharField(max_length=64, blank=True)
    
    # Metadata
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='data_exports'
    )
    requested_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Export parameters
    date_range_start = models.DateField(null=True, blank=True)
    date_range_end = models.DateField(null=True, blank=True)
    filters_applied = models.JSONField(default=dict, blank=True)
    
    # Access tracking
    download_count = models.IntegerField(default=0)
    last_downloaded_at = models.DateTimeField(null=True, blank=True)
    
    # Retention
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Export file will be deleted after this date'
    )
    
    class Meta:
        db_table = 'data_exports'
        verbose_name = 'Data Export'
        verbose_name_plural = 'Data Exports'
        ordering = ['-requested_at']
        indexes = [
            models.Index(fields=['case', '-requested_at']),
            models.Index(fields=['requested_by', '-requested_at']),
        ]
    
    def __str__(self):
        return f"{self.get_export_type_display()} - {self.requested_at}"


class SystemAlert(models.Model):
    """
    System-generated alerts for important events
    E.g., suspicious login, deadline approaching, etc.
    """
    ALERT_TYPE_CHOICES = [
        ('security', 'Security Alert'),
        ('deadline', 'Deadline Reminder'),
        ('calculation_error', 'Calculation Error'),
        ('document_issue', 'Document Issue'),
        ('communication', 'Communication Alert'),
        ('system', 'System Notification'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    alert_type = models.CharField(max_length=30, choices=ALERT_TYPE_CHOICES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES)
    
    # Alert details
    title = models.CharField(max_length=255)
    message = models.TextField()
    
    # Context
    case = models.ForeignKey(
        'cases.Case',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='alerts'
    )
    affected_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='alerts'
    )
    
    # Status
    is_read = models.BooleanField(default=False)
    is_resolved = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_alerts'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Alert will be auto-dismissed after this time'
    )
    
    class Meta:
        db_table = 'system_alerts'
        verbose_name = 'System Alert'
        verbose_name_plural = 'System Alerts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['affected_user', '-created_at']),
            models.Index(fields=['case', 'priority', '-created_at']),
            models.Index(fields=['is_read', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_priority_display()} - {self.title}"


class ComplianceReport(models.Model):
    """
    Periodic compliance reports
    For attorney review and court submission
    """
    REPORT_TYPE_CHOICES = [
        ('monthly', 'Monthly Activity Report'),
        ('discovery', 'Discovery Compliance Report'),
        ('financial', 'Financial Analysis Report'),
        ('communication', 'Communication Summary'),
        ('court_ordered', 'Court-Ordered Report'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(
        'cases.Case',
        on_delete=models.CASCADE,
        related_name='compliance_reports'
    )
    
    report_type = models.CharField(max_length=30, choices=REPORT_TYPE_CHOICES)
    report_period_start = models.DateField()
    report_period_end = models.DateField()
    
    # Report content
    summary = models.TextField()
    findings = models.JSONField(
        default=dict,
        help_text='Structured findings and metrics'
    )
    
    # File
    report_file = models.FileField(upload_to='reports/', null=True, blank=True)
    
    # Metadata
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    generated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'compliance_reports'
        verbose_name = 'Compliance Report'
        verbose_name_plural = 'Compliance Reports'
        ordering = ['-generated_at']
        indexes = [
            models.Index(fields=['case', '-generated_at']),
        ]
    
    def __str__(self):
        return f"{self.get_report_type_display()} - {self.report_period_start}"