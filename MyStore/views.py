import json
import logging

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import (
    Cart,
    CartItem,
    Category,
    FAQ,
    Order,
    OrderItem,
    Product,
    ReturnPolicy,
    ReturnRequest,
    TermsOfService,
)
from MyAccount.models import Address
from MyStore.models import Review, Wishlist

logger = logging.getLogger(__name__)
User = get_user_model()

PRODUCTS_PER_PAGE = 12


# ======================================================================
# HELPERS
# ======================================================================

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

    if user_profile and hasattr(user_profile, "phone"):
        user_phone = user_profile.phone or ""

    if default_address:
        address_parts = []
        for field in ["street", "address_line", "city", "state", "pincode"]:
            if hasattr(default_address, field):
                value = getattr(default_address, field)
                if value:
                    address_parts.append(str(value))
        user_address = ", ".join(address_parts)
    elif user_profile and hasattr(user_profile, "address"):
        user_address = getattr(user_profile, "address", "") or ""

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


# ======================================================================
# HOME & BROWSING
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


# ======================================================================
# FAQ, POLICIES & INFO
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


# ======================================================================
# RETURNS
# ======================================================================

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
# WISHLIST AJAX
# ======================================================================

@login_required
@require_POST
def toggle_wishlist_ajax(request):
    raw_product_id = request.POST.get("product_id")

    if raw_product_id in [None, ""]:
        return JsonResponse(
            {"status": "error", "message": "Product ID is required"},
            status=400,
        )

    try:
        product_id = int(str(raw_product_id).strip())
        product = get_object_or_404(Product, id=product_id, is_active=True)

        item = Wishlist.objects.filter(
            user=request.user,
            product=product,
        ).first()

        if item:
            item.delete()
            return JsonResponse(
                {
                    "status": "removed",
                    "message": "Removed from wishlist",
                    "is_in_wishlist": False,
                    "product_id": product.id,
                }
            )

        Wishlist.objects.create(user=request.user, product=product)
        return JsonResponse(
            {
                "status": "added",
                "message": "Added to wishlist",
                "is_in_wishlist": True,
                "product_id": product.id,
            }
        )

    except (TypeError, ValueError):
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

import json
import logging
import re

from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_POST

from .models import FAQ, Order, Product, ReturnPolicy, TermsOfService

logger = logging.getLogger(__name__)


# ============================================================
# CHATBOT HELPERS
# ============================================================

