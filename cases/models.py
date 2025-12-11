"""
Case Models for Exit Protocol
Implements the core multi-tenancy structure
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid


class Case(models.Model):
    """
    Core Case model - acts as the tenant boundary
    All data is isolated by Case
    """
    STATUS_CHOICES = [
        ('initiated', 'Initiated'),
        ('discovery', 'Discovery'),
        ('negotiation', 'Negotiation'),
        ('litigation', 'Litigation'),
        ('settlement', 'Settlement'),
        ('closed', 'Closed'),
        ('archived', 'Archived'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Case identification
    case_number = models.CharField(
        max_length=50, 
        unique=True,
        db_index=True,
        help_text='Court case number or internal reference'
    )
    case_title = models.CharField(
        max_length=255,
        help_text='e.g., "Smith v. Smith"'
    )
    
    # Court information
    court_name = models.CharField(max_length=255, blank=True)
    court_jurisdiction = models.CharField(max_length=100, blank=True)
    judge_name = models.CharField(max_length=255, blank=True)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='initiated'
    )
    
    # Key dates
    filing_date = models.DateField(null=True, blank=True)
    separation_date = models.DateField(
        null=True, 
        blank=True,
        help_text='Date of separation - critical for financial tracing'
    )
    marriage_date = models.DateField(null=True, blank=True)
    expected_resolution_date = models.DateField(null=True, blank=True)
    closed_date = models.DateField(null=True, blank=True)
    
    # Financial context
    estimated_marital_assets = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )
    estimated_separate_assets = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='cases_created'
    )
    
    # Soft delete
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'cases'
        verbose_name = 'Case'
        verbose_name_plural = 'Cases'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['case_number']),
            models.Index(fields=['status', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.case_number} - {self.case_title}"
    
    def get_primary_party(self):
        """Get the primary party (petitioner)"""
        return self.parties.filter(role='petitioner').first()
    
    def get_opposing_party(self):
        """Get the opposing party (respondent)"""
        return self.parties.filter(role='respondent').first()
    
    def is_in_discovery(self):
        """Check if case is in discovery phase"""
        return self.status == 'discovery'


class CaseParty(models.Model):
    """
    Represents a party to the divorce case
    Links users to cases with specific roles
    """
    ROLE_CHOICES = [
        ('petitioner', 'Petitioner'),
        ('respondent', 'Respondent'),
        ('attorney_petitioner', 'Attorney for Petitioner'),
        ('attorney_respondent', 'Attorney for Respondent'),
        ('mediator', 'Mediator'),
        ('financial_expert', 'Financial Expert'),
        ('observer', 'Observer'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='parties')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='case_participations'
    )
    
    role = models.CharField(max_length=30, choices=ROLE_CHOICES)
    
    # Permissions
    can_view_financials = models.BooleanField(default=True)
    can_edit_financials = models.BooleanField(default=False)
    can_view_communications = models.BooleanField(default=True)
    can_send_communications = models.BooleanField(default=True)
    can_view_evidence = models.BooleanField(default=True)
    can_upload_evidence = models.BooleanField(default=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(default=timezone.now)
    left_at = models.DateTimeField(null=True, blank=True)
    
    # Notes
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'case_parties'
        verbose_name = 'Case Party'
        verbose_name_plural = 'Case Parties'
        unique_together = [['case', 'user']]
        indexes = [
            models.Index(fields=['case', 'role']),
            models.Index(fields=['user', '-joined_at']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_role_display()} in {self.case}"
    
    def is_attorney(self):
        return self.role in ['attorney_petitioner', 'attorney_respondent']
    
    def is_principal_party(self):
        return self.role in ['petitioner', 'respondent']


class CaseNote(models.Model):
    """
    Case notes and journal entries
    Used for tracking important events and observations
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='notes')
    
    title = models.CharField(max_length=255)
    content = models.TextField()
    
    # Categorization
    CATEGORY_CHOICES = [
        ('general', 'General Note'),
        ('financial', 'Financial Observation'),
        ('legal', 'Legal Strategy'),
        ('communication', 'Communication Log'),
        ('evidence', 'Evidence Note'),
        ('deadline', 'Deadline/Reminder'),
    ]
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    
    # Visibility
    is_private = models.BooleanField(
        default=False,
        help_text='Private notes only visible to creator'
    )
    
    # Metadata
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='case_notes'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'case_notes'
        verbose_name = 'Case Note'
        verbose_name_plural = 'Case Notes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['case', '-created_at']),
            models.Index(fields=['category', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.case}"


class CaseTimeline(models.Model):
    """
    Timeline events for case chronology
    Important for establishing facts and sequences
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='timeline_events')
    
    event_date = models.DateField()
    event_title = models.CharField(max_length=255)
    event_description = models.TextField(blank=True)
    
    # Event types
    EVENT_TYPE_CHOICES = [
        ('marriage', 'Marriage'),
        ('separation', 'Separation'),
        ('filing', 'Court Filing'),
        ('financial', 'Financial Event'),
        ('custody', 'Custody Event'),
        ('property', 'Property Event'),
        ('communication', 'Communication'),
        ('legal', 'Legal Proceeding'),
        ('other', 'Other'),
    ]
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES)
    
    # Link to evidence
    related_evidence = models.ManyToManyField(
        'evidence.EvidenceDocument',
        blank=True,
        related_name='timeline_events'
    )
    
    # Importance
    is_key_event = models.BooleanField(
        default=False,
        help_text='Mark as key event for case summary'
    )
    
    # Metadata
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'case_timeline'
        verbose_name = 'Timeline Event'
        verbose_name_plural = 'Timeline Events'
        ordering = ['-event_date', '-created_at']
        indexes = [
            models.Index(fields=['case', '-event_date']),
            models.Index(fields=['event_type', '-event_date']),
        ]
    
    def __str__(self):
        return f"{self.event_date} - {self.event_title}"