from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class EmailOrUsernameBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None

        # Try username first
        try:
            user = User.objects.get(username=username)
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        except User.DoesNotExist:
            pass

        # If not found by username, try email
        try:
            user = User.objects.get(email=username)
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        except User.DoesNotExist:
            pass

        return None


# login/backends.py
AUTHENTICATION_BACKENDS = [
    'login.backends.EmailOrUsernameBackend',  # Login with username OR email
    'django.contrib.auth.backends.ModelBackend',
]

# For phone numbers
PHONENUMBER_DEFAULT_REGION = 'IN'  # India (+91)