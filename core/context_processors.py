"""
Context Processors for Exit Protocol
Makes common variables available in all templates
"""
from communication.models import Message


def case_context(request):
    """
    Add case information and common data to template context
    """
    context = {
        'case': getattr(request, 'case', None),
    }
    
    # Add unread message count if user is authenticated
    if request.user.is_authenticated:
        unread_count = Message.objects.filter(
            recipients=request.user,
            messagerecipient__is_read=False
        ).count()
        context['unread_count'] = unread_count
    
    return context