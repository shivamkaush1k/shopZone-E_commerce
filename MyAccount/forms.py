from django import forms
from django.core.validators import RegexValidator

from .models import (
    UserProfile,
    Address,
    ContactMessage,
    NotificationSettings,
    OrderTrackingNote,
)


class UserProfileForm(forms.ModelForm):
    phone_number = forms.CharField(
        required=False,
        max_length=15,
        validators=[
            RegexValidator(
                r'^\+?1?\d{9,15}$',
                'Enter a valid phone number.'
            )
        ]
    )
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    class Meta:
        model = UserProfile
        fields = [
            'phone_number',
            'bio',
            'gender',
            'newsletter_subscription',
            'email_notifications',
            'sms_notifications',
            'profile_visibility',
            'date_of_birth',
            'profile_picture',
        ]

class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = [
            'full_name',
            'phone_number',
            'address_line_1',
            'address_line_2',
            'city',
            'state',
            'postal_code',
            'country',
            'address_type',
            'is_default',
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address_line_1': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'address_line_2': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 20}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'address_type': forms.Select(attrs={'class': 'form-select'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ContactMessageForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        exclude = ['user', 'is_resolved', 'created_at']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 4}),
            'phone': forms.TextInput(attrs={'maxlength': 15}),
        }

    def clean_name(self):
        name = (self.cleaned_data.get('name') or '').strip()
        if not name:
            raise forms.ValidationError('Name is required.')
        return name

    def clean_subject(self):
        subject = (self.cleaned_data.get('subject') or '').strip()
        if not subject:
            raise forms.ValidationError('Subject is required.')
        return subject

    def clean_message(self):
        message = (self.cleaned_data.get('message') or '').strip()
        if not message:
            raise forms.ValidationError('Message is required.')
        return message


class NotificationSettingsForm(forms.ModelForm):
    class Meta:
        model = NotificationSettings
        fields = ['order_updates', 'promotional_emails', 'newsletter', 'sms_notifications', 'app_notifications']  # Added explicit fields
        widgets = {
            'order_updates': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'promotional_emails': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'newsletter': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sms_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'app_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'order_updates': 'Order status updates',
            'promotional_emails': 'Promotional emails',
            'newsletter': 'Weekly newsletter',
            'sms_notifications': 'SMS notifications (Twilio)',
            'app_notifications': 'Push notifications',
        }

class OrderTrackingNoteForm(forms.ModelForm):
    class Meta:
        model = OrderTrackingNote
        exclude = ['user', 'created_at']
        widgets = {
            'note': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_order_id(self):
        order_id = (self.cleaned_data.get('order_id') or '').strip()
        if not order_id:
            raise forms.ValidationError('Order ID is required.')
        return order_id

    def clean_note(self):
        note = (self.cleaned_data.get('note') or '').strip()
        if not note:
            raise forms.ValidationError('Note is required.')
        return note