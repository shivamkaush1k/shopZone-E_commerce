import json
import logging
from django.urls import reverse  # ← MISSING IMPORT

import razorpay
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .forms import PaymentInitiateForm, PaymentMethodForm
from .models import Invoice, Payment, PaymentMethod
from MyStore.models import Order

logger = logging.getLogger(__name__)

def get_razorpay_client():
    return razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )

@login_required
def initiate_payment(request, order_id):
    """Start payment for a specific online order."""
    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user,
        status="pending",
        payment_method="online",
    )

    has_saved_payments = PaymentMethod.objects.filter(
        user=request.user,
        is_active=True
    ).exists()

    if request.method == "POST":
        form = PaymentInitiateForm(request.POST, user=request.user)
        if form.is_valid():
            payment_method_choice = form.cleaned_data["payment_method"]
            saved_payment = form.cleaned_data.get("saved_payment")

            selected_method = None
            if payment_method_choice == "saved":
                if not saved_payment:
                    messages.error(request, "Please select a saved payment method.")
                else:
                    selected_method = saved_payment
            else:
                selected_method = payment_method_choice

            payment = Payment.objects.create(
                user=request.user,
                order=order,
                amount=order.total_amount,
                payment_method=selected_method,
                gateway="Razorpay",
                status="pending",
                currency="INR",
            )

            return redirect("PaymentMethod:process_payment", payment_id=payment.id)
    else:
        form = PaymentInitiateForm(user=request.user)

    context = {
        "form": form,
        "order": order,
        "has_saved_payments": has_saved_payments,
    }
    return render(request, "initiate.html", context)

@login_required
def process_payment(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)

    if payment.status == "completed":
        messages.info(request, "This payment has already been completed.")
        return redirect(f"{reverse('PaymentMethod:payment_success')}?payment_id={payment.id}")

    try:
        razorpay_client = get_razorpay_client()

        if not payment.gateway_response or not payment.gateway_response.get("id"):
            razorpay_order = razorpay_client.order.create(
                {
                    "amount": int(payment.amount * 100),
                    "currency": payment.currency,
                    "receipt": str(payment.order.id),
                }
            )
            payment.gateway_response = razorpay_order
            payment.save(update_fields=["gateway_response"])
        else:
            razorpay_order = payment.gateway_response

        razorpay_payload = {
            "key": settings.RAZORPAY_KEY_ID,
            "amount": int(payment.amount * 100),
            "currency": payment.currency,
            "name": "ShopZone",
            "description": f"Order #{payment.order.order_number}",
            "order_id": razorpay_order["id"],
            "payment_id": payment.id,
            "callback_url": request.build_absolute_uri(reverse('PaymentMethod:payment_callback')),
            "prefill": {
                "name": payment.order.full_name,
                "email": payment.order.email,
                "contact": payment.order.phone,
            },
        }

        context = {
            "payment": payment,
            "order": payment.order,
            "razorpay_payload": razorpay_payload,
        }
        return render(request, "Payment/process.html", context)

    except Exception:
        logger.exception("Error processing payment")
        messages.error(request, "Unable to initialize payment gateway.")
        return redirect("PaymentMethod:initiate_payment", order_id=payment.order.id)

@csrf_exempt
@require_POST
def payment_callback(request):
    try:
        data = json.loads(request.body or "{}")

        payment_id = data.get("payment_id")
        razorpay_payment_id = data.get("razorpay_payment_id")
        razorpay_order_id = data.get("razorpay_order_id")
        razorpay_signature = data.get("razorpay_signature")

        if not all([payment_id, razorpay_payment_id, razorpay_order_id, razorpay_signature]):
            return JsonResponse(
                {"success": False, "error": "Missing required payment fields"},
                status=400,
            )

        payment = get_object_or_404(Payment, id=payment_id)

        razorpay_client = get_razorpay_client()
        razorpay_client.utility.verify_payment_signature({
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature,
        })

        if payment.status in ("pending", "failed"):
            payment.transaction_id = razorpay_payment_id
            payment.status = "completed"
            existing_response = payment.gateway_response or {}
            existing_response.update({
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_order_id": razorpay_order_id,
                "verified": True,
            })
            payment.gateway_response = existing_response
            payment.completed_at = timezone.now()
            payment.save(update_fields=["transaction_id", "status", "gateway_response", "completed_at"])

            if payment.order.status == "pending":
                payment.order.status = "confirmed"
                payment.order.save(update_fields=["status"])

        return JsonResponse({"success": True, "payment_id": payment.id})

    except razorpay.errors.SignatureVerificationError:
        logger.warning("Razorpay signature verification failed")
        return JsonResponse(
            {"success": False, "error": "Signature verification failed"},
            status=400,
        )
    except json.JSONDecodeError:
        return JsonResponse(
            {"success": False, "error": "Invalid JSON payload"},
            status=400,
        )
    except Exception:
        logger.exception("Payment callback failed")
        return JsonResponse(
            {"success": False, "error": "Payment callback failed"},
            status=400,
        )

