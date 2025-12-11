from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils import timezone
from datetime import timedelta

# Import models
from cases.models import Case, CaseParty
from finance.models import FinancialAccount, Transaction
from evidence.models import EvidenceDocument
from communication.models import Message
from audit.models import SystemAlert

def home(request):
    """
    Landing Page View.
    If the user is already logged in, redirect them immediately to the dashboard.
    """
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    return render(request, 'home.html')

def health_check(request):
    """Simple health check for AWS/Azure load balancers"""
    return HttpResponse("OK", status=200)

@login_required
def switch_case(request, case_id):
    """
    Switch the active case in the session.
    Verifies the user actually belongs to the case before switching.
    """
    # Verify user has access to this case
    case_access = get_object_or_404(CaseParty, user=request.user, case__id=case_id)
    
    # Set session variable
    request.session['active_case_id'] = str(case_access.case.id)
    
    return redirect('core:dashboard')

@login_required
def dashboard(request):
    """
    Main Dashboard View.
    Aggregates data from Finance, Evidence, and Communication apps.
    """
    user = request.user
    
    # 1. Determine Active Case
    active_case_id = request.session.get('active_case_id')
    active_case = None

    if active_case_id:
        try:
            active_case = Case.objects.get(id=active_case_id)
        except Case.DoesNotExist:
            pass
    
    # Fallback: Find the most recent case the user is a party to
    if not active_case:
        latest_party = CaseParty.objects.filter(user=user).order_by('-joined_at').first()
        if latest_party:
            active_case = latest_party.case
            request.session['active_case_id'] = str(active_case.id)

    # If new user has no cases yet
    if not active_case:
        return render(request, 'core/dashboard.html', {
            'case': None,
            'account_count': 0, 
            'evidence_count': 0, 
            'total_risks': 0, 
            'readiness_score': 0,
            'activity_feed': []
        })

    # ---------------------------------------------------------
    # 2. Gather Statistics (Card Data)
    # ---------------------------------------------------------
    
    # Card 1: Financial Accounts
    account_count = FinancialAccount.objects.filter(
        case=active_case, 
        is_active=True
    ).count()
    
    # Footer text for financial card
    last_tx = Transaction.objects.filter(case=active_case).order_by('-updated_at').first()
    last_financial_update = "No activity yet"
    if last_tx:
        diff = timezone.now() - last_tx.updated_at
        if diff.days == 0:
            hours = diff.seconds // 3600
            last_financial_update = f"Updated {hours}h ago"
        else:
            last_financial_update = f"Updated {diff.days}d ago"

    # Card 2: Evidence Locker
    evidence_count = EvidenceDocument.objects.filter(case=active_case).count()
    
    # Documents added this week
    one_week_ago = timezone.now() - timedelta(days=7)
    evidence_this_week = EvidenceDocument.objects.filter(
        case=active_case, 
        upload_timestamp__gte=one_week_ago
    ).count()

    # Card 3: Conflict/Risk Alerts
    hostile_msg_count = Message.objects.filter(
        case=active_case, 
        flagged_as_hostile=True
    ).count()
    
    critical_alerts = SystemAlert.objects.filter(
        case=active_case,
        is_resolved=False,
        priority__in=['high', 'critical']
    ).count()
    
    total_risks = hostile_msg_count + critical_alerts
    risk_text = "Low hostility detected" if total_risks == 0 else "High hostility detected"

    # Card 4: Readiness Score (Algorithmic)
    readiness_score = 10 
    if account_count > 0: readiness_score += 20
    if evidence_count > 0: readiness_score += 20
    if CaseParty.objects.filter(case=active_case).count() > 1: readiness_score += 10
    if active_case.filing_date: readiness_score += 15
    if readiness_score > 100: readiness_score = 100

    # ---------------------------------------------------------
    # 3. Build Unified Activity Feed
    # ---------------------------------------------------------
    
    recent_evidence = EvidenceDocument.objects.filter(case=active_case).order_by('-upload_timestamp')[:5]
    recent_messages = Message.objects.filter(case=active_case).order_by('-sent_at')[:5]
    recent_alerts = SystemAlert.objects.filter(case=active_case).order_by('-created_at')[:5]

    activity_feed = []

    for item in recent_evidence:
        activity_feed.append({
            'type': 'evidence',
            'icon': 'bi-upload',
            'color_class': 'text-primary bg-blue-50', 
            'title': f'Uploaded "{item.original_filename}"',
            'subtitle': 'Evidence Locker',
            'timestamp': item.upload_timestamp
        })

    for item in recent_messages:
        icon = 'bi-exclamation-diamond-fill' if item.flagged_as_hostile else 'bi-chat-dots'
        color = 'text-danger bg-red-50' if item.flagged_as_hostile else 'text-dark bg-gray-50'
        
        activity_feed.append({
            'type': 'message',
            'icon': icon,
            'color_class': color,
            'title': f'Message: {item.subject}',
            'subtitle': 'Secure Comms',
            'timestamp': item.sent_at
        })

    for item in recent_alerts:
        activity_feed.append({
            'type': 'alert',
            'icon': 'bi-bell',
            'color_class': 'text-warning bg-yellow-50',
            'title': item.title,
            'subtitle': 'System Alert',
            'timestamp': item.created_at
        })

    # Sort combined list by timestamp descending
    activity_feed.sort(key=lambda x: x['timestamp'], reverse=True)
    activity_feed = activity_feed[:6]

    context = {
        'case': active_case,
        'user': user,
        'account_count': account_count,
        'last_financial_update': last_financial_update,
        'evidence_count': evidence_count,
        'evidence_this_week': evidence_this_week,
        'total_risks': total_risks,
        'risk_text': risk_text,
        'readiness_score': readiness_score,
        'activity_feed': activity_feed,
    }

    return render(request, 'core/dashboard.html', context)

def legal_directory(request):
    """Placeholder view for Legal Directory"""
    return render(request, 'core/legal_directory.html')