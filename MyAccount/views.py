import json
import logging
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import get_user_model, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.dispatch import receiver
from django.db.models.signals import post_save

from .models import (
    Address,
    ContactMessage,
    NotificationSettings,
    OrderTrackingNote,
    UserProfile,
)
from .forms import (
    AddressForm,
    NotificationSettingsForm,
    UserProfileForm,
)
from MyStore.models import (
    Cart,
    CartItem,
    Category,
    FAQ,
    Order,
    OrderItem,
    Product,
    ReturnPolicy,
    ReturnRequest,
    Review,
    TermsOfService,
    Wishlist,
)
from PaymentMethod.models import PaymentMethod
from .utils import send_sms  # Your SMS utility

logger = logging.getLogger(__name__)
User = get_user_model()
PRODUCTS_PER_PAGE = 12

# ======================================================================
# HELPERS
# ======================================================================

def get_user_order_queryset(user):
    return Order.objects.filter(user=user)

def get_account_summary(user):
    user_orders = get_user_order_queryset(user)
    return {
        "total_orders": user_orders.count(),
        "pending_orders": user_orders.filter(status="pending").count(),
        "wishlist_count": Wishlist.objects.filter(user=user).count(),
    }

def _get_product_base_queryset():
    return Product.objects.filter(is_active=True).select_related("category")

def _get_all_categories():
    return Category.objects.all().order_by("name")

def _apply_product_filters(queryset, current_category="", search_query=""):
    if current_category:
        queryset = queryset.filter(category__slug=current_category)
    if search_query:
        queryset = queryset.filter(
            Q(name__icontains=search_query)
            | Q(brand__icontains=search_query)
            | Q(category__name__icontains=search_query)
        )
    return queryset

def _apply_product_sorting(queryset, current_sort=""):
    current_sort = (current_sort or "").strip().lower()
    sort_map = {
        "price_low": "price",
        "price_high": "-price",
        "newest": "-created_at",
    }
    return queryset.order_by(sort_map.get(current_sort, "-id")), current_sort

def _paginate_queryset(request, queryset, per_page=PRODUCTS_PER_PAGE):
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get("page")
    return paginator.get_page(page_number)

def _get_checkout_prefill_data(user):
    user_profile = getattr(user, "userprofile", None)
    default_address = Address.objects.filter(user=user, is_default=True).first()

    user_full_name = user.get_full_name() or user.username or ""
    user_email = user.email or ""
    user_phone = ""
    user_address = ""

    if user_profile and hasattr(user_profile, "phone_number"):
        user_phone = user_profile.phone_number or ""

    if default_address:
        address_parts = []
        for field in [
            "address_line_1",
            "address_line_2",
            "city",
            "state",
            "postal_code",
            "country",
        ]:
            if hasattr(default_address, field):
                value = getattr(default_address, field)
                if value:
                    address_parts.append(str(value))
        user_address = ", ".join(address_parts)

    return {
        "user_full_name": user_full_name,
        "user_email": user_email,
        "user_phone": user_phone,
        "user_address": user_address,
    }

def _build_product_list_context(products, categories, current_category="", current_sort="", search_query=""):
    return {
        "products": products,
        "categories": categories,
        "current_category": current_category,
        "current_sort": current_sort,
        "search_query": search_query,
    }

def _send_order_notification(order, event_type):
    """Send SMS notification based on order event"""
    try:
        user = order.user
        phone = order.phone
        
        if not phone:
            logger.warning(f"No phone number for order {order.order_number}")
            return
            
        notification_settings = getattr(user, 'notification_settings', None)
        if not notification_settings or not notification_settings.sms_notifications:
            logger.info(f"SMS disabled for user {user.id}")
            return
            
        messages_map = {
            'order_placed': f"✅ Shopzone Order #{order.order_number} placed! Total: ₹{order.total_amount:.2f}. Track: shopzone.com/orders",
            'confirmed': f"📦 Order #{order.order_number} confirmed! Preparing to ship soon.",
            'shipped': f"🚚 Order #{order.order_number} shipped! Track your package soon.",
            'delivered': f"🎉 Order #{order.order_number} delivered! Thank you for shopping with Shopzone.",
            'cancelled': f"❌ Order #{order.order_number} cancelled.",
            'return_confirmed': f"🔄 Return request #{order.order_number[:8]} confirmed. Refund processing soon.",
        }
        
        message = messages_map.get(event_type, f"Order #{order.order_number} updated: {order.status}")
        success = send_sms(phone, message)
        if success:
            logger.info(f"SMS sent for {event_type}: {order.order_number}")
        else:
            logger.error(f"SMS failed for {event_type}: {order.order_number}")
            
    except Exception as e:
        logger.error(f"Error sending SMS notification: {e}")

