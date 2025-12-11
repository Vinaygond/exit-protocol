"""
Evidence Management Models for Exit Protocol
Implements chain of custody and immutable document storage
"""
from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.utils import timezone
import hashlib
import uuid
import os


def evidence_upload_path(instance, filename):
    """
    Generate secure upload path using content hash
    Format: evidence/{case_id}/{year}/{month}/{hash}/{filename}
    """
    now = timezone.now()
    # Use first 2 chars of hash for directory sharding
    hash_prefix = instance.file_hash_sha256[:2] if instance.file_hash_sha256 else 'temp'
    return f'evidence/{instance.case.id}/{now.year}/{now.month:02d}/{hash_prefix}/{filename}'


class EvidenceDocument(models.Model):
    """
    Core evidence document with cryptographic integrity
    All uploads are immutable once saved
    """
    DOCUMENT_TYPE_CHOICES = [
        ('bank_statement', 'Bank Statement'),
        ('tax_return', 'Tax Return'),
        ('pay_stub', 'Pay Stub'),
        ('property_deed', 'Property Deed'),
        ('appraisal', 'Appraisal'),
        ('invoice', 'Invoice/Receipt'),
        ('contract', 'Contract'),
        ('correspondence', 'Correspondence'),
        ('court_filing', 'Court Filing'),
        ('photo', 'Photograph'),
        ('other', 'Other Document'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey('cases.Case', on_delete=models.CASCADE, related_name='evidence')
    
    # File information
    document = models.FileField(
        upload_to=evidence_upload_path,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx', 'xls', 'xlsx', 'csv']
            )
        ]
    )
    original_filename = models.CharField(max_length=255)
    file_size_bytes = models.BigIntegerField()
    mime_type = models.CharField(max_length=127)
    
    # Cryptographic integrity
    file_hash_sha256 = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text='SHA-256 hash for integrity verification'
    )
    file_hash_md5 = models.CharField(
        max_length=32,
        blank=True,
        help_text='MD5 hash for compatibility with legacy systems'
    )
    
    # Document classification
    document_type = models.CharField(
        max_length=30,
        choices=DOCUMENT_TYPE_CHOICES,
        default='other'
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Date information
    document_date = models.DateField(
        null=True,
        blank=True,
        help_text='Date the document was created/dated'
    )
    
    # OCR and text extraction
    extracted_text = models.TextField(
        blank=True,
        help_text='Text extracted via OCR'
    )
    ocr_completed_at = models.DateTimeField(null=True, blank=True)
    ocr_confidence = models.FloatField(
        null=True,
        blank=True,
        help_text='OCR confidence score 0-1'
    )
    
    # Chain of custody
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_evidence'
    )
    upload_timestamp = models.DateTimeField(auto_now_add=True)
    upload_ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    # Blockchain timestamping (future feature)
    blockchain_timestamp = models.JSONField(
        null=True,
        blank=True,
        help_text='OpenTimestamps or similar proof'
    )
    
    # Access control
    is_privileged = models.BooleanField(
        default=False,
        help_text='Attorney work product or privileged communication'
    )
    is_redacted = models.BooleanField(
        default=False,
        help_text='Contains redacted information'
    )
    
    # Tags for organization
    tags = models.JSONField(
        default=list,
        blank=True,
        help_text='Searchable tags for document organization'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'evidence_documents'
        verbose_name = 'Evidence Document'
        verbose_name_plural = 'Evidence Documents'
        ordering = ['-upload_timestamp']
        indexes = [
            models.Index(fields=['case', '-upload_timestamp']),
            models.Index(fields=['document_type', '-document_date']),
            models.Index(fields=['file_hash_sha256']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.original_filename}"
    
    def save(self, *args, **kwargs):
        """Calculate hashes before saving if not already set"""
        if not self.file_hash_sha256 and self.document:
            self.file_hash_sha256, self.file_hash_md5 = self._calculate_hashes()
        
        if not self.original_filename and self.document:
            self.original_filename = os.path.basename(self.document.name)
        
        if not self.file_size_bytes and self.document:
            self.file_size_bytes = self.document.size
        
        super().save(*args, **kwargs)
    
    def _calculate_hashes(self):
        """Calculate SHA-256 and MD5 hashes of file"""
        sha256_hasher = hashlib.sha256()
        md5_hasher = hashlib.md5()
        
        # Reset file pointer
        self.document.seek(0)
        
        # Read in chunks to handle large files
        for chunk in self.document.chunks(chunk_size=8192):
            sha256_hasher.update(chunk)
            md5_hasher.update(chunk)
        
        # Reset file pointer again
        self.document.seek(0)
        
        return sha256_hasher.hexdigest(), md5_hasher.hexdigest()
    
    def verify_integrity(self):
        """Verify file integrity against stored hash"""
        if not self.document:
            return False
        
        current_hash, _ = self._calculate_hashes()
        return current_hash == self.file_hash_sha256


class EvidenceVersion(models.Model):
    """
    Track versions of evidence documents
    If a document is modified, preserve the original
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    original_document = models.ForeignKey(
        EvidenceDocument,
        on_delete=models.CASCADE,
        related_name='versions'
    )
    
    # Version information
    version_number = models.IntegerField()
    version_file = models.FileField(upload_to='evidence/versions/')
    version_hash_sha256 = models.CharField(max_length=64)
    
    # Change tracking
    change_description = models.TextField()
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    changed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'evidence_versions'
        verbose_name = 'Evidence Version'
        verbose_name_plural = 'Evidence Versions'
        ordering = ['-version_number']
        unique_together = [['original_document', 'version_number']]
    
    def __str__(self):
        return f"{self.original_document.title} - Version {self.version_number}"


class EvidenceAccessLog(models.Model):
    """
    Audit log for evidence access
    Track who viewed, downloaded, or modified documents
    """
    ACTION_CHOICES = [
        ('view', 'Viewed'),
        ('download', 'Downloaded'),
        ('modify', 'Modified'),
        ('delete', 'Deleted'),
        ('share', 'Shared'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(
        EvidenceDocument,
        on_delete=models.CASCADE,
        related_name='access_logs'
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Context
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, blank=True)
    
    class Meta:
        db_table = 'evidence_access_logs'
        verbose_name = 'Evidence Access Log'
        verbose_name_plural = 'Evidence Access Logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['document', '-timestamp']),
            models.Index(fields=['user', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user} - {self.action} - {self.document.title}"


class EvidenceCollection(models.Model):
    """
    Organize evidence documents into collections
    E.g., "2023 Tax Documents", "Property Appraisals"
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey('cases.Case', on_delete=models.CASCADE, related_name='evidence_collections')
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    documents = models.ManyToManyField(
        EvidenceDocument,
        related_name='collections',
        blank=True
    )
    
    # Exhibit numbering for court
    exhibit_prefix = models.CharField(
        max_length=10,
        blank=True,
        help_text='E.g., "PX" for Petitioner Exhibit'
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
        db_table = 'evidence_collections'
        verbose_name = 'Evidence Collection'
        verbose_name_plural = 'Evidence Collections'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.documents.count()} documents)"