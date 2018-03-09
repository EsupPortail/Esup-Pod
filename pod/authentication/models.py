from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.conf import settings
import hashlib

import logging
logger = logging.getLogger(__name__)

AUTH_TYPE = getattr(
    settings, 'AUTH_TYPE', (('local', _('local')), ('CAS', 'CAS')))
AFFILIATION = getattr(settings, 'AFFILIATION', (('member', _('member'))))
SECRET_KEY = getattr(settings, 'SECRET_KEY', '')


class Owner(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    auth_type = models.CharField(
        max_length=20, choices=AUTH_TYPE, default=AUTH_TYPE.get(0))
    affiliation = models.CharField(
        max_length=50, choices=AFFILIATION, default=AFFILIATION.get(0))
    commentaire = models.TextField(_('Comment'), blank=True, default="")
    hashkey = models.CharField(
        max_length=64, unique=True, blank=True, default="")

    def save(self, *args, **kwargs):
        self.hashkey = hashlib.sha256(SECRET_KEY + self.username).hexdigest()
        super(Owner, self).save(*args, **kwargs)