# ======================================================================
# HOME & PRODUCT BROWSING
# ======================================================================

def product_list(request):
    current_category = request.GET.get("category", "").strip()
    current_sort = request.GET.get("sort", "").strip().lower()
    search_query = request.GET.get("q", "").strip()

    products = _get_product_base_queryset()
    products = _apply_product_filters(products, current_category=current_category, search_query=search_query)
    products, current_sort = _apply_product_sorting(products, current_sort)

    page_obj = _paginate_queryset(request, products)
    categories = _get_all_categories()

    context = _build_product_list_context(
        products=page_obj,
        categories=categories,
        current_category=current_category,
        current_sort=current_sort,
        search_query=search_query,
    )
    return render(request, "productlist.html", context)

def product_list_by_category(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug)
    current_sort = request.GET.get("sort", "").strip().lower()
    search_query = request.GET.get("q", "").strip()

    products = _get_product_base_queryset().filter(category=category)
    products = _apply_product_filters(products, search_query=search_query)
    products, current_sort = _apply_product_sorting(products, current_sort)

    page_obj = _paginate_queryset(request, products)
    categories = _get_all_categories()

    context = _build_product_list_context(
        products=page_obj,
        categories=categories,
        current_category=category.slug,
        current_sort=current_sort,
        search_query=search_query,
    )
    context["selected_category"] = category
    return render(request, "productlist.html", context)

def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related("category"),
        slug=slug,
        is_active=True,
    )

    reviews = product.reviews.all().order_by("-created_at")[:5]
    is_in_wishlist = False

    if request.user.is_authenticated:
        is_in_wishlist = Wishlist.objects.filter(
            user=request.user,
            product=product,
        ).exists()

    savings = 0
    if product.original_price and product.original_price > product.price:
        savings = product.original_price - product.price

    context = {
        "product": product,
        "reviews": reviews,
        "is_in_wishlist": is_in_wishlist,
        "savings": savings,
    }
    return render(request, "product_detail.html", context)

@login_required
def home(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    user_orders = get_user_order_queryset(request.user)
    summary = get_account_summary(request.user)
    categories = Category.objects.annotate(product_count=Count("products"))
    products = Product.objects.filter(is_active=True).select_related("category")[:8]

    context = {
        "recent_orders": user_orders.order_by("-created_at")[:5],
        "profile": profile,
        "categories": categories,
        "products": products,
        **summary,
    }
    return render(request, "homePage.html", context)

@login_required
def dashboard_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    user_orders = get_user_order_queryset(request.user)
    summary = get_account_summary(request.user)

    context = {
        "recent_orders": user_orders.order_by("-created_at")[:5],
        "profile": profile,
        **summary,
    }
    return render(request, "dashboard.html", context)

# ======================================================================
# CART MANAGEMENT
# ======================================================================

@login_required
@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)

    try:
        quantity = int(request.POST.get("quantity", 1))
    except (TypeError, ValueError):
        quantity = 1

    quantity = max(quantity, 1)

    if product.stock is not None and product.stock <= 0:
        messages.error(request, f'"{product.name}" is out of stock.')
        next_url = request.POST.get("next") or request.META.get("HTTP_REFERER")
        return redirect(next_url or "MyStore:product_list")

    if product.stock is not None:
        quantity = min(quantity, product.stock)

    cart, _ = Cart.objects.get_or_create(user=request.user)

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={"quantity": quantity},
    )

    if not created:
        new_quantity = cart_item.quantity + quantity
        if product.stock is not None:
            new_quantity = min(new_quantity, product.stock)
        cart_item.quantity = new_quantity
        cart_item.save(update_fields=["quantity"])

    messages.success(request, f'"{product.name}" added to your cart.')

    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER")
    return redirect(next_url or "MyStore:cart")

