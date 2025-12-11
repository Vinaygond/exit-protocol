from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import UserSubscription

@login_required
def pricing_page(request):
    """
    Display subscription tiers.
    """
    return render(request, 'subscriptions/pricing.html')

@login_required
def upgrade_success(request):
    """
    Mock View: Simulates a successful Stripe payment for the demo.
    """
    sub, created = UserSubscription.objects.get_or_create(user=request.user)
    sub.plan_type = 'pro'
    sub.is_active = True
    sub.save()
    
    messages.success(request, "🚀 Upgrade Successful! You now have full access to Forensic Tools.")
    return redirect('core:dashboard')