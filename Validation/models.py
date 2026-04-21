from django.db import models
from django.conf import settings
from django.utils import timezone
import random
from phonenumber_field.modelfields import PhoneNumberField

class PhoneOTP(models.Model):
    otp_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='phone_otps')
    phone_number = PhoneNumberField()
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    is_used = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Phone OTP'
        verbose_name_plural = 'Phone OTPs'

    def save(self, *args, **kwargs):
        if not self.pk:
            self.otp = ''.join([str(random.randint(0,9)) for _ in range(6)])
            self.expires_at = timezone.now() + timezone.timedelta(minutes=5)
        super().save(*args, **kwargs)

    def is_valid(self, input_otp):
        return (not self.is_used and self.expires_at > timezone.now() and 
                self.otp == input_otp and self.attempts < 3)