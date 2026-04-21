from django import forms
from django.forms import ModelForm

from .models import (
    Category,
    Product,
    CartItem,
    Order,
    Review,
    ReturnRequest,
    RefundRequest,
)


# ------------------------------------------------------
# Category Form
# ------------------------------------------------------
class CategoryForm(ModelForm):
    class Meta:
        model = Category
        fields = [
            'name',
            'description',
            'image',
            'is_active',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


# ------------------------------------------------------
# Product Form
# ------------------------------------------------------
class ProductForm(ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 'category', 'description',
            'price', 'original_price', 'stock',
            'image', 'image2', 'image3',
            'brand', 'sku',
            'is_active', 'is_featured',
            'meta_keywords', 'meta_description',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'meta_description': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_name(self):
        name = (self.cleaned_data.get("name") or "").strip()
        if Product.objects.filter(name=name).exclude(id=self.instance.id).exists():
            raise forms.ValidationError("A product with this name already exists.")
        return name

    def clean_sku(self):
        sku = (self.cleaned_data.get("sku") or "").strip()
        if sku:
            if Product.objects.filter(sku=sku).exclude(id=self.instance.id).exists():
                raise forms.ValidationError("SKU already exists. Must be unique.")
        return sku


# ------------------------------------------------------
# Cart Item Form
# ------------------------------------------------------
class CartItemForm(ModelForm):
    class Meta:
        model = CartItem
        fields = ['quantity']
        widgets = {
            'quantity': forms.NumberInput(attrs={'min': 1})
        }

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity is not None and quantity < 1:
            raise forms.ValidationError("Quantity must be at least 1.")
        return quantity


# ------------------------------------------------------
# Order / Checkout Form
# ------------------------------------------------------
class OrderForm(ModelForm):
    class Meta:
        model = Order
        fields = [
            'full_name', 'email', 'phone',
            'address', 'city', 'state', 'pincode',
            'payment_method', 'notes',
        ]
        widgets = {
            'address': forms.Textarea(attrs={'rows': 2}),
            'notes': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Optional'}),
        }

    def clean_phone(self):
        phone = (self.cleaned_data.get("phone") or "").strip()
        if not phone.isdigit():
            raise forms.ValidationError("Phone number must contain digits only.")
        if len(phone) < 10:
            raise forms.ValidationError("Phone number must be at least 10 digits.")
        return phone


# ------------------------------------------------------
# Review Form
# ------------------------------------------------------
class ReviewForm(ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'title', 'comment']
        widgets = {
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 5}),
            'comment': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        if rating is None or rating < 1 or rating > 5:
            raise forms.ValidationError("Rating must be between 1 and 5.")
        return rating


# ------------------------------------------------------
# Return Request Form
# ------------------------------------------------------
class ReturnRequestForm(forms.ModelForm):
    class Meta:
        model = ReturnRequest
        fields = ['order', 'product_name', 'reason', 'description']
        widgets = {
            'reason': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(
                attrs={
                    'rows': 4,
                    'placeholder': 'Provide details about the issue...'
                }
            ),
        }

    def clean_product_name(self):
        product_name = (self.cleaned_data.get('product_name') or '').strip()
        if not product_name:
            raise forms.ValidationError("Product name is required.")
        return product_name


# ------------------------------------------------------
# Refund Request Form
# ------------------------------------------------------
class RefundRequestForm(forms.ModelForm):
    class Meta:
        model = RefundRequest
        fields = ['reason']
        widgets = {
            'reason': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 5,
                    'placeholder': 'Please explain why you want a refund...'
                }
            ),
        }

    def clean_reason(self):
        reason = (self.cleaned_data.get('reason') or '').strip()
        if not reason:
            raise forms.ValidationError("Reason is required.")
        return reason