@login_required
def payment_success(request):
    payment_id = request.GET.get("payment_id")
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)

    if payment.status == "completed" and payment.order:
        if payment.order.status != "confirmed":
            payment.order.status = "confirmed"
            payment.order.save(update_fields=["status"])
        messages.success(
            request,
            f"Payment successful! Order #{payment.order.order_number} confirmed.",
        )

    return render(request, "success.html", {"payment": payment})

@login_required
def payment_failed(request):
    payment_id = request.GET.get("payment_id")
    if not payment_id:
        messages.error(request, "Missing payment ID.")
        return redirect("PaymentMethod:payment_history")

    payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    return render(request, "Payment/failed.html", {"payment": payment})

@login_required
def payment_history(request):
    payments = Payment.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "Payment/history.html", {"payments": payments})

@login_required
def payment_receipt(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)

    invoice = getattr(payment, "invoice", None)
    if invoice is None:
        invoice = Invoice.objects.create(
            payment=payment,
            invoice_number=f"INV-{payment.created_at.year}-{payment.id:06d}",
            bill_to_name=(
                f"{request.user.first_name} {request.user.last_name}".strip()
                or request.user.username
            ),
            bill_to_email=request.user.email,
            bill_to_address="User Address",
            subtotal=payment.amount,
            tax=0,
            total=payment.amount,
        )

    return render(
        request,
        "Payment/receipt.html",
        {"invoice": invoice, "payment": payment},
    )

@login_required
def verify_payment(request):
    payment_id = request.GET.get("payment_id")
    if not payment_id:
        return JsonResponse(
            {"success": False, "error": "Missing payment_id"},
            status=400,
        )

    payment = get_object_or_404(Payment, id=payment_id, user=request.user)

    return JsonResponse({
        "success": True,
        "id": payment.id,
        "status": payment.status,
        "amount": str(payment.amount),
        "transaction_id": payment.transaction_id,
    })

@login_required
def payment_methods_view(request):
    methods = PaymentMethod.objects.filter(
        user=request.user, is_active=True
    ).order_by("-is_default", "-id")
    return render(
        request,
        "Payment/payment_methods.html",
        {"methods": methods},
    )

@login_required
def add_payment_method_view(request):
    if request.method == "POST":
        form = PaymentMethodForm(request.POST)
        if form.is_valid():
            method = form.save(commit=False)
            method.user = request.user

            if method.is_default:
                PaymentMethod.objects.filter(
                    user=request.user, is_default=True
                ).update(is_default=False)

            method.save()
            messages.success(request, "Payment method added successfully!")
            return redirect("PaymentMethod:payment_methods")
        messages.error(request, "Please correct the errors below.")
    else:
        form = PaymentMethodForm()

    return render(
        request,
        "Payment/add_payment_method.html",
        {"form": form},
    )

@login_required
def edit_payment_method_view(request, payment_id):
    method = get_object_or_404(PaymentMethod, id=payment_id, user=request.user)

    if request.method == "POST":
        form = PaymentMethodForm(request.POST, instance=method)
        if form.is_valid():
            updated_method = form.save(commit=False)
            updated_method.user = request.user

            if updated_method.is_default:
                PaymentMethod.objects.filter(
                    user=request.user, is_default=True
                ).exclude(id=updated_method.id).update(is_default=False)

            updated_method.save()
            messages.success(request, "Payment method updated!")
            return redirect("PaymentMethod:payment_methods")
        messages.error(request, "Please correct the errors below.")
    else:
        form = PaymentMethodForm(instance=method)

    return render(
        request,
        "Payment/edit_payment_method.html",
        {"form": form, "method": method},
    )

@login_required
def delete_payment_method_view(request, payment_id):
    method = get_object_or_404(PaymentMethod, id=payment_id, user=request.user)

    if request.method == "POST":
        method.is_active = False
        method.save(update_fields=["is_active"])
        messages.success(request, "Payment method removed!")
        return redirect("PaymentMethod:payment_methods")

    return render(
        "Payment/confirm_delete_payment.html",
        {"method": method},
    )