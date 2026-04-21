from decimal import Decimal, InvalidOperation

from django import forms

from .models import PaymentMethod


class PaymentMethodForm(forms.ModelForm):
    class Meta:
        model = PaymentMethod
        fields = [
            'method_type',
            'card_holder_name',
            'card_number',
            'expiry_month',
            'expiry_year',
            'upi_id',
            'paypal_email',
            'bank_name',
            'account_identifier',
            'is_default',
        ]
        widgets = {
            'method_type': forms.Select(attrs={'class': 'form-select'}),
            'card_holder_name': forms.TextInput(attrs={'class': 'form-control'}),
            'card_number': forms.TextInput(attrs={'class': 'form-control'}),
            'expiry_month': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 12}),
            'expiry_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'upi_id': forms.TextInput(attrs={'class': 'form-control'}),
            'paypal_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'bank_name': forms.TextInput(attrs={'class': 'form-control'}),
            'account_identifier': forms.TextInput(attrs={'class': 'form-control'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        method_type = cleaned_data.get('method_type')

        card_holder_name = (cleaned_data.get('card_holder_name') or '').strip()
        card_number = (cleaned_data.get('card_number') or '').strip()
        expiry_month = cleaned_data.get('expiry_month')
        expiry_year = cleaned_data.get('expiry_year')

        upi_id = (cleaned_data.get('upi_id') or '').strip()
        paypal_email = (cleaned_data.get('paypal_email') or '').strip()
        bank_name = (cleaned_data.get('bank_name') or '').strip()
        account_identifier = (cleaned_data.get('account_identifier') or '').strip()

        if method_type == 'card':
            if not card_holder_name:
                self.add_error('card_holder_name', 'Card holder name is required.')
            if not card_number:
                self.add_error('card_number', 'Card number is required.')
            elif not card_number.isdigit():
                self.add_error('card_number', 'Card number must contain digits only.')
            if not expiry_month:
                self.add_error('expiry_month', 'Expiry month is required.')
            if not expiry_year:
                self.add_error('expiry_year', 'Expiry year is required.')

        elif method_type == 'upi':
            if not upi_id:
                self.add_error('upi_id', 'UPI ID is required.')

        elif method_type == 'paypal':
            if not paypal_email:
                self.add_error('paypal_email', 'PayPal email is required.')

        elif method_type == 'bank':
            if not bank_name:
                self.add_error('bank_name', 'Bank name is required.')
            if not account_identifier:
                self.add_error('account_identifier', 'Account identifier is required.')

        return cleaned_data


class PaymentInitiateForm(forms.Form):
    PAYMENT_METHOD_CHOICES = [
        ('saved', 'Saved Payment Method'),
        ('new', 'New Payment Method'),
        ('cod', 'Cash on Delivery'),
    ]

    payment_method = forms.ChoiceField(
        choices=PAYMENT_METHOD_CHOICES,
        widget=forms.RadioSelect
    )

    saved_payment = forms.ModelChoiceField(
        queryset=PaymentMethod.objects.none(),
        required=False,
        empty_label="Select saved payment method",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    order_id = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    amount = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user is not None:
            self.fields['saved_payment'].queryset = PaymentMethod.objects.filter(
                user=user,
                is_active=True
            ).order_by('-is_default', '-created_at')

    def clean_amount(self):
        amount_raw = (self.cleaned_data.get('amount') or '').strip()
        try:
            amount = Decimal(amount_raw)
            if amount <= 0:
                raise forms.ValidationError('Amount must be greater than zero.')
            return amount
        except (InvalidOperation, ValueError):
            raise forms.ValidationError('Enter a valid payment amount.')

    def clean_order_id(self):
        order_id = (self.cleaned_data.get('order_id') or '').strip()
        if not order_id:
            raise forms.ValidationError('Order ID is required.')
        return order_id

    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')
        saved_payment = cleaned_data.get('saved_payment')

        if payment_method == 'saved' and not saved_payment:
            self.add_error('saved_payment', 'Please select a saved payment method.')

        return cleaned_data