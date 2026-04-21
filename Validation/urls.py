from django.urls import path
from . import views

app_name = 'validation'
urlpatterns = [
    path('phone/', views.SendPhoneOTPView.as_view(), name='send_phone_otp'),
    path('otp/', views.VerifyOTPView.as_view(), name='verify_otp'),
    path('address/', views.verify_address, name='verify_address'),
]