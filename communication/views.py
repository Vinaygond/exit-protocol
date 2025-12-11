"""
Communication and Messaging Views
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from communication.models import Message, MessageRecipient
from communication.forms import MessageComposeForm, BIFFGeneratorForm
from cases.models import CaseParty
from audit.models import AuditLog
from .ai_engine import BIFFEngine  # <--- NEW IMPORT

@login_required
def message_list(request):
    """List all messages for current user in active case"""
    case = request.case
    if not case:
        messages.error(request, 'No active case selected.')
        return redirect('cases:select_case')
    
    # Get messages where user is recipient
    received_messages = Message.objects.filter(
        case=case,
        recipients=request.user,
        is_draft=False
    ).order_by('-sent_at')
    
    # Get messages sent by user
    sent_messages = Message.objects.filter(
        case=case,
        sender=request.user,
        is_draft=False
    ).order_by('-sent_at')
    
    # Get drafts
    drafts = Message.objects.filter(
        case=case,
        sender=request.user,
        is_draft=True
    ).order_by('-created_at')
    
    # Tab selection
    tab = request.GET.get('tab', 'inbox')
    
    context = {
        'case': case,
        'received_messages': received_messages,
        'sent_messages': sent_messages,
        'drafts': drafts,
        'active_tab': tab,
    }
    return render(request, 'communication/message_list.html', context)

@login_required
def message_compose(request):
    """Compose and send new message"""
    case = request.case
    if not case:
        messages.error(request, 'No active case selected.')
        return redirect('cases:select_case')
    
    # Check if there are any recipients available
    available_recipients = CaseParty.objects.filter(
        case=case, is_active=True
    ).exclude(user=request.user).exists()

    if not available_recipients:
        messages.warning(request, "No other parties (attorneys/spouses) have joined this case yet.")
    
    if request.method == 'POST':
        form = MessageComposeForm(request.POST, case=case, user=request.user)
        if form.is_valid():
            message = form.save(commit=False)
            message.case = case
            message.sender = request.user
            
            if 'save_draft' in request.POST:
                message.is_draft = True
                message.save()
                messages.success(request, 'Message saved as draft.')
                return redirect('communication:message_list')
            else:
                # Process with BIFF filter if enabled
                if form.cleaned_data.get('apply_biff_filter'):
                    message.ai_filter_applied = True
                    # In a real app, you'd run the engine here too
                    message.processed_body = message.original_body 
                
                message.is_draft = False
                message.save()
                
                # Add recipients
                recipients = form.cleaned_data.get('recipients')
                for recipient_party in recipients:
                    MessageRecipient.objects.create(
                        message=message,
                        recipient=recipient_party.user
                    )
                
                # Log the message
                AuditLog.objects.create(
                    user=request.user,
                    action='create',
                    description=f'Sent message: {message.subject}',
                    case=case
                )
                
                messages.success(request, 'Message sent successfully!')
                return redirect('communication:message_list')
    else:
        form = MessageComposeForm(case=case, user=request.user)
    
    return render(request, 'communication/message_compose.html', {'form': form, 'case': case})

@login_required
def message_detail(request, message_id):
    """View message details"""
    case = request.case
    message = get_object_or_404(Message, id=message_id, case=case)
    
    # Check access
    if message.sender != request.user and request.user not in message.recipients.all():
        messages.error(request, 'You do not have access to this message.')
        return redirect('communication:message_list')
    
    # Mark as read
    if request.user in message.recipients.all():
        message.mark_as_read_by(request.user)
    
    # Get thread
    thread_messages = []
    if message.reply_to or message.thread_root:
        root = message.thread_root or message.reply_to
        if not root and message.thread_root:
             root = message.thread_root

        if root:
            thread_messages = Message.objects.filter(
                Q(id=root.id) | Q(thread_root=root)
            ).filter(case=case).order_by('sent_at')

    return render(request, 'communication/message_detail.html', {
        'case': case,
        'message': message,
        'thread_messages': thread_messages,
    })

@login_required
def message_reply(request, message_id):
    """Reply to a message"""
    case = request.case
    original_message = get_object_or_404(Message, id=message_id, case=case)
    
    if request.user not in original_message.recipients.all() and request.user != original_message.sender:
         messages.error(request, 'You cannot reply to this message.')
         return redirect('communication:message_list')

    if request.method == 'POST':
        form = MessageComposeForm(request.POST, case=case, user=request.user)
        if form.is_valid():
            message = form.save(commit=False)
            message.case = case
            message.sender = request.user
            message.reply_to = original_message
            message.thread_root = original_message.thread_root or original_message
            message.save()
            
            target_user = original_message.sender if request.user != original_message.sender else original_message.recipients.first()
            
            if target_user:
                MessageRecipient.objects.create(message=message, recipient=target_user)

            messages.success(request, 'Reply sent successfully!')
            return redirect('communication:message_detail', message_id=message.id)
    else:
        initial_subject = original_message.subject
        if not initial_subject.startswith('Re:'):
            initial_subject = f"Re: {initial_subject}"
            
        form = MessageComposeForm(
            case=case, 
            user=request.user,
            initial={'subject': initial_subject}
        )
    
    return render(request, 'communication/message_compose.html', {
        'form': form, 
        'case': case, 
        'reply_to': original_message
    })

@login_required
def biff_generator(request):
    """
    Script Generator Tool (AI Powered).
    Takes hostile text and returns a BIFF-compliant draft.
    """
    result = None
    
    if request.method == 'POST':
        form = BIFFGeneratorForm(request.POST)
        if form.is_valid():
            hostile_text = form.cleaned_data['received_text']
            context = form.cleaned_data.get('context')
            
            # Use the AI Engine
            engine = BIFFEngine()
            
            # Currently uses mock_rewrite() inside the engine.
            # To go live, uncomment the OpenAI code in ai_engine.py
            result = engine.rewrite_hostile_text(hostile_text, context)
            
    else:
        form = BIFFGeneratorForm()

    return render(request, 'communication/biff_tool.html', {'form': form, 'result': result})