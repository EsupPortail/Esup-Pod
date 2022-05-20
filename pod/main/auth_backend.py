from django.contrib.auth.backends import ModelBackend
from django.contrib.sites.models import Site
from django.contrib.auth.models import User


class SiteBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None):
        user_or_none = super(SiteBackend, self).authenticate(request, username, password)
        print(user_or_none)
        site = Site.objects.get_current()
        if (
            user_or_none
            and not user_or_none.is_superuser
            and (site not in user_or_none.owner.sites.all())
        ):
            user_or_none = None
        return user_or_none

    def get_user(self, user_id):
        try:
            site = Site.objects.get_current()
            user = User.objects.get(pk=user_id)
            if user and not user.is_superuser and (site not in user.owner.sites.all()):
                user = None
            return user
        except User.DoesNotExist:
            return None
