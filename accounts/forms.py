"""
Forms for User Management and Authentication
"""
from django import forms
from django.contrib.auth.forms import PasswordChangeForm as DjangoPasswordChangeForm
from django.core.exceptions import ValidationError
from accounts.models import User, UserProfile
import re


class UserRegistrationForm(forms.ModelForm):
    """User registration form with password validation"""
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password'
        }),
        min_length=12,
        label='Password',
        help_text='Minimum 12 characters with letters, numbers, and special characters'
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password'
        }),
        label='Confirm Password'
    )
    
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone_number']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'your@email.com'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'First name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Last name'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+1234567890'
            }),
        }
    
    def clean_email(self):
        """Validate email is unique and properly formatted"""
        email = self.cleaned_data.get('email', '').lower().strip()
        
        if User.objects.filter(email=email).exists():
            raise ValidationError('This email address is already registered.')
        
        return email
    
    def clean_password(self):
        """Validate password strength"""
        password = self.cleaned_data.get('password')
        
        if not password:
            return password
        
        # Check for at least one uppercase letter
        if not re.search(r'[A-Z]', password):
            raise ValidationError('Password must contain at least one uppercase letter.')
        
        # Check for at least one lowercase letter
        if not re.search(r'[a-z]', password):
            raise ValidationError('Password must contain at least one lowercase letter.')
        
        # Check for at least one digit
        if not re.search(r'\d', password):
            raise ValidationError('Password must contain at least one number.')
        
        # Check for at least one special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError('Password must contain at least one special character.')
        
        return password
    
    def clean(self):
        """Validate passwords match"""
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm:
            if password != password_confirm:
                raise ValidationError('Passwords do not match.')
        
        return cleaned_data


class UserLoginForm(forms.Form):
    """User login form"""
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'your@email.com',
            'autofocus': True
        }),
        label='Email Address'
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Enter your password'
        }),
        label='Password'
    )
    
    def clean_email(self):
        """Normalize email"""
        return self.cleaned_data.get('email', '').lower().strip()


class UserProfileForm(forms.ModelForm):
    """User profile editing form"""
    first_name = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    phone_number = forms.CharField(
        max_length=17,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+1234567890'
        })
    )
    
    class Meta:
        model = UserProfile
        fields = [
            'address_line1', 'address_line2', 'city', 'state', 'zip_code',
            'timezone', 'notifications_enabled', 'email_notifications', 
            'sms_notifications', 'bar_number', 'law_firm'
        ]
        widgets = {
            'address_line1': forms.TextInput(attrs={'class': 'form-control'}),
            'address_line2': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={
                'class': 'form-control',
                'maxlength': '2',
                'placeholder': 'CA'
            }),
            'zip_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '12345'
            }),
            'timezone': forms.Select(attrs={'class': 'form-select'}),
            'bar_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'For attorneys only'
            }),
            'law_firm': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'For attorneys only'
            }),
            'notifications_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'email_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sms_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'address_line1': 'Street Address',
            'address_line2': 'Apt/Suite (optional)',
            'zip_code': 'ZIP Code',
            'bar_number': 'Bar Number',
            'law_firm': 'Law Firm',
        }
        help_texts = {
            'timezone': 'Select your local timezone',
            'bar_number': 'Only required for attorney users',
            'law_firm': 'Only required for attorney users',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Pre-populate user fields if instance exists
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['phone_number'].initial = self.instance.user.phone_number
        
        # Add timezone choices
        self.fields['timezone'].choices = [
            ('America/New_York', 'Eastern Time'),
            ('America/Chicago', 'Central Time'),
            ('America/Denver', 'Mountain Time'),
            ('America/Los_Angeles', 'Pacific Time'),
            ('America/Anchorage', 'Alaska Time'),
            ('Pacific/Honolulu', 'Hawaii Time'),
            ('UTC', 'UTC'),
        ]


class PasswordChangeForm(DjangoPasswordChangeForm):
    """Custom password change form with enhanced validation"""
    old_password = forms.CharField(
        label='Current Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter current password'
        })
    )
    new_password1 = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new password'
        }),
        help_text='Minimum 12 characters with letters, numbers, and special characters'
    )
    new_password2 = forms.CharField(
        label='Confirm New Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password'
        })
    )
    
    def clean_new_password1(self):
        """Validate new password strength"""
        password = self.cleaned_data.get('new_password1')
        
        if not password:
            return password
        
        # Minimum length
        if len(password) < 12:
            raise ValidationError('Password must be at least 12 characters long.')
        
        # Check for at least one uppercase letter
        if not re.search(r'[A-Z]', password):
            raise ValidationError('Password must contain at least one uppercase letter.')
        
        # Check for at least one lowercase letter
        if not re.search(r'[a-z]', password):
            raise ValidationError('Password must contain at least one lowercase letter.')
        
        # Check for at least one digit
        if not re.search(r'\d', password):
            raise ValidationError('Password must contain at least one number.')
        
        # Check for at least one special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError('Password must contain at least one special character.')
        
        # Check password is not too similar to email
        user = self.user
        if user.email and user.email.split('@')[0].lower() in password.lower():
            raise ValidationError('Password cannot be too similar to your email address.')
        
        return password


class EmailVerificationForm(forms.Form):
    """Form for email verification code"""
    verification_code = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control text-center',
            'placeholder': '000000',
            'maxlength': '6'
        }),
        label='Verification Code',
        help_text='Enter the 6-digit code sent to your email'
    )
    
    def clean_verification_code(self):
        """Validate verification code format"""
        code = self.cleaned_data.get('verification_code', '').strip()
        
        if not code.isdigit():
            raise ValidationError('Verification code must contain only numbers.')
        
        return code


class PasswordResetRequestForm(forms.Form):
    """Form for requesting password reset"""
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your@email.com'
        }),
        label='Email Address',
        help_text='Enter the email address associated with your account'
    )
    
    def clean_email(self):
        """Normalize and validate email exists"""
        email = self.cleaned_data.get('email', '').lower().strip()
        
        # Note: In production, you might want to NOT reveal if email exists
        # for security reasons (prevents enumeration attacks)
        if not User.objects.filter(email=email).exists():
            raise ValidationError(
                'If this email address exists in our system, '
                'you will receive a password reset link.'
            )
        
        return email


class PasswordResetConfirmForm(forms.Form):
    """Form for confirming password reset with new password"""
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new password'
        }),
        min_length=12,
        label='New Password',
        help_text='Minimum 12 characters with letters, numbers, and special characters'
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password'
        }),
        label='Confirm Password'
    )
    
    def clean(self):
        """Validate passwords match"""
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if new_password and confirm_password:
            if new_password != confirm_password:
                raise ValidationError('Passwords do not match.')
        
        return cleaned_data