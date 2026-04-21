from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import UserProfile, PasswordResetToken

@admin.register(UserProfile)
class UserProfileAdmin(ImportExportModelAdmin):
    list_display = ['user', 'phone_number', 'phone_verified', 'city', 'pincode', 'is_address_complete']
    list_filter = ['phone_verified', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone_number']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User Info', {
            'fields': ('user', 'phone_number', 'phone_verified')
        }),
        ('Address', {
            'fields': ('address_line1', 'city', 'state', 'pincode')
        }),
        ('Other', {
            'fields': ('profile_picture', 'date_of_birth', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def is_address_complete(self, obj):
        return obj.is_address_complete()
    is_address_complete.short_description = 'Address Ready?'

@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'token', 'created_at', 'is_used', 'is_expired']
    list_filter = ['is_used', 'created_at']
    readonly_fields = ['token', 'created_at']
    actions = ['mark_used', 'delete_expired']
    
    def is_expired(self, obj):
        return obj.is_expired()
    is_expired.boolean = True
    
    def mark_used(self, request, queryset):
        updated = queryset.update(is_used=True)
        self.message_user(request, f'{updated} token(s) marked as used.')
    mark_used.short_description = 'Mark selected as used'
    
    def delete_expired(self, request, queryset):
        expired = queryset.filter(created_at__lt=timezone.now() - timedelta(hours=24))
        count = expired.delete()[0]
        self.message_user(request, f'{count} expired token(s) deleted.')
    delete_expired.short_description = 'Delete expired tokens'