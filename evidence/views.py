"""
Evidence Management Views
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, FileResponse
from django.db import IntegrityError  # <--- Added Import
from evidence.models import EvidenceDocument, EvidenceCollection, EvidenceAccessLog
from evidence.forms import EvidenceUploadForm, EvidenceCollectionForm
from cases.models import CaseParty
from audit.models import AuditLog


@login_required
def evidence_list(request):
    """List all evidence documents for current case"""
    case = request.case
    if not case:
        messages.error(request, 'No active case selected.')
        return redirect('cases:select_case')
    
    # Filter by document type if specified
    document_type = request.GET.get('type', '')
    
    documents = EvidenceDocument.objects.filter(case=case)
    
    if document_type:
        documents = documents.filter(document_type=document_type)
    
    documents = documents.order_by('-upload_timestamp')
    
    # Get unique document types for filter
    document_types = EvidenceDocument.DOCUMENT_TYPE_CHOICES
    
    context = {
        'case': case,
        'documents': documents,
        'document_types': document_types,
        'selected_type': document_type,
    }
    
    return render(request, 'evidence/evidence_list.html', context)


@login_required
def evidence_upload(request):
    """Upload new evidence document"""
    case = request.case
    if not case:
        messages.error(request, 'No active case selected.')
        return redirect('cases:select_case')
    
    if request.method == 'POST':
        form = EvidenceUploadForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.case = case
            document.uploaded_by = request.user
            document.upload_ip_address = get_client_ip(request)
            
            try:
                # File info will be auto-calculated in model save()
                # This triggers the hash check. If duplicate, it raises IntegrityError.
                document.save()
                
                # Queue OCR processing
                from finance.tasks import process_evidence_ocr
                process_evidence_ocr.delay(str(document.id))
                
                # Log the upload
                AuditLog.objects.create(
                    user=request.user,
                    action='create',
                    description=f'Uploaded evidence: {document.title}',
                    case=case,
                    ip_address=get_client_ip(request)
                )
                
                messages.success(request, 'Evidence uploaded successfully! OCR processing started.')
                return redirect('evidence:evidence_detail', document_id=document.id)

            except IntegrityError:
                # Catch the duplicate error and redirect safely
                messages.warning(request, f'Duplicate detected! The file "{document.title}" has already been uploaded.')
                return redirect('evidence:evidence_list')

    else:
        form = EvidenceUploadForm()
    
    return render(request, 'evidence/evidence_upload.html', {
        'form': form,
        'case': case
    })


@login_required
def evidence_detail(request, document_id):
    """View evidence document details"""
    case = request.case
    document = get_object_or_404(EvidenceDocument, id=document_id, case=case)
    
    # Log access
    EvidenceAccessLog.objects.create(
        document=document,
        user=request.user,
        action='view',
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:512]
    )
    
    # Get access history
    access_logs = document.access_logs.all().order_by('-timestamp')[:20]
    
    # Get collections this document belongs to
    collections = document.collections.all()
    
    context = {
        'case': case,
        'document': document,
        'access_logs': access_logs,
        'collections': collections,
    }
    
    return render(request, 'evidence/evidence_detail.html', context)


@login_required
def evidence_download(request, document_id):
    """Download evidence document"""
    case = request.case
    document = get_object_or_404(EvidenceDocument, id=document_id, case=case)
    
    # Log download
    EvidenceAccessLog.objects.create(
        document=document,
        user=request.user,
        action='download',
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:512]
    )
    
    AuditLog.objects.create(
        user=request.user,
        action='read',
        description=f'Downloaded evidence: {document.title}',
        case=case,
        ip_address=get_client_ip(request)
    )
    
    # Serve file
    response = FileResponse(document.document.open('rb'))
    response['Content-Type'] = document.mime_type
    response['Content-Disposition'] = f'attachment; filename="{document.original_filename}"'
    
    return response


@login_required
def collection_list(request):
    """List evidence collections"""
    case = request.case
    if not case:
        messages.error(request, 'No active case selected.')
        return redirect('cases:select_case')
    
    collections = EvidenceCollection.objects.filter(case=case).order_by('name')
    
    return render(request, 'evidence/collection_list.html', {
        'case': case,
        'collections': collections
    })


@login_required
def collection_create(request):
    """Create new evidence collection"""
    case = request.case
    if not case:
        messages.error(request, 'No active case selected.')
        return redirect('cases:select_case')
    
    if request.method == 'POST':
        form = EvidenceCollectionForm(request.POST)
        if form.is_valid():
            collection = form.save(commit=False)
            collection.case = case
            collection.created_by = request.user
            collection.save()
            
            # Add selected documents to collection
            if form.cleaned_data.get('documents'):
                collection.documents.set(form.cleaned_data['documents'])
            
            messages.success(request, 'Collection created successfully!')
            return redirect('evidence:collection_list')
    else:
        form = EvidenceCollectionForm()
        # Filter documents to current case
        form.fields['documents'].queryset = EvidenceDocument.objects.filter(case=case)
    
    return render(request, 'evidence/collection_form.html', {
        'form': form,
        'case': case
    })


def get_client_ip(request):
    """Extract client IP from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip