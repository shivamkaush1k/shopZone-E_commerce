from decimal import Decimal
import random

from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    @property
    def emoji(self):
        emoji_map = {
            'electronics': '📱',
            'fashion': '👗',
            'clothing': '👕',
            'books': '📚',
            'beauty': '💄',
            'sports': '⚽',
            'toys': '🧸',
            'furniture': '🛋️',
            'home & kitchen': '🏠',
            'automotive': '🚗',
            'garden': '🌱',
            'health': '💊',
            'pet supplies': '🐾',
            'office supplies': '📁',
            'accessories': '👜',
            'electronics accessories': '🔌',
            'gaming': '🎮',
            'electronics & gadgets': '📱',
            'health & wellness': '💊',
        }
        return emoji_map.get(self.name.strip().lower(), '🛒')

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Category.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    
# ======================================================================
# PRODUCT MODEL
# ======================================================================
class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    description = models.TextField()
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    original_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    stock = models.PositiveIntegerField(default=0)

    image = models.ImageField(upload_to='products/', blank=True, null=True)
    image2 = models.ImageField(upload_to='products/', blank=True, null=True)
    image3 = models.ImageField(upload_to='products/', blank=True, null=True)

    brand = models.CharField(max_length=100, blank=True)
    sku = models.CharField(max_length=50, unique=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)

    meta_keywords = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active']),
            models.Index(fields=['category']),
            models.Index(fields=['is_featured']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug

        if self.original_price is not None and self.original_price < self.price:
            self.original_price = self.price

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_discount_percentage(self):
        if self.original_price and self.original_price > self.price:
            discount = ((self.original_price - self.price) / self.original_price) * 100
            return round(discount)
        return 0

    def is_in_stock(self):
        return self.stock > 0


# ======================================================================
# CART MODEL
# ======================================================================
class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='shopping_cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_total_items(self):
        return self.items.aggregate(total=models.Sum('quantity'))['total'] or 0

    def get_total_price(self):
        return sum(item.get_total_price() for item in self.items.select_related('product').all())

    def __str__(self):
        return f"Cart({self.user.username})"


# ======================================================================
# CART ITEM MODEL
# ======================================================================
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-added_at']
        constraints = [
            models.UniqueConstraint(fields=['cart', 'product'], name='unique_cart_product')
        ]

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    def get_total_price(self):
        return self.product.price * self.quantity


# ======================================================================
# ORDER MODEL
# ======================================================================
class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    PAYMENT_CHOICES = [
        ('cod', 'Cash on Delivery'),
        ('online', 'Online Payment'),
        ('upi', 'UPI'),
        ('card', 'Credit/Debit Card'),
        ('netbanking', 'Net Banking'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='store_orders')
    order_number = models.CharField(max_length=50, unique=True, blank=True)

    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    shipping_charge = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('50.00'))
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='cod')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')

    payment_order_id = models.CharField(max_length=100, blank=True, null=True)
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    refund_id = models.CharField(max_length=100, blank=True, null=True)
    refund_reason = models.TextField(blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    tracking_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    admin_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(blank=True, null=True)
    shipped_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['status']),
        ]

    def save(self, *args, **kwargs):
        if not self.order_number:
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            random_num = random.randint(1000, 9999)
            self.order_number = f'ORD{timestamp}{random_num}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order {self.order_number} - {self.user.username}"

    def get_total_items(self):
        return sum(item.quantity for item in self.items.all())

    def update_status(self, new_status):
        self.status = new_status
        now = timezone.now()

        if new_status == 'confirmed' and not self.confirmed_at:
            self.confirmed_at = now
        elif new_status == 'shipped' and not self.shipped_at:
            self.shipped_at = now
        elif new_status == 'delivered' and not self.delivered_at:
            self.delivered_at = now

        self.save()


# ======================================================================
# ORDER ITEM MODEL
# ======================================================================
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='order_items')

    product_name = models.CharField(max_length=200)
    product_sku = models.CharField(max_length=50, blank=True)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    price = models.DecimalField(max_digits=10, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.quantity} x {self.product_name}"

    def get_total_price(self):
        return self.price * self.quantity

    def save(self, *args, **kwargs):
        if self.product:
            if not self.product_name:
                self.product_name = self.product.name
            if not self.product_sku:
                self.product_sku = self.product.sku
            if not self.price:
                self.price = self.product.price
        super().save(*args, **kwargs)


# ======================================================================
# WISHLIST MODEL
# ======================================================================
class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='store_wishlist_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlisted_by')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-added_at']
        constraints = [
            models.UniqueConstraint(fields=['user', 'product'], name='unique_wishlist_item')
        ]

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"


# ======================================================================
# REVIEW MODEL
# ======================================================================
class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='product_reviews')
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(max_length=200, blank=True)
    comment = models.TextField()
    is_verified_purchase = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['product', 'user'], name='unique_product_review')
        ]

    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.rating}★)"


# ======================================================================
# FAQ MODEL
# ======================================================================
class FAQ(models.Model):
    CATEGORY_CHOICES = [
        ('general', 'General'),
        ('shipping', 'Shipping'),
        ('returns', 'Returns & Refunds'),
        ('payment', 'Payment'),
        ('account', 'Account'),
        ('products', 'Products'),
    ]

    question = models.CharField(max_length=500)
    answer = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='general')
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'order']
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'

    def __str__(self):
        return f"{self.get_category_display()} - {self.question[:50]}"


# ======================================================================
# RETURN POLICY MODEL
# ======================================================================
class ReturnPolicy(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    return_window_days = models.PositiveIntegerField(default=30)
    refund_percentage = models.PositiveIntegerField(default=100)
    conditions = models.TextField(help_text="Conditions for returns")
    process_steps = models.TextField(help_text="Step-by-step return process")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Return Policy'
        verbose_name_plural = 'Return Policies'

    def __str__(self):
        return self.title


# ======================================================================
# TERMS OF SERVICE MODEL
# ======================================================================
class TermsOfService(models.Model):
    title = models.CharField(max_length=200, default='Terms of Service')
    content = models.TextField()
    version = models.CharField(max_length=10, default='1.0')
    effective_date = models.DateField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Terms of Service'
        verbose_name_plural = 'Terms of Services'
        ordering = ['-effective_date']

    def __str__(self):
        return f"{self.title} v{self.version}"


# ======================================================================
# USER TOS AGREEMENT MODEL
# ======================================================================
class UserTOSAgreement(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='tos_agreement')
    tos = models.ForeignKey(TermsOfService, on_delete=models.SET_NULL, null=True, related_name='user_agreements')
    agreed_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        verbose_name = 'User TOS Agreement'
        verbose_name_plural = 'User TOS Agreements'

    def __str__(self):
        version = self.tos.version if self.tos else "N/A"
        return f"{self.user.username} - TOS v{version}"


# ======================================================================
# RETURN REQUEST MODEL
# ======================================================================
class ReturnRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('shipped_back', 'Shipped Back'),
        ('received', 'Received'),
        ('refunded', 'Refunded'),
    ]

    REASON_CHOICES = [
        ('defective', 'Defective/Damaged'),
        ('wrong_item', 'Wrong Item Received'),
        ('not_as_described', 'Not As Described'),
        ('changed_mind', 'Changed Mind'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='return_requests')
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='return_requests')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='return_requests')
    product_name = models.CharField(max_length=255)
    reason = models.CharField(max_length=100, choices=REASON_CHOICES)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolution_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-requested_at']

    def __str__(self):
        return f"Return Request #{self.id} - Order {self.order.order_number} - {self.user.username}"


# ======================================================================
# REFUND REQUEST MODEL
# ======================================================================
class RefundRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='refund_requests')
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='refund_requests')
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Refund Request for Order {self.order.order_number} by {self.user.username}"