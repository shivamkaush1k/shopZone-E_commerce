from .models import UserProfile, Address, ContactMessage, NotificationSettings, OrderTrackingNote

from django.contrib import admin
from .models import (
    UserProfile,
    Address,
    ContactMessage,
    NotificationSettings,
    OrderTrackingNote,
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "phone_number",
        "gender",
        "profile_visibility",
        "newsletter_subscription",
        "email_notifications",
        "sms_notifications",
        "created_at",
    )
    list_filter = (
        "gender",
        "profile_visibility",
        "newsletter_subscription",
        "email_notifications",
        "sms_notifications",
        "created_at",
    )
    search_fields = ("user__username", "user__email", "phone_number")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "full_name",
        "phone_number",
        "city",
        "state",
        "postal_code",
        "country",
        "address_type",
        "is_default",
        "created_at",
    )
    list_filter = (
        "address_type",
        "is_default",
        "country",
        "state",
        "created_at",
    )
    search_fields = (
        "user__username",
        "full_name",
        "phone_number",
        "city",
        "state",
        "postal_code",
    )
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "email",
        "subject",
        "phone",
        "is_resolved",
        "created_at",
    )
    list_filter = ("is_resolved", "created_at")
    search_fields = ("name", "email", "subject", "phone")
    list_editable = ("is_resolved",)
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)


# MyAccount/admin.py

@admin.register(NotificationSettings)
class NotificationSettingsAdmin(admin.ModelAdmin):
    list_display = ['user', 'order_updates', 'promotional_emails', 'newsletter', 'sms_notifications', 'app_notifications']
    list_filter = ['order_updates', 'promotional_emails', 'sms_notifications', 'app_notifications']
    readonly_fields = ['created_at', 'updated_at']
    search_fields = ['user__username', 'user__email']

@admin.register(OrderTrackingNote)
class OrderTrackingNoteAdmin(admin.ModelAdmin):
    list_display = ("user", "order_id", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__username", "order_id", "note")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)