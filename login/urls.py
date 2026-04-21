from django.urls import path
from . import views

app_name = 'login'

urlpatterns = [
    path('', views.home, name='home'),
    
    # Authentication
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    
    # Password reset
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('reset-password/<str:token>/', views.reset_password_view, name='reset_password'),
    path('password-reset/done/', views.password_reset_done_view, name='password_reset_done'),
    path('password-reset-complete/', views.password_reset_complete_view, name='password_reset_complete'),
    
    # Profile & Dashboard
    path('profile/', views.profile_view, name='profile'),
]