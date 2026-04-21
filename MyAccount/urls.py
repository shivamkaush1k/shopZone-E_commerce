from django.urls import path
from . import views

app_name = 'MyAccount'

urlpatterns = [
    # ======================================================================
    # HOME & DASHBOARD
    # ======================================================================
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('contact/', views.contact, name='contact'),

    # ======================================================================
    # PROFILE MANAGEMENT
    # ======================================================================
    path('profile/', views.profile_view, name='profile'),
    path('edit-profile/', views.edit_profile_view, name='edit_profile'),
    path('change-password/', views.change_password_view, name='change_password'),
    path('delete-account/', views.delete_account_view, name='delete_account'),

    # ======================================================================
    # ORDERS
    # ======================================================================
    path('orders/', views.order_list, name='orders'),
    path('order/<int:order_id>/', views.order_detail_view, name='order_detail'),
    path('order/<int:order_id>/cancel/', views.cancel_order_view, name='cancel_order'),

    # ======================================================================
    # WISHLIST
    # ======================================================================
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('add-to-wishlist/<int:product_id>/', views.add_to_wishlist_view, name='add_to_wishlist'),
    path('toggle-wishlist/', views.toggle_wishlist_ajax, name='toggle_wishlist_ajax'),

    # ======================================================================
    # ADDRESS MANAGEMENT
    # ======================================================================
    path('addresses/', views.addresses_view, name='addresses'),
    path('add-address/', views.add_address_view, name='add_address'),
    path('edit-address/<int:address_id>/', views.edit_address_view, name='edit_address'),
    path('delete-address/<int:address_id>/', views.delete_address_view, name='delete_address'),
    path('set-default-address/<int:address_id>/', views.set_default_address_view, name='set_default_address'),

    # ======================================================================
    # PAYMENT METHODS
    # ======================================================================
    path('payment-methods/', views.payment_methods_view, name='payment_methods'),
    path('add-payment-method/', views.add_payment_method_view, name='add_payment_method'),
    path('edit-payment-method/<int:payment_id>/', views.edit_payment_method_view, name='edit_payment_method'),
    path('delete-payment-method/<int:payment_id>/', views.delete_payment_method_view, name='delete_payment_method'),

    # ======================================================================
    # REVIEWS & SETTINGS
    # ======================================================================
    path('my-reviews/', views.my_reviews_view, name='my_reviews'),
    path('settings/', views.account_settings_view, name='settings'),
    path('notification-settings/', views.notification_settings_view, name='notification_settings'),
]