from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField  # pip install django-phonenumber-field[phonenumbers]
from datetime import timedelta

class UserProfile(models.Model):
    # 🔥 PHONE VERIFICATION STATES (matches your views.py)
    PHONE_NOT_SET = 'not_set'
    PHONE_PENDING = 'pending'
    PHONE_VERIFIED = 'verified'
    
    PHONE_STATUS_CHOICES = [
        (PHONE_NOT_SET, 'Not Set'),
        (PHONE_PENDING, 'Pending Verification'),
        (PHONE_VERIFIED, 'Verified'),
    ]
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='userprofile'  # 🔥 FIXES reverse accessor clash
    )
    
    # 🔥 PHONE VALIDATION FIELDS
    phone_number = PhoneNumberField(blank=True, null=True)  # International format +91XXXXXXXXXX
    phone_verified = models.CharField(
        max_length=20, 
        choices=PHONE_STATUS_CHOICES, 
        default=PHONE_NOT_SET
    )
    
    # ADDRESS FIELDS (split for validation/checkout)
    address_line1 = models.CharField(max_length=100, blank=True)
    address_line2 = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=50, blank=True)
    state = models.CharField(max_length=50, blank=True)
    pincode = models.CharField(max_length=10, blank=True)
    
    # OTHER PROFILE FIELDS
    date_of_birth = models.DateField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        status = self.get_phone_verified_display()
        return f"{self.user.username} - {self.phone_number} ({status})"

    @property
    def full_address(self):
        """Combined address for display"""
        parts = [self.address_line1, self.address_line2, self.city, self.state, self.pincode]
        return ', '.join(filter(None, parts))

    def is_address_complete(self):
        """Check if address is ready for checkout"""
        return bool(self.pincode and self.city and self.state)

class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    is_used = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Reset token for {self.user.username}"
    
    def is_expired(self):
        """Check if token is older than 24 hours"""
        return timezone.now() > self.created_at + timedelta(hours=24)