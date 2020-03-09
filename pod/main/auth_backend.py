from django.contrib.auth.backends import ModelBackend
from django.contrib.sites.models import Site
from django.contrib.auth.models import User


class SiteBackend(ModelBackend):
    def authenticate(self, **credentials):
        user_or_none = super(SiteBackend, self).authenticate(**credentials)
        site = Site.objects.get_current()
        if user_or_none and (site not in user_or_none.owner.sites.all()):
            user_or_none = None
        print(user_or_none)
        return user_or_none

    def get_user(self, user_id):
        try:
            return User.objects.get(
                pk=user_id, owner__sites=Site.objects.get_current())
        except User.DoesNotExist:
            return None
