from django.urls import path
from . import views

app_name = "PaymentMethod"

urlpatterns = [
    path("initiate/<int:order_id>/", views.initiate_payment, name="initiate_payment"),
    path("process/<int:payment_id>/", views.process_payment, name="process_payment"),
    path("callback/", views.payment_callback, name="payment_callback"),

    path("success/", views.payment_success, name="payment_success"),
    path("failed/", views.payment_failed, name="payment_failed"),
    path("verify/", views.verify_payment, name="verify_payment"),

    path("history/", views.payment_history, name="payment_history"),
    path("receipt/<int:payment_id>/", views.payment_receipt, name="payment_receipt"),

    path("methods/", views.payment_methods_view, name="payment_methods"),
    path("methods/add/", views.add_payment_method_view, name="add_payment_method"),
    path("methods/<int:payment_id>/edit/", views.edit_payment_method_view, name="edit_payment_method"),
    path("methods/<int:payment_id>/delete/", views.delete_payment_method_view, name="delete_payment_method"),
]