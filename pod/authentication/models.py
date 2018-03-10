from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import post_save
import hashlib

import logging
import traceback
logger = logging.getLogger(__name__)

AUTH_TYPE = getattr(
    settings, 'AUTH_TYPE', (('local', _('local')), ('CAS', 'CAS')))
AFFILIATION = getattr(
    settings, 'AUTH_TYPE',
    (('member', _('member')), ('student', _('student'))))
SECRET_KEY = getattr(settings, 'SECRET_KEY', '')


class Owner(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    auth_type = models.CharField(
        max_length=20, choices=AUTH_TYPE, default=AUTH_TYPE[0][0])
    affiliation = models.CharField(
        max_length=50, choices=AFFILIATION, default=AFFILIATION[0][0])
    commentaire = models.TextField(_('Comment'), blank=True, default="")
    hashkey = models.CharField(
        max_length=64, unique=True, blank=True, default="")

    def __str__(self):
        return "%s %s (%s)" % (self.user.first_name, self.user.last_name, self.user.username)

    def save(self, *args, **kwargs):
        self.hashkey = hashlib.sha256(
            (SECRET_KEY + self.user.username).encode('utf-8')).hexdigest()
        super(Owner, self).save(*args, **kwargs)


@receiver(post_save, sender=User)
def create_owner_profile(sender, instance, created, **kwargs):
    if created:
        try:
            Owner.objects.create(user=instance)
        except Exception as e:
            msg = u'\n Create owner profile ***** Error:%r' % e
            msg += '\n%s' % traceback.format_exc()
            logger.error(msg)
            print(msg)


# @receiver(post_save, sender=Owner)
# def check_hashkey(sender, instance, created, **kwargs):
#    print('coucou')
