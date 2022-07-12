
import hashlib

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.contrib.sites.models import Site
from django.contrib.auth.models import User
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.template.defaultfilters import slugify

from pod.authentication.models import AccessGroup
from pod.main.models import get_nextautoincrement


SECRET_KEY = getattr(settings, "SECRET_KEY", "")


def two_hours_hence():
    return timezone.now() + timezone.timedelta(hours=2)


class Meeting(models.Model):
    """ This models hold information about each meeting room.
        When creating a big blue button room with BBB APIs,
        Will store it's info here for later usages.
    """
    name = models.CharField(
        max_length=255,
        verbose_name=_('Meeting Name')
    )
    meeting_id = models.SlugField(
        max_length=200,
        verbose_name=_('Meeting ID'),
        editable=False,
    )
    owner = models.ForeignKey(
        User,
        verbose_name=_("Owner"),
        related_name="owner_meeting",
        on_delete=models.CASCADE)
    additional_owners = models.ManyToManyField(
        User,
        blank=True,
        verbose_name=_("Additional owners"),
        related_name="owners_meetings",
        help_text=_(
            "You can add additional owners to the meeting."
        ),
    )
    attendee_password = models.CharField(
        max_length=50,
        verbose_name=_('Attendee Password')
    )
    moderator_password = models.CharField(
        max_length=50,
        verbose_name=_('Moderator Password'),
        editable=False
    )
    start_at = models.DateTimeField(_("Start date"), default=timezone.now)
    end_at = models.DateTimeField(_("End date"), default=two_hours_hence())
    is_restricted = models.BooleanField(
        verbose_name=_("Restricted access"),
        help_text=_(
            "If this box is checked, "
            "the meeting will only be accessible to authenticated users."
        ),
        default=False,
    )
    restrict_access_to_groups = models.ManyToManyField(
        AccessGroup,
        blank=True,
        verbose_name=_("Groups"),
        help_text=_("Select one or more groups who can access to this meeting"),
    )
    is_running = models.BooleanField(
        default=False,
        verbose_name=_('Is running'),
        help_text=_('Indicates whether this meeting is running in BigBlueButton or not!'),
        editable=False
    )
    site = models.ForeignKey(
        Site,
        verbose_name=_("Site"),
        on_delete=models.CASCADE
    )

    # Configs
    max_participants = models.IntegerField(
        default=10,
        verbose_name=_('Max Participants')
    )
    welcome_text = models.TextField(
        default=_('Welcome!'),
        verbose_name=_('Meeting Text in Bigbluebutton')
    )
    logout_url = models.CharField(
        max_length=500,
        default='', null=True, blank=True,
        verbose_name=_('URL to visit after user logged out')
    )
    record = models.BooleanField(
        default=True,
        verbose_name=_('Record')
    )
    auto_start_recording = models.BooleanField(
        default=False,
        verbose_name=_('Auto Start Recording')
    )
    allow_start_stop_recording = models.BooleanField(
        default=True,
        verbose_name=_('Allow Stop/Start Recording'),
        help_text=_('Allow the user to start/stop recording. (default true)')
    )
    webcam_only_for_moderators = models.BooleanField(
        default=False,
        verbose_name=_('Webcam Only for moderators?'),
        help_text=_('will cause all webcams shared by viewers '
                    'during this meeting to only appear for moderators')
    )

    # Lock settings
    lock_settings_disable_cam = models.BooleanField(
        default=False,
        verbose_name=_('Disable Camera'),
        help_text=_('will prevent users from sharing their camera in the meeting')
    )
    lock_settings_disable_mic = models.BooleanField(
        default=False,
        verbose_name=_('Disable Mic'),
        help_text=_('will only allow user to join listen only')
    )
    lock_settings_disable_private_chat = models.BooleanField(
        default=False,
        verbose_name=_('Disable Private chat'),
        help_text=_('if True will disable private chats in the meeting')
    )
    lock_settings_disable_public_chat = models.BooleanField(
        default=False,
        verbose_name=_('Disable public chat'),
        help_text=_('if True will disable public chat in the meeting')
    )
    lock_settings_disable_note = models.BooleanField(
        default=False,
        verbose_name=_('Disable Note'),
        help_text=_('if True will disable notes in the meeting.')
    )
    lock_settings_locked_layout = models.BooleanField(
        default=False,
        verbose_name=_('Locked Layout'),
        help_text=_('will lock the layout in the meeting. ')
    )

    # Not important Info
    parent_meeting_id = models.CharField(
        null=True,
        blank=True,
        max_length=100,
        verbose_name=_('Parent Meeting ID')
    )
    internal_meeting_id = models.CharField(
        null=True,
        blank=True,
        max_length=100,
        verbose_name=_('Internal Meeting ID')
    )
    voice_bridge = models.CharField(
        max_length=50,
        null=True, blank=True,
        verbose_name=_('Voice Bridge')
    )

    # Hook related info
    hook_id = models.CharField(
        null=True, blank=True,
        max_length=50, default='',
        verbose_name=_('Hook ID received from BBB')
    )
    hook_url = models.CharField(
        default='',
        max_length=500,
        null=True, blank=True,
        verbose_name=_('Hook URL')
    )

    # Time related Info
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '{}-{}'.format("%04d" % self.id, self.name)

    def save(self, *args, **kwargs):
        """Store a video object in db."""
        newid = -1
        if not self.id:
            try:
                newid = get_nextautoincrement(Meeting)
            except Exception:
                try:
                    newid = Meeting.objects.latest("id").id
                    newid += 1
                except Exception:
                    newid = 1
        else:
            newid = self.id
        newid = "%04d" % newid
        self.meeting_id = "%s-%s" % (newid, slugify(self.name))
        super(Meeting, self).save(*args, **kwargs)

    def get_hashkey(self):
        return hashlib.sha256(
            ("%s-%s" % (SECRET_KEY, self.attendee_password)).encode("utf-8")
        ).hexdigest()

    class Meta:
        db_table = 'meeting'
        verbose_name = 'Meeting'
        verbose_name_plural = _('Meeting')
        ordering = ["-created_at", "-id"]
        get_latest_by = "created_at"
        constraints = [
            models.UniqueConstraint(
                fields=['meeting_id', 'site'],
                name='meeting_unique_slug_site'
            )
        ]


@receiver(pre_save, sender=Meeting)
def default_site_meeting(sender, instance, **kwargs):
    if not hasattr(instance, 'site'):
        instance.site = Site.objects.get_current()
    if instance.start_at > instance.end_at:
        raise ValueError(_('Start date must be less than end date'))
