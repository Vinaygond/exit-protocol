from django.db import models
from django.conf import settings
from django.utils import timezone

class UserSubscription(models.Model):
    """
    Tracks the subscription status of a user.
    """
    PLAN_CHOICES = [
        ('free', 'Free Tier'),
        ('pro', 'Pro Protocol ($49/mo)'),
        ('attorney', 'Attorney/Firm ($199/mo)'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscription')
    stripe_customer_id = models.CharField(max_length=100, blank=True)
    stripe_subscription_id = models.CharField(max_length=100, blank=True)
    
    plan_type = models.CharField(max_length=20, choices=PLAN_CHOICES, default='free')
    is_active = models.BooleanField(default=False)
    
    current_period_end = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.get_plan_type_display()}"

    def has_access(self, feature_name):
        """
        Gate logic: Check if user can access a specific feature.
        """
        if self.plan_type in ['pro', 'attorney'] and self.is_active:
            return True
            
        # Free tier limitations
        if feature_name == 'biff_ai': return False
        if feature_name == 'libr_forensics': return False
        if feature_name == 'pdf_export': return False
        
        return True