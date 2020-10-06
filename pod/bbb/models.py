import importlib

from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.utils import timezone
from select2 import fields as select2_fields

USE_BBB = getattr(settings, 'USE_BBB', False)


class Meeting(models.Model):
    # Meeting id for the BBB session
    meeting_id = models.CharField(
        _('Meeting id'), max_length=200,
        help_text=_('Id of the BBB meeting.')
    )
    # Internal meeting id for the BBB session
    internal_meeting_id = models.CharField(
        _('Internal meeting id'),
        max_length=200, help_text=_('Internal id of the BBB meeting.')
    )
    # Meeting name for the BBB session
    meeting_name = models.CharField(
        _('Meeting name'),
        max_length=200, help_text=_('Name of the BBB meeting.')
    )
    # Date of the BBB session
    date = models.DateTimeField(_('date'), default=timezone.now)
    # Encoding step / status of the process. Possible values are :
    #  - 0 : default (Publish is possible)
    #  - 1 : Waiting for encoding
    #  - 2 : Encoding in progress
    #  - 3 : Already published
    encoding_step = models.IntegerField(
        _('Encoding step'),
        help_text=_('Encoding step for conversion of the '
                    'BBB presentation to video file.'),
        default=0)
    # Is this meeting was recorded in BigBlueButton ?
    recorded = models.BooleanField(
        _('Recorded'),
        help_text=_('BBB presentation recorded ?'),
        default=False)
    # Is the recording of the presentation is available in BigBlueButton ?
    recording_available = models.BooleanField(
        _('Recording available'),
        help_text=_('BBB presentation recording is available ?'),
        default=False)
    # URL of the recording of the BigBlueButton presentation
    recording_url = models.CharField(
        _('Recording url'),
        help_text=_('URL of the recording of the BBB presentation.'),
        max_length=200
    )
    # URL of the recording thumbnail of the BigBlueButton presentation
    thumbnail_url = models.CharField(
        _('Thumbnail url'),
        help_text=_('URL of the recording thumbnail of the BBB presentation.'),
        max_length=200
    )
    # User who converted the BigBlueButton presentation to video file
    encoded_by = select2_fields.ForeignKey(
        User, on_delete=models.CASCADE,
        limit_choices_to={'is_staff': True},
        verbose_name=_('User'), null=True, blank=True, help_text=_(
            'User who converted the BBB presentation to video file.')
    )

    def __unicode__(self):
        return "%s - %s" % (self.meeting_name, self.meeting_id)

    def __str__(self):
        return "%s - %s" % (self.meeting_name, self.meeting_id)

    def save(self, *args, **kwargs):
        super(Meeting, self).save(*args, **kwargs)

    class Meta:
        verbose_name = _("Meeting")
        verbose_name_plural = _("Meetings")
        ordering = ['date']


@receiver(post_save, sender=Meeting)
def process_recording(sender, instance, created, **kwargs):
    # Convert the BBB presentation only one time
    # Be careful : this is the condition to create a video of the
    # BigBlueButton presentation only one time.
    if instance.encoding_step == 1 and instance.encoded_by is not None:
        mod = importlib.import_module(
            '%s.plugins.type_%s' % (__package__, 'bbb'))
        mod.process(instance)


# Management of the BigBlueButton users,
# with role = MODERATOR in BigBlueButton
class User(models.Model):
    # User who performed the session in BigBlueButton
    meeting = models.ForeignKey(Meeting,
                                on_delete=models.CASCADE,
                                verbose_name=_('Meeting'))
    # Full name (First_name Last_name) of the user from BigBlueButton
    full_name = models.CharField(_('Full name'), max_length=200, help_text=_(
        'Full name of the user from BBB.')
    )
    # Role of this user (only MODERATOR for the moment)
    role = models.CharField(_('User role'), max_length=200, help_text=_(
        'Role of the user from BBB.')
    )
    # Username of this user, if the BBB user was translated with a Pod user
    # Redundant information with user, but can be useful.
    username = models.CharField(_('Username / User id'),
                                max_length=150, help_text=_(
                'Username / User id, if the BBB user was matching a Pod user.')
    )

    # Pod user, if the BBB user was translated with a Pod user
    user = select2_fields.ForeignKey(
        User, on_delete=models.CASCADE,
        limit_choices_to={'is_staff': True},
        verbose_name=_('User'), null=True, blank=True, help_text=_(
            'User from the Pod database, if user found.')
    )

    def __unicode__(self):
        return "%s - %s" % (self.full_name, self.role)

    def __str__(self):
        return "%s - %s" % (self.full_name, self.role)

    def save(self, *args, **kwargs):
        super(User, self).save(*args, **kwargs)

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        ordering = ['full_name']
