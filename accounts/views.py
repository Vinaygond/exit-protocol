"""
Authentication and User Management Views
"""
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from accounts.models import User, UserProfile, LoginHistory
from accounts.forms import (
    UserRegistrationForm, 
    UserLoginForm, 
    UserProfileForm,
    PasswordChangeForm
)


def register(request):
    """User registration"""
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            
            # Create user profile
            UserProfile.objects.create(user=user)
            
            # Log the registration
            LoginHistory.objects.create(
                user=user,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:512],
                success=True
            )
            
            # Log them in
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('core:dashboard')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})


def user_login(request):
    """User login"""
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            
            try:
                user = User.objects.get(email=email)
                
                # Check if account is locked
                if user.is_locked_out():
                    messages.error(
                        request, 
                        'Account temporarily locked due to failed login attempts. '
                        'Please try again in 30 minutes.'
                    )
                    return render(request, 'accounts/login.html', {'form': form})
                
                # Authenticate
                user_auth = authenticate(request, username=email, password=password)
                
                if user_auth is not None:
                    # Successful login
                    user.reset_failed_login()
                    user.last_login = timezone.now()
                    user.save()
                    
                    # Log the login
                    LoginHistory.objects.create(
                        user=user,
                        ip_address=get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')[:512],
                        success=True
                    )
                    
                    login(request, user_auth)
                    
                    next_url = request.GET.get('next', 'core:dashboard')
                    return redirect(next_url)
                else:
                    # Failed login
                    user.increment_failed_login()
                    LoginHistory.objects.create(
                        user=user,
                        ip_address=get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')[:512],
                        success=False
                    )
                    messages.error(request, 'Invalid email or password.')
            
            except User.DoesNotExist:
                messages.error(request, 'Invalid email or password.')
    else:
        form = UserLoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def user_logout(request):
    """User logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('core:home')


@login_required
def profile(request):
    """User profile view and edit"""
    try:
        user_profile = request.user.profile
    except UserProfile.DoesNotExist:
        user_profile = UserProfile.objects.create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=user_profile)
        if form.is_valid():
            form.save()
            
            # Update user info
            request.user.first_name = form.cleaned_data.get('first_name', request.user.first_name)
            request.user.last_name = form.cleaned_data.get('last_name', request.user.last_name)
            request.user.phone_number = form.cleaned_data.get('phone_number', request.user.phone_number)
            request.user.save()
            
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=user_profile)
    
    # Get recent login history
    recent_logins = LoginHistory.objects.filter(
        user=request.user
    ).order_by('-timestamp')[:10]
    
    context = {
        'form': form,
        'recent_logins': recent_logins,
    }
    
    return render(request, 'accounts/profile.html', context)


@login_required
def change_password(request):
    """Change user password"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            user.password_changed_at = timezone.now()
            user.save()
            
            # Update session to prevent logout
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, user)
            
            messages.success(request, 'Password changed successfully!')
            return redirect('accounts:profile')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'accounts/change_password.html', {'form': form})


@login_required
def security_log(request):
    """View security activity log"""
    login_history = LoginHistory.objects.filter(
        user=request.user
    ).order_by('-timestamp')[:50]
    
    return render(request, 'accounts/security_log.html', {
        'login_history': login_history
    })


def get_client_ip(request):
    """Extract client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

