from django.db.models import Count
from django.contrib.auth.decorators import login_required
from django.shortcuts import resolve_url, render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.http import require_POST
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.urls import reverse
import uuid
from .models import UserProfile, PasswordResetToken
from datetime import timedelta
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from MyStore.models import *

User = get_user_model()

def home(request):
    categories = Category.objects.all().annotate(product_count=Count('products'))
    featured_products = Product.objects.filter(is_featured=True, is_active=True)[:8]
    context = {
        'categories': categories,
        'products': featured_products,
    }
    return render(request, 'homePage.html', context)

def login_view(request):
    if request.user.is_authenticated:
        return redirect('MyAccount:home')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        remember_me = request.POST.get('remember_me')

        if not username or not password:
            messages.error(request, 'Please provide username/email and password')
            return render(request, 'loginpage.html')

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)

            # 🔥 PHONE VERIFICATION CHECK
            try:
                profile = user.userprofile
                if profile.phone_verified != profile.PHONE_VERIFIED:
                    messages.info(request, 'Please verify your phone number first')
                    return redirect('validation:send_phone_otp')
            except:
                messages.info(request, 'Please verify your phone number first')
                return redirect('validation:send_phone_otp')

            # Session expiry
            if remember_me:
                request.session.set_expiry(1209600)  # 2 weeks
            else:
                request.session.set_expiry(0)

            messages.success(request, f'Welcome back, {user.username}!')
            next_url = request.GET.get('next')
            if next_url and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
            ):
                return redirect(next_url)
            return redirect('MyAccount:home')

        messages.error(request, 'Invalid username/email or password')

    return render(request, 'loginpage.html')

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('login:home')
  
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        # Validation
        if not all([username, email, password, confirm_password]):
            messages.error(request, 'All fields are required')
            return render(request, 'signup.html')
        
        if password != confirm_password:
            messages.error(request, 'Passwords do not match')
            return render(request, 'signup.html')
        
        try:
            validate_password(password)
        except ValidationError as e:
            for error in e.messages:
                messages.error(request, error)
            return render(request, 'signup.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return render(request, 'signup.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered')
            return render(request, 'signup.html')
        
        try:
            # Create user + profile
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            UserProfile.objects.get_or_create(user=user)
            
            # 🔥 AUTO-LOGIN + PHONE VERIFICATION
            login(request, user)
            messages.success(request, 'Account created! Please verify your phone number.')
            return redirect('validation:send_phone_otp')
            
        except Exception as e:
            messages.error(request, 'An error occurred during registration')
            return render(request, 'signup.html')
  
    return render(request, 'signup.html')

def forgot_password_view(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()

        if not email:
            messages.error(request, 'Please provide your email address')
            return render(request, 'forgot_password.html')

        try:
            user = User.objects.get(email=email)

            # Delete old tokens
            PasswordResetToken.objects.filter(user=user, is_used=False).delete()

            # Create new token
            token = str(uuid.uuid4())
            PasswordResetToken.objects.create(user=user, token=token)

            # Build reset URL
            reset_url = request.build_absolute_uri(
                reverse('login:reset_password', args=[token])
            )

            # Send email
            send_mail(
                subject='Password Reset Request - ShopZone',
                message=f'''Hello {user.first_name or user.username},

We received a request to reset your password. Click the link below to proceed:

{reset_url}

This link will expire in 24 hours.

If you didn't request this, please ignore this email.

Best regards,
ShopZone Team
                ''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )

            messages.success(request, 'If that email exists, a reset link has been sent.')
            return redirect('login:login')

        except User.DoesNotExist:
            messages.success(request, 'If that email exists, a reset link has been sent.')
            return redirect('login:login')
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            return render(request, 'forgot_password.html')

    return render(request, 'forgot_password.html')

def reset_password_view(request, token):
    try:
        reset_token = PasswordResetToken.objects.get(token=token, is_used=False)
        
        # Check expiry (24 hours)
        expiry_time = reset_token.created_at + timedelta(hours=24)
        if timezone.now() > expiry_time:
            reset_token.is_used = True
            reset_token.save()
            messages.error(request, 'Reset link has expired. Please request a new one.')
            return redirect('login:forgot_password')
        
        if request.method == 'POST':
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            if not new_password or not confirm_password:
                messages.error(request, 'Please fill in both password fields')
                return render(request, 'password_reset_confirm.html', {'token': token})
            
            if new_password != confirm_password:
                messages.error(request, 'Passwords do not match')
                return render(request, 'password_reset_confirm.html', {'token': token})
            
            try:
                validate_password(new_password, user=reset_token.user)
            except ValidationError as e:
                for error in e.messages:
                    messages.error(request, error)
                return render(request, 'password_reset_confirm.html', {'token': token})
            
            # Update password
            user = reset_token.user
            user.set_password(new_password)
            user.save()
            
            # Mark token used
            reset_token.is_used = True
            reset_token.save()
            
            messages.success(request, 'Password changed successfully! You can now login.')
            return redirect('login:password_reset_complete')
        
        return render(request, 'password_reset_confirm.html', {'token': token})
        
    except PasswordResetToken.DoesNotExist:
        messages.error(request, 'Invalid or expired reset link')
        return redirect('login:forgot_password')

def password_reset_complete_view(request):
    return render(request, 'password_reset_complete.html')

@login_required
def logout_view(request):
    username = request.user.username
    logout(request)
    messages.success(request, f'Goodbye, {username}! You have been logged out.')
    return redirect('login:login')

@login_required
def dashboard_view(request):
    return render(request, 'dashboard.html')

@login_required
def profile_view(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
  
    if request.method == 'POST':
        # 🔥 PHONE VERIFICATION CHECK ON PROFILE UPDATE
        if (not profile.phone_verified == profile.PHONE_VERIFIED or 
            request.POST.get('phone_number')):
            messages.info(request, 'Phone verification required')
            return redirect('validation:send_phone_otp')
    
    return render(request, 'profile.html', {'profile': profile})

def password_reset_done_view(request):
    return render(request, "password_reset_done.html")