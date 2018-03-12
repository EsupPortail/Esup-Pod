from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.apps import apps
from django.template.defaultfilters import slugify
try:
    from filepicker.models import CustomImageModel
except ImportError:
    pass

import hashlib
import os
import logging
import traceback
logger = logging.getLogger(__name__)

FILEPICKER = True if apps.is_installed('filepicker') else False
AUTH_TYPE = getattr(
    settings, 'AUTH_TYPE', (('local', _('local')), ('CAS', 'CAS')))
AFFILIATION = getattr(
    settings, 'AUTH_TYPE',
    (('member', _('member')), ('student', _('student'))))
SECRET_KEY = getattr(settings, 'SECRET_KEY', '')
FILES_DIR = getattr(
    settings, 'FILES_DIR', 'files')


def get_upload_path_files(instance, filename):
    fname, dot, extension = filename.rpartition('.')
    try:
        fname.index("/")
        return os.path.join(FILES_DIR,
                            '%s/%s.%s' % (os.path.dirname(fname),
                                          slugify(os.path.basename(fname)),
                                          extension))
    except ValueError:
        return os.path.join(FILES_DIR,
                            '%s.%s' % (slugify(fname), extension))


class AuthenticationImageModel(models.Model):
    image = models.ImageField(
        _('Image'), null=True, upload_to=get_upload_path_files,
        blank=True, max_length=255)


class Owner(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    auth_type = models.CharField(
        max_length=20, choices=AUTH_TYPE, default=AUTH_TYPE[0][0])
    affiliation = models.CharField(
        max_length=50, choices=AFFILIATION, default=AFFILIATION[0][0])
    commentaire = models.TextField(_('Comment'), blank=True, default="")
    hashkey = models.CharField(
        max_length=64, unique=True, blank=True, default="")
    if FILEPICKER:
        userpicture = models.ForeignKey(CustomImageModel,
                                        blank=True, null=True,
                                        verbose_name=_('Picture'))
    else:
        userpicture = models.ForeignKey(AuthenticationImageModel,
                                        blank=True, null=True,
                                        verbose_name=_('Picture'))

    def __str__(self):
        return "%s %s (%s)" % (self.user.first_name, self.user.last_name,
                               self.user.username)

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