@login_required
def cart_view(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.items.select_related("product").all()

    context = {
        "cart": cart,
        "cart_items": cart_items,
        "total_items": cart.get_total_items(),
        "total_price": cart.get_total_price(),
    }
    return render(request, "cart.html", context)

@login_required
@require_POST
def update_cart_quantity(request):
    try:
        data = json.loads(request.body or "{}")
        item_id = data.get("item_id")
        new_quantity = int(data.get("quantity", 1))

        if new_quantity < 1:
            return JsonResponse(
                {"success": False, "error": "Quantity must be at least 1"},
                status=400,
            )

        cart_item = get_object_or_404(
            CartItem.objects.select_related("cart", "product"),
            id=item_id,
            cart__user=request.user,
        )

        if cart_item.product.stock is not None and new_quantity > cart_item.product.stock:
            return JsonResponse(
                {
                    "success": False,
                    "error": f"Only {cart_item.product.stock} item(s) available in stock",
                },
                status=400,
            )

        cart_item.quantity = new_quantity
        cart_item.save(update_fields=["quantity"])
        cart = cart_item.cart

        return JsonResponse(
            {
                "success": True,
                "item_total": str(cart_item.get_total_price()),
                "cart_total": str(cart.get_total_price()),
                "total_items": cart.get_total_items(),
                "quantity": cart_item.quantity,
            }
        )

    except (json.JSONDecodeError, TypeError, ValueError):
        return JsonResponse(
            {"success": False, "error": "Invalid quantity or payload"},
            status=400,
        )
    except Exception:
        logger.exception("Error updating cart quantity")
        return JsonResponse(
            {"success": False, "error": "Something went wrong"},
            status=500,
        )

@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(
        CartItem,
        id=item_id,
        cart__user=request.user,
    )
    cart_item.delete()
    messages.success(request, "Item removed from cart.")
    return redirect("MyStore:cart")

# ======================================================================
# CHECKOUT & ORDERS
# ======================================================================

@login_required
def checkout(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.items.select_related("product").all()

    if not cart_items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect("MyStore:cart")

    total_price = sum(item.get_total_price() for item in cart_items)
    prefill_data = _get_checkout_prefill_data(request.user)

    base_context = {
        "cart_items": cart_items,
        "total_price": total_price,
        **prefill_data,
    }

    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        address = request.POST.get("address", "").strip()
        phone = request.POST.get("phone", "").strip()
        payment_method = request.POST.get("payment_method", "").strip().lower()

        if not all([full_name, address, phone, payment_method]):
            messages.error(request, "All checkout fields are required.")
            return render(request, "checkout.html", base_context)

        if payment_method not in {"cod", "online"}:
            messages.error(request, "Invalid payment method selected.")
            return render(request, "checkout.html", base_context)

        try:
            with transaction.atomic():
                locked_items = (
                    CartItem.objects
                    .select_related("product", "cart")
                    .select_for_update()
                    .filter(cart=cart)
                )

                if not locked_items.exists():
                    messages.error(request, "Your cart is empty.")
                    return redirect("MyStore:cart")

                recalculated_total = 0

                for item in locked_items:
                    product = item.product
                    if product.stock is not None and item.quantity > product.stock:
                        messages.error(request, f'Not enough stock for "{product.name}".')
                        return render(request, "checkout.html", base_context)
                    recalculated_total += item.get_total_price()

                order = Order.objects.create(
                    user=request.user,
                    full_name=full_name,
                    email=request.user.email,
                    address=address,
                    phone=phone,
                    payment_method=payment_method,
                    total_amount=recalculated_total,
                    status="pending" if payment_method == "online" else "confirmed",
                )

                order_items = []
                for item in locked_items:
                    product = item.product
                    order_items.append(
                        OrderItem(
                            order=order,
                            product=product,
                            quantity=item.quantity,
                            price=product.price,
                            product_name=product.name,
                        )
                    )

                    if product.stock is not None:
                        product.stock -= item.quantity
                        product.save(update_fields=["stock"])

                OrderItem.objects.bulk_create(order_items)
                locked_items.delete()

            # Send SMS notification for order placed
            _send_order_notification(order, 'order_placed')

        except Exception:
            logger.exception("Error during checkout")
            messages.error(request, "Unable to place your order right now. Please try again.")
            return render(request, "checkout.html", base_context)

        if payment_method == "cod":
            messages.success(
                request,
                f"Order #{order.order_number} placed successfully! (Cash on Delivery)",
            )
            return redirect("MyStore:order_success", order_id=order.id)

        messages.info(request, "Redirecting to secure payment...")
        return redirect("PaymentMethod:initiate_payment", order_id=order.id)

    return render(request, "checkout.html", base_context)

@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, "order_success.html", {"order": order})

@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user).order_by("-created_at")

    status = request.GET.get("status", "").strip()
    if status:
        orders = orders.filter(status=status)

    search = request.GET.get("search", "").strip()
    if search:
        orders = orders.filter(order_number__icontains=search)

    paginator = Paginator(orders, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    status_choices = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    ]

    context = {
        "page_obj": page_obj,
        "orders": page_obj.object_list,
        "status_choices": status_choices,
        "current_status": status,
        "search_query": search,
        "total_orders": Order.objects.filter(user=request.user).count(),
    }
    return render(request, "orders.html", context)

