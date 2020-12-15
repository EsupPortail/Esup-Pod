
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User
from django.contrib.auth.backends import ModelBackend


class SettingsBackend(ModelBackend):

    def authenticate(self, request, username=None, password=None):
        print("ABCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC")
        login_valid = ('admin' == username)
        pwd_valid = check_password(password, 'admin')
        if login_valid and pwd_valid:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                # Create a new user. There's no need to set a password
                # because only the password from settings.py is checked.
                user = User(username=username)
                user.is_staff = True
                user.is_superuser = True
                user.save()
            return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None