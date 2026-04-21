from django.urls import path
from . import views
from MyAccount.views import toggle_wishlist_ajax
app_name = 'MyStore'

urlpatterns = [
  
    # ======================================================================
    # PRODUCTS & BROWSING
    # ======================================================================
    path('products/', views.product_list, name='product_list'),
    path('category/<slug:category_slug>/', views.product_list_by_category, name='product_by_category'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),

    # ======================================================================
    # SHOPPING CART
    # ======================================================================
    path('cart/', views.cart_view, name='cart'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove-from-cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('update-cart-quantity/', views.update_cart_quantity, name='update_cart_quantity'),

    # ======================================================================
    # CHECKOUT & ORDERS
    # ======================================================================
    path('checkout/', views.checkout, name='checkout'),
    path('order-success/<int:order_id>/', views.order_success, name='order_success'),

    # ======================================================================
    # INFORMATION PAGES
    # ======================================================================
    path('faq/', views.faq_list, name='faq'),
    path('return-policy/', views.return_policy, name='return_policy'),
    path('terms-of-service/', views.terms_of_service, name='terms_of_service'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),

    # ======================================================================
    # RETURNS & REFUNDS
    # ======================================================================
    path('request-return/', views.request_return, name='request_return'),
    path('return-status/<int:request_id>/', views.return_status, name='return_status'),
    path('my-returns/', views.my_returns, name='my_returns'),
    path("toggle-wishlist-ajax/", toggle_wishlist_ajax, name="toggle_wishlist_ajax"),
    path('returns/<int:request_id>/cancel/', views.cancel_return_request, name='cancel_return_request'),    
    path('chat/message/', views.chat_message, name='chat_message'),
]