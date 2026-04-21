from django.contrib import admin
from django.utils.text import slugify
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ForeignKeyWidget
import uuid

from .models import (
    Product, Category, Cart, CartItem, Order, OrderItem,
    Wishlist, Review, FAQ, ReturnPolicy, TermsOfService,
    UserTOSAgreement, ReturnRequest
)
from .resources import CategoryResource


class ProductResource(resources.ModelResource):
    category = fields.Field(
        column_name='category__name',
        attribute='category',
        widget=ForeignKeyWidget(Category, 'name')
    )

    class Meta:
        model = Product
        fields = (
            'id',
            'name',
            'slug',
            'category',
            'description',
            'price',
            'original_price',
            'stock',
            'brand',
            'sku',
            'is_active',
            'is_featured',
        )
        export_order = (
            'id',
            'name',
            'slug',
            'category',
            'description',
            'price',
            'original_price',
            'stock',
            'brand',
            'sku',
            'is_active',
            'is_featured',
        )
        import_id_fields = ['sku']
        skip_unchanged = True
        report_skipped = True

    def before_import_row(self, row, **kwargs):
        if not row.get('sku') or str(row['sku']).strip() == '':
            base_sku = slugify(row.get('name', '')).upper().replace('-', '')[:20]
            row['sku'] = f"{base_sku}-{uuid.uuid4().hex[:6].upper()}"

        if row.get('catego') and not row.get('category__name'):
            row['category__name'] = row.get('catego')

        if not row.get('slug') or str(row['slug']).strip() == '':
            row['slug'] = slugify(row.get('name', ''))

        return row


@admin.register(Category)
class CategoryAdmin(ImportExportModelAdmin):
    resource_class = CategoryResource
    list_display = ('name', 'slug', 'is_active', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')


@admin.register(Product)
class ProductAdmin(ImportExportModelAdmin):
    resource_class = ProductResource
    list_display = (
        'name', 'category', 'price', 'stock', 'sku',
        'is_active', 'is_featured', 'created_at'
    )
    list_filter = ('category', 'is_active', 'is_featured', 'created_at')
    search_fields = ('name', 'description', 'sku', 'brand')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('price', 'stock', 'is_active', 'is_featured')


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'updated_at')
    search_fields = ('user__username',)


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'product', 'quantity', 'added_at')
    list_filter = ('added_at',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'status', 'total_amount', 'created_at')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('order_number', 'user__username', 'email', 'phone')
    readonly_fields = ('order_number', 'created_at', 'updated_at')
    ordering = ('-created_at',)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product_name', 'quantity', 'price')
    search_fields = ('product_name',)


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'added_at')
    list_filter = ('added_at',)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'rating', 'is_verified_purchase', 'created_at')
    list_filter = ('rating', 'is_verified_purchase', 'created_at')
    search_fields = ('user__username', 'product__name', 'title', 'comment')


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('category', 'question', 'is_active', 'order')
    list_filter = ('category', 'is_active')
    search_fields = ('question', 'answer')
    ordering = ('category', 'order')
    fieldsets = (
        ('Question & Answer', {
            'fields': ('question', 'answer', 'category')
        }),
        ('Settings', {
            'fields': ('order', 'is_active')
        }),
    )


@admin.register(ReturnPolicy)
class ReturnPolicyAdmin(admin.ModelAdmin):
    list_display = ('title', 'return_window_days', 'refund_percentage', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Policy Details', {
            'fields': ('title', 'description')
        }),
        ('Return Settings', {
            'fields': ('return_window_days', 'refund_percentage')
        }),
        ('Instructions', {
            'fields': ('conditions', 'process_steps'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


@admin.register(TermsOfService)
class TermsOfServiceAdmin(admin.ModelAdmin):
    list_display = ('title', 'version', 'effective_date', 'is_active')
    list_filter = ('is_active', 'effective_date')
    search_fields = ('title', 'content')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Document Info', {
            'fields': ('title', 'version', 'effective_date')
        }),
        ('Content', {
            'fields': ('content',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(UserTOSAgreement)
class UserTOSAgreementAdmin(admin.ModelAdmin):
    list_display = ('user', 'tos', 'agreed_at')
    list_filter = ('tos', 'agreed_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('agreed_at', 'user', 'tos', 'ip_address')

    def has_add_permission(self, request):
        return False


@admin.register(ReturnRequest)
class ReturnRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'product_name', 'status', 'requested_at')
    list_filter = ('status', 'reason', 'requested_at')
    search_fields = ('user__username', 'product_name', 'description')
    readonly_fields = ('requested_at', 'updated_at', 'user')

    fieldsets = (
        ('User & Order', {
            'fields': ('user', 'order')
        }),
        ('Product & Return Info', {
            'fields': ('product_name', 'reason', 'description')
        }),
        ('Processing', {
            'fields': ('status', 'refund_amount')
        }),
        ('Timeline', {
            'fields': ('requested_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['approve_return', 'reject_return', 'refund_return']

    def approve_return(self, request, queryset):
        updated = queryset.update(status='approved')
        self.message_user(request, f'{updated} returns approved.')
    approve_return.short_description = 'Mark selected as Approved'

    def reject_return(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} returns rejected.')
    reject_return.short_description = 'Mark selected as Rejected'

    def refund_return(self, request, queryset):
        updated = queryset.update(status='refunded')
        self.message_user(request, f'{updated} returns refunded.')
    refund_return.short_description = 'Mark selected as Refunded'