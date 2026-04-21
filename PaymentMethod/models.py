from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.db import models, transaction
from django.db.models import Q
from django.utils import timezone

User = get_user_model()


upi_validator = RegexValidator(
    regex=r'^[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}$',
    message='Enter a valid UPI ID.'
)

card_digits_validator = RegexValidator(
    regex=r'^\d{12,19}$',
    message='Card number must contain 12 to 19 digits.'
)

last4_validator = RegexValidator(
    regex=r'^\d{4}$',
    message='This field must contain exactly 4 digits.'
)


class PaymentMethod(models.Model):
    PAYMENT_TYPES = [
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('upi', 'UPI'),
        ('paypal', 'PayPal'),
        ('net_banking', 'Net Banking'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='payment_methods'
    )
    method_type = models.CharField(max_length=20, choices=PAYMENT_TYPES)

    card_holder_name = models.CharField(max_length=100, blank=True, null=True)
    card_number = models.CharField(
        max_length=19,
        blank=True,
        null=True,
        validators=[card_digits_validator]
    )
    expiry_month = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )
    expiry_year = models.PositiveIntegerField(blank=True, null=True)
    card_last4 = models.CharField(
        max_length=4,
        blank=True,
        null=True,
        validators=[last4_validator]
    )

    upi_id = models.CharField(max_length=100, blank=True, null=True, validators=[upi_validator])
    paypal_email = models.EmailField(blank=True, null=True)
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    account_identifier = models.CharField(max_length=200, blank=True, null=True)

    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_default', '-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user'],
                condition=Q(is_default=True),
                name='unique_default_payment_method_per_user'
            ),
            models.UniqueConstraint(
                fields=['user', 'card_number'],
                condition=Q(card_number__isnull=False),
                name='unique_card_number_per_user'
            ),
            models.UniqueConstraint(
                fields=['user', 'upi_id'],
                condition=Q(upi_id__isnull=False),
                name='unique_upi_per_user'
            ),
        ]

    def __str__(self):
        if self.method_type in ['credit_card', 'debit_card'] and self.card_last4:
            return f"{self.get_method_type_display()} ending in {self.card_last4}"
        if self.method_type == 'upi' and self.upi_id:
            return f"UPI - {self.upi_id}"
        if self.method_type == 'paypal' and self.paypal_email:
            return f"PayPal - {self.paypal_email}"
        if self.method_type == 'net_banking' and self.account_identifier:
            return f"Net Banking - {self.account_identifier}"
        return self.get_method_type_display()

    def clean(self):
        current_year = timezone.now().year
        current_month = timezone.now().month
        card_types = ['credit_card', 'debit_card']

        if self.method_type in card_types:
            required = {
                'card_holder_name': self.card_holder_name,
                'card_number': self.card_number,
                'expiry_month': self.expiry_month,
                'expiry_year': self.expiry_year,
            }
            for field, value in required.items():
                if value in [None, '']:
                    raise ValidationError({field: f'{field.replace("_", " ").title()} is required.'})

            if self.expiry_year < current_year:
                raise ValidationError({'expiry_year': 'Expiry year cannot be in the past.'})

            if self.expiry_year == current_year and self.expiry_month < current_month:
                raise ValidationError({'expiry_month': 'Expiry month cannot be in the past.'})

            if self.card_number:
                self.card_last4 = self.card_number[-4:]

            self.upi_id = None
            self.paypal_email = None
            self.bank_name = None
            self.account_identifier = None

        elif self.method_type == 'upi':
            if not self.upi_id:
                raise ValidationError({'upi_id': 'UPI ID is required for UPI payments.'})

            self.card_holder_name = None
            self.card_number = None
            self.expiry_month = None
            self.expiry_year = None
            self.card_last4 = None
            self.paypal_email = None
            self.bank_name = None
            self.account_identifier = None

        elif self.method_type == 'paypal':
            if not self.paypal_email:
                raise ValidationError({'paypal_email': 'PayPal email is required.'})

            self.card_holder_name = None
            self.card_number = None
            self.expiry_month = None
            self.expiry_year = None
            self.card_last4 = None
            self.upi_id = None
            self.bank_name = None
            self.account_identifier = None

        elif self.method_type == 'net_banking':
            if not self.bank_name:
                raise ValidationError({'bank_name': 'Bank name is required for net banking.'})
            if not self.account_identifier:
                raise ValidationError({'account_identifier': 'Account identifier is required for net banking.'})

            self.card_holder_name = None
            self.card_number = None
            self.expiry_month = None
            self.expiry_year = None
            self.card_last4 = None
            self.upi_id = None
            self.paypal_email = None

        else:
            raise ValidationError({'method_type': 'Invalid payment method type.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        with transaction.atomic():
            if self.is_default:
                PaymentMethod.objects.filter(
                    user=self.user,
                    is_default=True
                ).exclude(pk=self.pk).update(is_default=False)
            super().save(*args, **kwargs)


class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    order_id = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='INR')

    payment_method = models.ForeignKey(
        PaymentMethod,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments_used'
    )

    gateway = models.CharField(max_length=50, default='Razorpay')
    transaction_id = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    gateway_response = models.JSONField(null=True, blank=True)

    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    refund_status = models.CharField(max_length=20, blank=True)
    refund_date = models.DateTimeField(null=True, blank=True)

    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment {self.order_id} ({self.status})"

    def clean(self):
        if self.amount is None or self.amount <= Decimal('0'):
            raise ValidationError({'amount': 'Payment amount must be greater than 0.'})

    def save(self, *args, **kwargs):
        if self.status == 'completed' and self.completed_at is None:
            self.completed_at = timezone.now()
        self.full_clean()
        super().save(*args, **kwargs)


class Invoice(models.Model):
    payment = models.OneToOneField(
        Payment,
        on_delete=models.CASCADE,
        related_name='invoice'
    )
    invoice_number = models.CharField(max_length=50, unique=True)

    bill_to_name = models.CharField(max_length=150)
    bill_to_email = models.EmailField()
    bill_to_address = models.TextField()

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    issued_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-issued_at']

    def __str__(self):
        return f"Invoice {self.invoice_number}"

    def clean(self):
        if self.total is None or self.total < Decimal('0'):
            raise ValidationError({'total': 'Total must be zero or greater.'})