def _clean_text(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _truncate_text(value, limit=280):
    text = _clean_text(value)
    return text if len(text) <= limit else text[:limit] + "..."


def _contains_any(text, keywords):
    text = (text or "").lower()
    return any(keyword in text for keyword in keywords)


def _normalize_message(message):
    message = _clean_text(message).lower()
    replacements = {
        "refunds": "refund",
        "returns": "return",
        "deliveries": "delivery",
        "payments": "payment",
        "products": "product",
        "orders": "order",
        "cancelled": "cancel",
        "shipping time": "shipping",
        "track order": "track my order",
        "where is my parcel": "where is my order",
        "cash on delivery": "cod",
        "sign in": "login",
    }
    for old, new in replacements.items():
        message = message.replace(old, new)
    return message


def _get_faq_matches(message):
    message = _clean_text(message)
    words = [w for w in message.split() if len(w) > 2]

    query = (
        Q(question__icontains=message)
        | Q(answer__icontains=message)
        | Q(category__icontains=message)
    )

    for word in words:
        query |= (
            Q(question__icontains=word)
            | Q(answer__icontains=word)
            | Q(category__icontains=word)
        )

    return FAQ.objects.filter(is_active=True).filter(query).order_by("category", "order")[:5]


def _get_product_matches(message):
    message = _clean_text(message)
    words = [w for w in message.split() if len(w) > 2]

    query = (
        Q(name__icontains=message)
        | Q(brand__icontains=message)
        | Q(category__name__icontains=message)
        | Q(description__icontains=message)
    )

    for word in words:
        query |= (
            Q(name__icontains=word)
            | Q(brand__icontains=word)
            | Q(category__name__icontains=word)
            | Q(description__icontains=word)
        )

    return (
        Product.objects.filter(is_active=True)
        .filter(query)
        .select_related("category")[:5]
    )


def _reply_greeting():
    return (
        "Hi! I’m ShopZone Assistant.\n\n"
        "I can help with:\n"
        "• products and prices\n"
        "• stock and availability\n"
        "• shipping and delivery\n"
        "• returns and refunds\n"
        "• payment methods\n"
        "• orders and tracking\n"
        "• cart, checkout, wishlist, and account help"
    )


def _reply_thanks():
    return "You’re welcome! You can also ask me about delivery, order status, refunds, prices, stock, or checkout."


def _reply_goodbye():
    return "Goodbye! If you need more help with ShopZone, just open the chat again."


def _reply_contact_support():
    return (
        "If you still need help, please contact ShopZone support from the contact page. "
        "I can also help with returns, shipping, products, payments, and orders."
    )


def _reply_shipping():
    faqs = FAQ.objects.filter(is_active=True).filter(
        Q(question__icontains="shipping")
        | Q(answer__icontains="shipping")
        | Q(question__icontains="delivery")
        | Q(answer__icontains="delivery")
        | Q(question__icontains="courier")
        | Q(answer__icontains="courier")
        | Q(question__icontains="dispatch")
        | Q(answer__icontains="dispatch")
    )[:4]

    if faqs:
        return "Here’s what I found about shipping and delivery:\n\n" + "\n\n".join(
            f"{faq.question}: {_truncate_text(faq.answer)}" for faq in faqs
        )

    return (
        "ShopZone provides shipping and delivery support. "
        "You can ask about shipping time, delivery status, dispatch, or tracking."
    )


def _reply_returns():
    policy = ReturnPolicy.objects.filter(is_active=True).first()
    if policy:
        content = getattr(policy, "content", "") or getattr(policy, "description", "")
        if content:
            return "Here’s a summary of ShopZone returns and refunds policy:\n\n" + _truncate_text(content, 420)

    faqs = FAQ.objects.filter(is_active=True).filter(
        Q(question__icontains="return")
        | Q(answer__icontains="return")
        | Q(question__icontains="refund")
        | Q(answer__icontains="refund")
        | Q(question__icontains="exchange")
        | Q(answer__icontains="exchange")
        | Q(question__icontains="replacement")
        | Q(answer__icontains="replacement")
    )[:4]

    if faqs:
        return "Here’s what I found about returns and refunds:\n\n" + "\n\n".join(
            f"{faq.question}: {_truncate_text(faq.answer)}" for faq in faqs
        )

    return "You can visit the return policy page or request a return from your account if your order is eligible."


def _reply_payments():
    faqs = FAQ.objects.filter(is_active=True).filter(
        Q(question__icontains="payment")
        | Q(answer__icontains="payment")
        | Q(question__icontains="cod")
        | Q(answer__icontains="cod")
        | Q(question__icontains="upi")
        | Q(answer__icontains="upi")
        | Q(question__icontains="card")
        | Q(answer__icontains="card")
        | Q(question__icontains="wallet")
        | Q(answer__icontains="wallet")
    )[:5]

    if faqs:
        return "Here’s what I found about payment methods:\n\n" + "\n\n".join(
            f"{faq.question}: {_truncate_text(faq.answer)}" for faq in faqs
        )

    return "ShopZone supports checkout and payment-related help, including COD where available."


def _reply_orders(user):
    if not user or not user.is_authenticated:
        return "Please log in to view or track your ShopZone orders."

    recent_orders = Order.objects.filter(user=user).order_by("-created_at")[:3]

    if recent_orders:
        return "Here are your recent orders:\n\n" + "\n".join(
            f"Order #{order.order_number} - Status: {order.status} - Total: ₹{order.total_amount}"
            for order in recent_orders
        )

    return "I could not find any recent orders in your account."


def _reply_track_order(user):
    if not user or not user.is_authenticated:
        return "Please log in first to track your order."

    latest_order = Order.objects.filter(user=user).order_by("-created_at").first()
    if latest_order:
        return (
            f"Your latest order is #{latest_order.order_number} and its current status is '{latest_order.status}'. "
            "You can open your orders page for more details."
        )

    return "I could not find any recent order to track."


def _reply_cancel_order(user):
    if not user or not user.is_authenticated:
        return "Please log in first, then check your orders page to see whether the order can be cancelled."

    latest_order = Order.objects.filter(user=user).order_by("-created_at").first()
    if latest_order:
        return (
            f"Your latest order is #{latest_order.order_number} with status '{latest_order.status}'. "
            "If it has not been shipped or delivered yet, cancellation may be possible from your orders section."
        )

    return "I couldn’t find a recent order to cancel."


def _reply_cart_help():
    return "You can add items to cart from the product page, update quantity in the cart, or remove products before checkout."


def _reply_checkout_help():
    return (
        "At checkout, enter your full name, address, phone number, and choose a payment method. "
        "If your cart is empty, checkout cannot continue."
    )


def _reply_wishlist_help():
    return "You can save products to your wishlist and remove them anytime from the wishlist icon or wishlist page."


def _reply_login_help():
    return (
        "If you cannot access orders, returns, or saved information, please log in first. "
        "After login, use My Account for orders, addresses, and returns."
    )


def _reply_account_help():
    return "You can manage your profile, addresses, orders, and returns from your account section after login."


def _reply_offers():
    faqs = FAQ.objects.filter(is_active=True).filter(
        Q(question__icontains="offer")
        | Q(answer__icontains="offer")
        | Q(question__icontains="discount")
        | Q(answer__icontains="discount")
        | Q(question__icontains="coupon")
        | Q(answer__icontains="coupon")
        | Q(question__icontains="promo")
        | Q(answer__icontains="promo")
    )[:4]

    if faqs:
        return "Here’s what I found about offers and discounts:\n\n" + "\n\n".join(
            f"{faq.question}: {_truncate_text(faq.answer)}" for faq in faqs
        )

    return "Offers and coupons may be available during promotions or checkout. Please check banners and product pages."


def _reply_terms():
    tos = TermsOfService.objects.filter(is_active=True).order_by("-version").first()
    if tos:
        content = getattr(tos, "content", "") or getattr(tos, "description", "")
        if content:
            return "Here’s a short summary from ShopZone terms and policy:\n\n" + _truncate_text(content, 420)

    return "You can visit the terms and policies page for more details."


def _reply_privacy():
    return "You can check the privacy policy page for details about data collection, account information, and store policies."


def _reply_product_search(message):
    products = _get_product_matches(message)
    if products:
        lines = []
        for product in products:
            category_name = product.category.name if product.category else "General"
            stock_text = product.stock if product.stock is not None else "Available"
            lines.append(
                f"{product.name} | Brand: {getattr(product, 'brand', 'N/A')} | "
                f"Category: {category_name} | Price: ₹{product.price} | Stock: {stock_text}"
            )
        return "Here are some matching ShopZone products:\n\n" + "\n".join(lines)

    return "I couldn’t find an exact product match. Try asking by product name, brand, or category."


def _reply_stock(message):
    products = _get_product_matches(message)
    if products:
        return "Here’s the stock info I found:\n\n" + "\n".join(
            f"{product.name} - Stock: {product.stock if product.stock is not None else 'Available'}"
            for product in products
        )

    return "I couldn’t find stock details for that item. Try using the exact product name."


def _reply_price(message):
    products = _get_product_matches(message)
    if products:
        return "Here are the prices I found:\n\n" + "\n".join(
            f"{product.name} - ₹{product.price}" for product in products
        )

    return "I couldn’t find the product price. Try using the exact product name or brand."


def _reply_recommendations():
    products = Product.objects.filter(is_active=True).select_related("category").order_by("-id")[:5]
    if products:
        return "Here are some products you may like:\n\n" + "\n".join(
            f"{product.name} - ₹{product.price}" for product in products
        )

    return "I don’t have product recommendations right now. Please browse the product list page."


def _reply_availability(message):
    return _reply_stock(message)


def _reply_faq(message):
    faqs = _get_faq_matches(message)
    if faqs:
        return "Here’s what I found in ShopZone FAQ:\n\n" + "\n\n".join(
            f"{faq.question}: {_truncate_text(faq.answer)}" for faq in faqs
        )

    return (
        "Sorry, I couldn’t find a direct answer for that. "
        "Try asking about products, delivery, returns, payments, cart, checkout, or order status."
    )


def _get_quick_replies(message, user=None):
    text = (message or "").lower()

    if _contains_any(text, ["return", "refund", "exchange", "replacement"]):
        return [
            {"text": "Return policy", "url": reverse("MyStore:return_policy")},
            {"text": "Request a return", "url": reverse("MyStore:request_return")},
            {"text": "My returns", "url": reverse("MyStore:my_returns")},
            {"text": "Contact support", "url": reverse("MyAccount:contact")},
        ]

    if _contains_any(text, ["order", "track", "status", "cancel"]):
        items = [
            {"text": "Track my order"},
            {"text": "Cancel my order"},
            {"text": "Shipping and delivery"},
            {"text": "Contact support", "url": reverse("MyAccount:contact")},
        ]
        if user and user.is_authenticated:
            items.insert(0, {"text": "My orders", "url": reverse("MyAccount:orders")})
        return items

    if _contains_any(text, ["payment", "cod", "upi", "card", "wallet", "checkout"]):
        return [
            {"text": "Payment methods"},
            {"text": "Cash on delivery"},
            {"text": "Checkout help"},
            {"text": "Shipping and delivery"},
        ]

    if _contains_any(text, ["product", "price", "stock", "available", "buy", "brand", "category"]):
        return [
            {"text": "Browse products", "url": reverse("MyStore:product_list")},
            {"text": "Product prices"},
            {"text": "Stock availability"},
            {"text": "Returns and refunds"},
        ]

    if _contains_any(text, ["login", "account", "wishlist", "cart", "checkout"]):
        items = [
            {"text": "Cart help"},
            {"text": "Checkout help"},
            {"text": "Contact support", "url": reverse("MyAccount:contact")},
        ]
        if user and user.is_authenticated:
            items.insert(0, {"text": "My orders", "url": reverse("MyAccount:orders")})
        return items

    return [
        {"text": "Shipping and delivery"},
        {"text": "Returns and refunds"},
        {"text": "Payment methods"},
        {"text": "Track my order"},
    ]


def _generate_chatbot_reply(message, user=None):
    text = _normalize_message(message)

    if not text:
        return "Please enter a message."

    if _contains_any(text, ["hi", "hello", "hey", "good morning", "good evening", "good afternoon"]):
        return _reply_greeting()

    if _contains_any(text, ["thanks", "thank you", "thx"]):
        return _reply_thanks()

    if _contains_any(text, ["bye", "goodbye", "see you"]):
        return _reply_goodbye()

    if _contains_any(text, ["contact", "support", "help desk", "customer care"]):
        return _reply_contact_support()

    if _contains_any(text, ["track my order", "where is my order", "track order", "tracking"]):
        return _reply_track_order(user)

    if _contains_any(text, ["cancel order", "cancel my order"]):
        return _reply_cancel_order(user)

    if _contains_any(text, ["order", "order status", "my order"]):
        return _reply_orders(user)

    if _contains_any(text, ["return", "refund", "exchange", "replacement", "money back"]):
        return _reply_returns()

    if _contains_any(text, ["shipping", "delivery", "courier", "dispatch", "parcel"]):
        return _reply_shipping()

    if _contains_any(text, ["payment", "cod", "upi", "card", "wallet"]):
        return _reply_payments()

    if _contains_any(text, ["cart", "add to cart", "remove from cart", "cart issue"]):
        return _reply_cart_help()

    if _contains_any(text, ["checkout", "place order", "buy now"]):
        return _reply_checkout_help()

    if _contains_any(text, ["wishlist", "save item", "saved products"]):
        return _reply_wishlist_help()

    if _contains_any(text, ["login", "sign in", "account", "profile"]):
        return _reply_login_help()

    if _contains_any(text, ["address", "profile address", "saved address"]):
        return _reply_account_help()

    if _contains_any(text, ["offer", "discount", "coupon", "promo", "sale"]):
        return _reply_offers()

    if _contains_any(text, ["terms", "agreement", "policy"]):
        return _reply_terms()

    if _contains_any(text, ["privacy", "data", "personal information"]):
        return _reply_privacy()

    if _contains_any(text, ["recommend", "suggest", "best product", "show products"]):
        return _reply_recommendations()

    if _contains_any(text, ["stock", "available", "availability", "in stock", "out of stock"]):
        return _reply_availability(message)

    if _contains_any(text, ["price", "cost", "how much", "rate"]):
        return _reply_price(message)

    if _contains_any(text, ["product", "brand", "category", "buy"]):
        return _reply_product_search(message)

    return _reply_faq(message)


# ============================================================
# CHATBOT VIEW
# ============================================================

@require_POST
def chat_message(request):
    try:
        data = json.loads(request.body or "{}")
        user_message = (data.get("message") or "").strip()

        if not user_message:
            return JsonResponse(
                {
                    "success": False,
                    "reply": "Please enter a message.",
                    "quick_replies": _get_quick_replies(""),
                },
                status=400,
            )

        user = request.user if request.user.is_authenticated else None
        reply = _generate_chatbot_reply(user_message, user)

        return JsonResponse(
            {
                "success": True,
                "reply": reply,
                "quick_replies": _get_quick_replies(user_message, user),
            }
        )

    except json.JSONDecodeError:
        return JsonResponse(
            {
                "success": False,
                "reply": "Invalid request format.",
                "quick_replies": _get_quick_replies(""),
            },
            status=400,
        )
    except Exception:
        logger.exception("Error in chatbot view")
        return JsonResponse(
            {
                "success": False,
                "reply": "Sorry, I’m having trouble right now. Please try again later.",
                "quick_replies": [
                    {"text": "Shipping and delivery"},
                    {"text": "Returns and refunds"},
                    {"text": "Payment methods"},
                    {"text": "Contact support", "url": reverse("MyAccount:contact")},
                ],
            },
            status=500,
        )

