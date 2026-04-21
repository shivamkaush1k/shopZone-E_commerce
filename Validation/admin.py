from django.contrib import admin
from django.utils import timezone
from .models import PhoneOTP

@admin.register(PhoneOTP)
class PhoneOTPAdmin(admin.ModelAdmin):
    list_display = ['phone_number', 'user', 'otp', 'attempts', 'expires_at', 'is_used']
    list_filter = ['is_used', 'attempts']
    readonly_fields = ['otp', 'created_at']
    
    actions = ['delete_expired']
    def delete_expired(self, request, queryset):
        expired = queryset.filter(expires_at__lt=timezone.now())
        count = expired.delete()[0]
        self.message_user(request, f'{count} expired OTPs deleted.')
    delete_expired.short_description = 'Delete expired OTPs'