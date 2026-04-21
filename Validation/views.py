from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views import View
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from login.models import UserProfile  # Use existing login UserProfile
from .forms import PhoneVerificationForm, OTPVerificationForm, AddressVerificationForm
from .models import PhoneOTP
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from twilio.rest import Client
from django.conf import settings
import json

@method_decorator(login_required, name='dispatch')
class SendPhoneOTPView(View):
    template_name = 'phone_verification.html'

    def get(self, request):
        profile = UserProfile.objects.get(user=request.user)
        if profile.phone_verified == profile.PHONE_VERIFIED:
            return redirect('MyAccount:profile')
        return render(request, self.template_name)

    def post(self, request):
        form = PhoneVerificationForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data['phone_number']
            
            # Delete old OTPS
            PhoneOTP.objects.filter(phone_number=phone).delete()
            
            # Create new OTP
            otp_obj = PhoneOTP.objects.create(phone_number=phone, user=request.user)
            
            # Send SMS via Twilio
            try:
                client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                client.messages.create(
                    body=f'Your ShopZone OTP: {otp_obj.otp}',
                    from_=settings.TWILIO_PHONE_NUMBER,
                    to=str(phone)
                )
            except:
                pass  # Fallback for dev
            
            request.session['pending_phone'] = str(phone)
            messages.success(request, f'OTP sent to {phone.as_e164}')
            return redirect('validation:verify_otp')
        return render(request, self.template_name, {'form': form})

@method_decorator(login_required, name='dispatch')
class VerifyOTPView(View):
    template_name = 'verify_otp.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        # Handle single OTP or 6-digit inputs
        otp_input = request.POST.get('otp') or ''
        if not otp_input:
            for i in range(1, 7):
                digit = request.POST.get(f'otp_digit_{i}', '')
                otp_input += digit

        form = OTPVerificationForm({'otp': otp_input})
        if form.is_valid() and 'pending_phone' in request.session:
            phone = request.session['pending_phone']
            
            try:
                otp_obj = PhoneOTP.objects.filter(
                    phone_number=phone,
                    expires_at__gt=timezone.now()
                ).latest('created_at')
                
                if otp_obj.is_valid(otp_input):
                    profile = UserProfile.objects.get(user=request.user)
                    profile.phone_number = phone
                    profile.phone_verified = profile.PHONE_VERIFIED
                    profile.save()
                    otp_obj.is_used = True
                    otp_obj.save()
                    
                    del request.session['pending_phone']
                    messages.success(request, 'Phone verified successfully!')
                    return redirect('MyStore:checkout')
                else:
                    otp_obj.attempts += 1
                    otp_obj.save()
                    messages.error(request, 'Invalid or expired OTP.')
            except PhoneOTP.DoesNotExist:
                messages.error(request, 'No OTP found.')
        return render(request, self.template_name, {'form': form})

@login_required
def verify_address(request):
    profile = UserProfile.objects.get(user=request.user)
    if request.method == 'POST':
        form = AddressVerificationForm(request.POST)
        if form.is_valid():
            profile.address_line1 = form.cleaned_data['address_line1']
            profile.city = form.cleaned_data['city']
            profile.state = form.cleaned_data['state']
            profile.pincode = form.cleaned_data['pincode']
            profile.save()
            messages.success(request, 'Address verified!')
            return redirect('MyStore:profile')
    else:
        initial = {
            'address_line1': profile.address_line1,
            'city': profile.city,
            'state': profile.state,
            'pincode': profile.pincode,
        }
        form = AddressVerificationForm(initial=initial)
    return render(request, 'verify_address.html', {'form': form})