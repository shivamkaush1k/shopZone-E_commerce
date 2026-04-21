"""
Django settings for e_commerce project.
"""

from pathlib import Path
from django.contrib.messages import constants as messages
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent


# ==================== CORE SETTINGS ====================
SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = [host.strip() for host in config(
    "ALLOWED_HOSTS",
    default="127.0.0.1,localhost"
).split(",") if host.strip()]


# ==================== APPLICATIONS ====================
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "import_export",
    "razorpay",

    "MyAccount",
    "MyStore",
    "PaymentMethod",
    "Validation",
    "login",
]


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


ROOT_URLCONF = "e_commerce.urls"


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "MyStore.context_processors.cart_context",
            ],
        },
    },
]


WSGI_APPLICATION = "e_commerce.wsgi.application"


# ==================== DATABASE ====================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": config("DB_NAME", default="ecommerce_db"),
        "USER": config("DB_USER", default="root"),
        "PASSWORD": config("DB_PASSWORD", default=""),
        "HOST": config("DB_HOST", default="localhost"),
        "PORT": config("DB_PORT", default="3306"),
        "OPTIONS": {
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
            "charset": "utf8mb4",
        },
    }
}


# ==================== AUTH ====================
AUTHENTICATION_BACKENDS = [
    "login.backends.EmailOrUsernameBackend",
    "django.contrib.auth.backends.ModelBackend",
]

LOGIN_URL = "login:login"
LOGIN_REDIRECT_URL = "MyAccount:dashboard"
LOGOUT_REDIRECT_URL = "login:home"


# ==================== PASSWORD VALIDATION ====================
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# ==================== INTERNATIONALIZATION ====================
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True


# ==================== STATIC & MEDIA ====================
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ==================== EMAIL ====================
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = config("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = config(
    "DEFAULT_FROM_EMAIL",
    default="ShopZone <noreply@shopzone.com>"
)
CONTACT_RECEIVER_EMAIL = config(
    "CONTACT_RECEIVER_EMAIL",
    default=EMAIL_HOST_USER
)


# ==================== SMS ====================
TWILIO_ACCOUNT_SID = config("TWILIO_ACCOUNT_SID", default="")
TWILIO_AUTH_TOKEN = config("TWILIO_AUTH_TOKEN", default="")
TWILIO_PHONE_NUMBER = config("TWILIO_PHONE_NUMBER", default="")


# ==================== SESSION ====================
SESSION_COOKIE_AGE = 1209600
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False


# ==================== PASSWORD RESET ====================
PASSWORD_RESET_TIMEOUT = 3600


# ==================== SECURITY ====================
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

if not DEBUG:
    SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=True, cast=bool)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = config("SECURE_HSTS_SECONDS", default=31536000, cast=int)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
else:
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SECURE_HSTS_SECONDS = 0


# ==================== MESSAGE TAGS ====================
MESSAGE_TAGS = {
    messages.DEBUG: "debug",
    messages.INFO: "info",
    messages.SUCCESS: "success",
    messages.WARNING: "warning",
    messages.ERROR: "danger",
}

# ==================== PAYMENT GATEWAY ====================
PAYMENT_GATEWAY = config("PAYMENT_GATEWAY", default="razorpay")

RAZORPAY_MODE = config("RAZORPAY_MODE", default="TEST").upper()

if RAZORPAY_MODE == "LIVE":
    RAZORPAY_KEY_ID = config("RAZORPAY_LIVE_KEY_ID", default="")
    RAZORPAY_KEY_SECRET = config("RAZORPAY_LIVE_KEY_SECRET", default="")
else:
    RAZORPAY_KEY_ID = config("RAZORPAY_TEST_KEY_ID", default="")
    RAZORPAY_KEY_SECRET = config("RAZORPAY_TEST_KEY_SECRET", default="")

RAZORPAY_CURRENCY = config("RAZORPAY_CURRENCY", default="INR")
RAZORPAY_COMPANY_NAME = config("RAZORPAY_COMPANY_NAME", default="ShopZone")

# ==================== SITE CONFIG ====================
SITE_URL = config("SITE_URL", default="http://127.0.0.1:8000")


# ==================== LOGGING ====================
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {name} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": BASE_DIR / "payment.log",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "MyStore.payment": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}




# For phone numbers
PHONENUMBER_DEFAULT_REGION = 'IN'  # India (+91)