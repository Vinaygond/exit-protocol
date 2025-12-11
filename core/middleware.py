"""
Custom Middleware for Exit Protocol
Implements case isolation, smart context loading, and security features.
"""
from django.utils.functional import SimpleLazyObject
from django.shortcuts import redirect
from django.urls import reverse
from cases.models import Case, CaseParty

# Import models inside methods or safely to avoid circular import risks during startup
from django.apps import apps

def get_active_case(request):
    """
    Robust case selector that runs on every request.
    Priority:
    1. Session ID (Fastest)
    2. Database Fallback (Most recent active case) - Prevents Redirect Loops
    """
    if not request.user.is_authenticated:
        return None

    # 1. Try fetching from Session
    active_case_id = request.session.get('active_case_id')
    if active_case_id:
        try:
            return Case.objects.get(id=active_case_id, is_active=True)
        except Case.DoesNotExist:
            # Session ID is stale, clear it and fall through to DB lookup
            del request.session['active_case_id']

    # 2. Fallback: Find the most recent case the user joined
    # This ensures that even if session is empty, we find their main case
    try:
        latest_party = CaseParty.objects.filter(
            user=request.user, 
            is_active=True,
            case__is_active=True
        ).select_related('case').order_by('-joined_at').first()

        if latest_party:
            # Found one! Save to session to speed up next request
            request.session['active_case_id'] = str(latest_party.case.id)
            return latest_party.case
    except Exception:
        # Failsafe for migration/startup edge cases
        return None

    return None


class CaseContextMiddleware:
    """
    Injects the active case into every request as 'request.case'.
    This is the core engine that powers the Dashboard, Finance, and Evidence views.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Lazy load the case so we don't hit DB for static files or irrelevant requests
        request.case = SimpleLazyObject(lambda: get_active_case(request))
        
        response = self.get_response(request)
        return response


class SecurityHeadersMiddleware:
    """
    Add additional security headers
    Beyond what Django provides by default
    """
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Additional security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Content Security Policy (Basic implementation)
        csp = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com",
            "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com",
            "img-src 'self' data: https:",
            "font-src 'self' data:",
            "connect-src 'self'",
            "frame-ancestors 'none'",
        ]
        response['Content-Security-Policy'] = "; ".join(csp)
        
        return response


class AnomalyDetectionMiddleware:
    """
    Detect and log suspicious activities
    E.g., login from new IP address
    """
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.user.is_authenticated:
            # Perform checks safely
            self._check_login_location(request)
        
        response = self.get_response(request)
        return response
    
    def _check_login_location(self, request):
        """
        Check if user is logging in from unusual location
        """
        current_ip = self._get_client_ip(request)
        
        try:
            # Lazy import to avoid circular dependencies during app initialization
            LoginHistory = apps.get_model('accounts', 'LoginHistory')
            SystemAlert = apps.get_model('audit', 'SystemAlert')
            
            # Get user's recent known IPs
            recent_ips = LoginHistory.objects.filter(
                user=request.user,
                success=True
            ).values_list('ip_address', flat=True).distinct()[:10]
            
            # If we have history, and this IP is new, log an alert
            if recent_ips and current_ip not in recent_ips:
                # Check if we already alerted for this IP recently to avoid spam
                exists = SystemAlert.objects.filter(
                    affected_user=request.user,
                    title='New login location detected',
                    message__contains=current_ip
                ).exists()
                
                if not exists:
                    SystemAlert.objects.create(
                        alert_type='security',
                        priority='medium',
                        title='New login location detected',
                        message=f'User {request.user.email} logged in from new IP: {current_ip}',
                        affected_user=request.user
                    )
        except Exception:
            # Middleware should never crash the request flow
            pass
    
    def _get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip