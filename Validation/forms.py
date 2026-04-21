from django import forms
from phonenumber_field.formfields import PhoneNumberField

class PhoneVerificationForm(forms.Form):
    phone_number = PhoneNumberField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+91 9876543210',
            'autocomplete': 'tel'
        })
    )

class OTPVerificationForm(forms.Form):
    otp = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '123456',
            'autocomplete': 'one-time-code',
            'inputmode': 'numeric'
        })
    )

class AddressVerificationForm(forms.Form):
    address_line1 = forms.CharField(max_length=100, widget=forms.Textarea(attrs={'rows': 2}))
    city = forms.CharField(max_length=50)
    state = forms.CharField(max_length=50)
    pincode = forms.CharField(max_length=10)