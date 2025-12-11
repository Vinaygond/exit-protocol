from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps
from .models import UserSubscription

def premium_required(view_func):
    """
    Decorator: Redirects non-paying users to the pricing page.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # 1. Get or Create Subscription object if missing
        sub, created = UserSubscription.objects.get_or_create(user=request.user)
        
        # 2. Check Active Status
        # For prototype/demo purposes, you can manually set is_active=True in Admin
        if not sub.is_active or sub.plan_type == 'free':
            messages.info(request, "🔒 This feature requires a Pro subscription.")
            return redirect('subscriptions:pricing')
            
        return view_func(request, *args, **kwargs)
    return _wrapped_view