@login_required
def order_detail_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    tracking_notes = OrderTrackingNote.objects.filter(order_id=order.id).order_by("-created_at")

    return render(request, "order_detail.html", {
        "order": order,
        "tracking_notes": tracking_notes,
    })

@login_required
@require_POST
def cancel_order_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.status in ["pending", "confirmed"]:
        old_status = order.status
        order.status = "cancelled"
        order.save(update_fields=["status"])
        messages.success(request, f"Order {order.order_number} cancelled.")
        
        # Send SMS for cancellation
        _send_order_notification(order, 'cancelled')
    else:
        messages.error(request, "Order cannot be cancelled now.")

    return redirect("MyAccount:order_detail", order_id=order_id)

# ======================================================================
# PROFILE
# ======================================================================

@login_required
def profile_view(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    user_orders = get_user_order_queryset(request.user)
    summary = get_account_summary(request.user)
    
    context = {
        'cart_items': CartItem.objects.filter(cart=cart).count(),
        'wishlist_items': Wishlist.objects.filter(user=request.user).select_related('product')[:4],
        'addresses': Address.objects.filter(user=request.user).order_by('-is_default', '-id'),
        'recent_orders': user_orders.order_by('-created_at')[:5],
        'orders': user_orders.order_by('-created_at'),  # ← ADD THIS ONE LINE
        **summary,
    }
    return render(request, "profile.html", context)

@login_required
def edit_profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect("MyAccount:profile")
        messages.error(request, "Please correct the errors below.")
    else:
        form = UserProfileForm(instance=profile)

    return render(request, "edit_profile.html", {"form": form})

@login_required
def change_password_view(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Password updated successfully!")
            return redirect("MyAccount:profile")
        messages.error(request, "Please correct the errors below.")
    else:
        form = PasswordChangeForm(request.user)

    return render(request, "change_password.html", {"form": form})

@login_required
def delete_account_view(request):
    if request.method == "POST":
        password = request.POST.get("password", "")

        if request.user.check_password(password):
            user = request.user
            logout(request)
            user.delete()
            messages.success(request, "Account deleted.")
            return redirect("login:login")

        messages.error(request, "Incorrect password.")

    return render(request, "delete_account.html")

# ======================================================================
# ADDRESSES (continued)
# ======================================================================

@login_required
def addresses_view(request):
    addresses = Address.objects.filter(user=request.user).order_by("-is_default", "-id")
    return render(request, "addresses.html", {"addresses": addresses})

@login_required
def add_address_view(request):
    if request.method == "POST":
        form = AddressForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                address = form.save(commit=False)
                address.user = request.user

                if not Address.objects.filter(user=request.user).exists():
                    address.is_default = True
                elif address.is_default:
                    Address.objects.filter(
                        user=request.user,
                        is_default=True
                    ).update(is_default=False)

                address.save()

            messages.success(request, "Address added successfully!")
            return redirect("MyAccount:addresses")

        messages.error(request, "Please correct the errors below.")
    else:
        form = AddressForm()

    return render(request, "add_addresses.html", {"form": form})

@login_required
def edit_address_view(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)

    if request.method == "POST":
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            with transaction.atomic():
                updated_address = form.save(commit=False)

                if updated_address.is_default:
                    Address.objects.filter(
                        user=request.user,
                        is_default=True
                    ).exclude(id=updated_address.id).update(is_default=False)

                updated_address.save()

            messages.success(request, "Address updated successfully!")
            return redirect("MyAccount:addresses")

        messages.error(request, "Please correct the errors below.")
    else:
        form = AddressForm(instance=address)

    return render(request, "edit_addresses.html", {
        "form": form,
        "address": address,
    })

@login_required
@require_POST
def delete_address_view(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    was_default = address.is_default
    address.delete()

    if was_default:
        next_address = Address.objects.filter(user=request.user).order_by("-id").first()
        if next_address:
            next_address.is_default = True
            next_address.save(update_fields=["is_default"])

    messages.success(request, "Address deleted successfully!")
    return redirect("MyAccount:addresses")

@login_required
@require_POST
def set_default_address_view(request, address_id):
    with transaction.atomic():
        Address.objects.filter(user=request.user).update(is_default=False)
        address = get_object_or_404(Address, id=address_id, user=request.user)
        address.is_default = True
        address.save(update_fields=["is_default"])

    messages.success(request, "Default address updated successfully!")
    return redirect("MyAccount:addresses")

# ======================================================================
# PAYMENT METHODS
# ======================================================================

@login_required
def payment_methods_view(request):
    payment_methods = PaymentMethod.objects.filter(user=request.user).order_by("-is_default", "-id")
    return render(request, "payment_methods.html", {"payment_methods": payment_methods})

@login_required
def add_payment_method_view(request):
    from PaymentMethod.forms import PaymentMethodForm

    if request.method == "POST":
        form = PaymentMethodForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                obj = form.save(commit=False)
                obj.user = request.user

                if obj.is_default:
                    PaymentMethod.objects.filter(
                        user=request.user,
                        is_default=True,
                    ).update(is_default=False)

                obj.save()

            messages.success(request, "Payment method added!")
            return redirect("MyAccount:payment_methods")
        messages.error(request, "Please correct the errors below.")
    else:
        form = PaymentMethodForm()

    return render(request, "add_payment_method.html", {"form": form})

@login_required
def edit_payment_method_view(request, payment_id):
    from PaymentMethod.forms import PaymentMethodForm

    payment = get_object_or_404(PaymentMethod, id=payment_id, user=request.user)

    if request.method == "POST":
        form = PaymentMethodForm(request.POST, instance=payment)
        if form.is_valid():
            with transaction.atomic():
                updated_payment = form.save(commit=False)

                if updated_payment.is_default:
                    PaymentMethod.objects.filter(
                        user=request.user,
                        is_default=True,
                    ).exclude(id=updated_payment.id).update(is_default=False)

                updated_payment.save()

            messages.success(request, "Payment method updated!")
            return redirect("MyAccount:payment_methods")
        messages.error(request, "Please correct the errors below.")
    else:
        form = PaymentMethodForm(instance=payment)

    return render(request, "edit_payment_method.html", {"form": form})

@login_required
@require_POST
def delete_payment_method_view(request, payment_id):
    payment = get_object_or_404(PaymentMethod, id=payment_id, user=request.user)
    payment.delete()
    messages.success(request, "Payment method deleted!")
    return redirect("MyAccount:payment_methods")

# ======================================================================
# WISHLIST
# ======================================================================

@login_required
def wishlist_view(request):
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related("product")

    if request.method == "POST" and "remove_product_id" in request.POST:
        product_id = request.POST.get("remove_product_id", "").strip()

        if not product_id:
            messages.error(request, "Invalid product ID.")
            return redirect("MyAccount:wishlist")

        try:
            product_id = int(product_id)
        except (ValueError, TypeError):
            messages.error(request, "Invalid product ID format.")
            return redirect("MyAccount:wishlist")

        wishlist_item = Wishlist.objects.filter(
            user=request.user,
            product_id=product_id
        ).first()

        if wishlist_item:
            wishlist_item.delete()
            messages.success(request, "Item removed from wishlist successfully!")
        else:
            messages.error(request, "Item not found in wishlist.")

        return redirect("MyAccount:wishlist")

    return render(request, "wishlist.html", {"wishlist_items": wishlist_items})

@login_required
def add_to_wishlist_view(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)

    wishlist_item, created = Wishlist.objects.get_or_create(
        user=request.user,
        product=product,
    )

    if created:
        messages.success(request, f'"{product.name}" added to wishlist.')
    else:
        messages.info(request, f'"{product.name}" is already in your wishlist.')

    next_url = request.GET.get("next")
    if next_url:
        return redirect(next_url)

    return redirect("MyAccount:wishlist")

@login_required
@require_POST
def toggle_wishlist_ajax(request):
    try:
        raw_product_id = None

        if request.content_type and "application/json" in request.content_type:
            data = json.loads(request.body or "{}")
            raw_product_id = data.get("product_id")
        else:
            raw_product_id = request.POST.get("product_id")

        if not raw_product_id:
            return JsonResponse(
                {"status": "error", "message": "Product ID is required"},
                status=400,
            )

        product_id = int(str(raw_product_id).strip())
        product = get_object_or_404(Product, id=product_id, is_active=True)

        item = Wishlist.objects.filter(
            user=request.user,
            product=product,
        ).first()

        if item:
            item.delete()
            return JsonResponse({
                "status": "removed",
                "message": "Removed from wishlist",
                "is_in_wishlist": False,
                "product_id": product.id,
            })

        Wishlist.objects.create(user=request.user, product=product)
        return JsonResponse({
            "status": "added",
            "message": "Added to wishlist",
            "is_in_wishlist": True,
            "product_id": product.id,
        })

    except json.JSONDecodeError:
        return JsonResponse(
            {"status": "error", "message": "Invalid JSON payload"},
            status=400,
        )
    except (ValueError, TypeError):
        return JsonResponse(
            {"status": "error", "message": "Invalid product ID format"},
            status=400,
        )
    except Exception:
        logger.exception("Error toggling wishlist")
        return JsonResponse(
            {"status": "error", "message": "Something went wrong"},
            status=500,
        )

# ======================================================================
# REVIEWS & SETTINGS
# ======================================================================

@login_required
def my_reviews_view(request):
    reviews = Review.objects.filter(user=request.user).order_by("-created_at")
    paginator = Paginator(reviews, 10)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "my_reviews.html", {"reviews": page_obj})

@login_required
def account_settings_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    notification_settings, _ = NotificationSettings.objects.get_or_create(user=request.user)

    return render(request, "settings.html", {
        "profile": profile,
        "notification_settings": notification_settings,
    })

@login_required
def notification_settings_view(request):
    settings_obj, _ = NotificationSettings.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = NotificationSettingsForm(request.POST, instance=settings_obj)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.save()
            messages.success(request, "Notification settings updated successfully!")
            return redirect("MyAccount:notification_settings")
        messages.error(request, "Please correct the errors below.")
    else:
        form = NotificationSettingsForm(instance=settings_obj)

    return render(request, "notification_settings.html", {"form": form})

# ======================================================================
# CONTACT
# ======================================================================

@login_required
def contact(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        subject = request.POST.get("subject", "").strip()
        message_text = request.POST.get("message", "").strip()

        if not all([name, email, subject, message_text]):
            messages.error(request, "All fields are required.")
            return redirect("MyAccount:contact")

        ContactMessage.objects.create(
            user=request.user,
            name=name,
            email=email,
            subject=subject,
            message=message_text,
        )
        messages.success(request, "Message received! We'll respond soon.")
        return redirect("MyAccount:contact")

    return render(request, "contacts.html")

# ======================================================================
# FAQ, POLICIES & RETURNS
# ======================================================================

def faq_list(request):
    faqs = FAQ.objects.filter(is_active=True).order_by("category", "order")
    categories = faqs.values_list("category", flat=True).distinct()

    faq_dict = {
        category: faqs.filter(category=category)
        for category in categories
    }

    context = {
        "faq_dict": faq_dict,
        "faqs": faqs,
    }
    return render(request, "faq.html", context)

def return_policy(request):
    policy = ReturnPolicy.objects.filter(is_active=True).first()
    return render(request, "return_policy.html", {"policy": policy})

def terms_of_service(request):
    tos = TermsOfService.objects.filter(is_active=True).order_by("-version").first()
    return render(request, "terms_of_service.html", {"tos": tos})

def privacy_policy(request):
    context = {
        "page_title": "Privacy Policy",
        "last_updated": "November 28, 2025",
        "company_name": "ShopZone E-Commerce Pvt. Ltd.",
        "contact_email": "support@shopzone.com",
        "support_phone": "+91-XXXXXXXXXX",
        "address": "Noida, Uttar Pradesh, India - 201301",
        "registration_number": "UXXXXXXUP2025PTCXXXXX",
    }
    return render(request, "privacy_policy.html", context)

@login_required
def request_return(request):
    if request.method == "POST":
        order_id = request.POST.get("order_id")
        product_name = request.POST.get("product_name", "Order Items").strip()
        reason = request.POST.get("reason", "").strip()
        description = request.POST.get("description", "").strip()

        order = get_object_or_404(Order, id=order_id, user=request.user)

        if order.status not in ["delivered", "confirmed"]:
            messages.error(request, "Only delivered or confirmed orders can be returned.")
            return redirect("MyStore:request_return")

        if len(description) < 20:
            messages.error(request, "Description must be at least 20 characters long.")
            return redirect("MyStore:request_return")

        return_request = ReturnRequest.objects.create(
            user=request.user,
            order=order,
            product_name=product_name,
            reason=reason,
            description=description,
            status="pending",
        )

        messages.success(
            request,
            f"Return request #{return_request.id} submitted successfully!",
        )
        return redirect("MyStore:return_status", request_id=return_request.id)

    orders = Order.objects.filter(
        user=request.user,
        status__in=["delivered", "confirmed"],
    ).order_by("-created_at")

    return render(request, "request_return.html", {"orders": orders})

@login_required
def return_status(request, request_id):
    return_request_obj = get_object_or_404(
        ReturnRequest,
        id=request_id,
        user=request.user,
    )
    return render(request, "return_status.html", {"return_request": return_request_obj})

@login_required
def my_returns(request):
    returns = (
        ReturnRequest.objects
        .filter(user=request.user)
        .select_related("order", "user")
        .order_by("-requested_at")
    )
    return render(request, "my_returns.html", {"returns": returns})

@login_required
@require_POST
def cancel_return_request(request, request_id):
    return_request = get_object_or_404(
        ReturnRequest,
        id=request_id,
        user=request.user,
    )

    if return_request.status != "pending":
        messages.error(request, "Only pending return requests can be cancelled.")
        return redirect("MyStore:my_returns")

    return_request.delete()
    messages.success(request, f"Return request #{request_id} has been cancelled successfully.")
    return redirect("MyStore:my_returns")

# ======================================================================
# SMS SIGNAL HANDLERS (Optional - for admin status updates)
# ======================================================================

@receiver(post_save, sender=Order)
def order_status_changed(sender, instance, **kwargs):
    """Auto-send SMS when order status changes (useful for admin updates)"""
    if kwargs.get('created'):
        # Order just created
        _send_order_notification(instance, 'order_placed')
    else:
        # Order updated - check if status changed (requires tracking old status)
        # For simplicity, send on any update - refine as needed
        if instance.status in ['confirmed', 'shipped', 'delivered', 'cancelled']:
            _send_order_notification(instance, instance.status)

@login_required
@require_POST
def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    new_status = request.POST.get('status')
    
    if new_status in Order.STATUS_CHOICES:  # Assuming you have status choices
        old_status = order.status
        order.status = new_status
        order.save()
        
        # Send SMS if status changed
        if old_status != new_status:
            _send_order_notification(order, new_status)
        
        messages.success(request, f"Order status updated to {new_status}")
    else:
        messages.error(request, "Invalid status")
    
    return redirect("MyAccount:order_detail", order_id=order_id)