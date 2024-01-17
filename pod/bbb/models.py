import importlib

from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.utils import timezone


USE_BBB = getattr(settings, "USE_BBB", False)


class BBB_Meeting(models.Model):
    # Meeting id for the BBB session
    meeting_id = models.CharField(
        _("Meeting id"), max_length=200, help_text=_("Id of the BBB meeting.")
    )
    # Internal meeting id for the BBB session
    internal_meeting_id = models.CharField(
        _("Internal meeting id"),
        max_length=200,
        help_text=_("Internal id of the BBB meeting."),
    )
    # Meeting name for the BBB session
    meeting_name = models.CharField(
        _("Meeting name"),
        max_length=200,
        help_text=_("Name of the BBB meeting."),
    )
    # Date of the BBB session
    session_date = models.DateTimeField(_("Session date"), default=timezone.now)
    # Encoding step / status of the process
    ENCODING_STEP = (
        (0, _("Publish is possible")),
        (1, _("Waiting for encoding")),
        (2, _("Encoding in progress")),
        (3, _("Already published")),
    )
    encoding_step = models.IntegerField(
        _("Encoding step"),
        choices=ENCODING_STEP,
        help_text=_(
            "Encoding step for conversion of the BBB presentation to video file."
        ),
        default=0,
    )
    # Is this meeting was recorded in BigBlueButton?
    recorded = models.BooleanField(
        _("Recorded"), help_text=_("BBB presentation recorded?"), default=False
    )
    # Is the recording of the presentation is available in BigBlueButton?
    recording_available = models.BooleanField(
        _("Recording available"),
        help_text=_("BBB presentation recording is available?"),
        default=False,
    )
    # URL of the recording of the BigBlueButton presentation
    recording_url = models.CharField(
        _("Recording url"),
        help_text=_("URL of the recording of the BBB presentation."),
        max_length=200,
    )
    # URL of the recording thumbnail of the BigBlueButton presentation
    thumbnail_url = models.CharField(
        _("Thumbnail url"),
        help_text=_("URL of the recording thumbnail of the BBB presentation."),
        max_length=200,
    )
    # User who converted the BigBlueButton presentation to video file
    encoded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={"is_staff": True},
        verbose_name=_("User"),
        null=True,
        blank=True,
        help_text=_("User who converted the BBB presentation to video file."),
    )
    # Last date of the BBB session in progress
    last_date_in_progress = models.DateTimeField(
        _("Last date in progress"),
        default=timezone.now,
        help_text=_("Last date where BBB session was in progress."),
    )

    def __unicode__(self):
        return "%s - %s" % (self.meeting_name, self.meeting_id)

    def __str__(self):
        return "%s - %s" % (self.meeting_name, self.meeting_id)

    def save(self, *args, **kwargs):
        super(BBB_Meeting, self).save(*args, **kwargs)

    class Meta:
        verbose_name = _("Meeting")
        verbose_name_plural = _("Meetings")
        ordering = ["session_date"]


@receiver(post_save, sender=BBB_Meeting)
def process_recording(sender, instance, created, **kwargs):
    # Convert the BBB presentation only one time
    # Be careful: this is the condition to create a video of the
    # BigBlueButton presentation only one time.
    if instance.encoding_step == 1 and instance.encoded_by is not None:
        mod = importlib.import_module("%s.plugins.type_%s" % (__package__, "bbb"))
        mod.process(instance)


# Management of the BigBlueButton users,
# with role = MODERATOR in BigBlueButton
class Attendee(models.Model):
    # Meeting for which this user was a moderator
    meeting = models.ForeignKey(
        BBB_Meeting, on_delete=models.CASCADE, verbose_name=_("Meeting")
    )
    # Full name (First_name Last_name) of the user from BigBlueButton
    full_name = models.CharField(
        _("Full name"),
        max_length=200,
        help_text=_("Full name of the user from BBB."),
    )
    # Role of this user (only MODERATOR for the moment)
    role = models.CharField(
        _("User role"),
        max_length=200,
        help_text=_("Role of the user from BBB."),
    )
    # Username of this user, if the BBB user was translated with a Pod user
    # Redundant information with user, but can be useful.
    username = models.CharField(
        _("Username / User id"),
        max_length=150,
        help_text=_("Username / User id, if the BBB user was matching a Pod user."),
    )

    # Pod user, if the BBB user was translated with a Pod user
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={"is_staff": True},
        verbose_name=_("User"),
        null=True,
        blank=True,
        help_text=_("User from the Pod database, if user found."),
    )

    def __unicode__(self):
        return "%s - %s" % (self.full_name, self.role)

    def __str__(self):
        return "%s - %s" % (self.full_name, self.role)

    def save(self, *args, **kwargs):
        super(Attendee, self).save(*args, **kwargs)

    class Meta:
        verbose_name = _("Attendee")
        verbose_name_plural = _("Attendees")
        ordering = ["full_name"]


# Management of BigBlueButton sessions for live
# See bbb-pod-live.php for more explanations.
class Livestream(models.Model):
    # Meeting
    meeting = models.ForeignKey(
        BBB_Meeting, on_delete=models.CASCADE, verbose_name=_("Meeting")
    )
    # Start date of the live
    start_date = models.DateTimeField(
        _("Start date"),
        default=timezone.now,
        help_text=_("Start date of the live."),
    )
    # End date of the live
    end_date = models.DateTimeField(
        _("End date"),
        null=True,
        blank=True,
        help_text=_("End date of the live."),
    )
    # Live status
    STATUS = (
        (0, _("Live not started")),
        (1, _("Live in progress")),
        (2, _("Live stopped")),
    )
    status = models.IntegerField(_("Live status"), choices=STATUS, default=0)
    # Server/Process performing the live
    server = models.CharField(
        _("Server"),
        max_length=20,
        null=True,
        blank=True,
        help_text=_("Server/process performing the live."),
    )
    # User that want to perform the live
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={"is_staff": True},
        verbose_name=_("User"),
        null=True,
        blank=True,
        help_text=_("Username / User id, that want to perform the live."),
    )
    # Restricted access to the created live
    is_restricted = models.BooleanField(
        verbose_name=_("Restricted access"),
        help_text=_("Is live only accessible to authenticated users?"),
        default=False,
    )
    # Broadcaster in charge to perform the live
    broadcaster_id = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Broadcaster"),
        help_text=_("Broadcaster in charge to perform live."),
    )
    # If the user wants that show the public chat in the live
    show_chat = models.BooleanField(
        verbose_name=_("Show public chat"),
        help_text=_("Do you want to show the public chat in the live?"),
        default=True,
    )
    # If the user wants to download the video of this meeting after the live
    download_meeting = models.BooleanField(
        verbose_name=_("Save meeting in Dashboard"),
        help_text=_(
            "Do you want to save the video of "
            "this meeting, at the end of the live, directly in “Dashboard“?"
        ),
        default=False,
    )
    # If the user wants that students have a chat in the live page
    enable_chat = models.BooleanField(
        verbose_name=_("Enable chat"),
        help_text=_(
            "Do you want a chat on the live page "
            "for students? Messages sent in this live page's chat will "
            "end up in BigBlueButton's public chat."
        ),
        default=False,
    )
    # Redis hostname, useful for chat
    redis_hostname = models.CharField(
        _("Redis hostname"),
        max_length=200,
        null=True,
        blank=True,
        help_text=_("Redis hostname, useful for chat"),
    )
    # Redis port, useful for chat
    redis_port = models.IntegerField(
        _("Redis port"),
        null=True,
        blank=True,
        help_text=_("Redis port, useful for chat"),
    )
    # Redis channel, useful for chat
    redis_channel = models.CharField(
        _("Redis channel"),
        max_length=200,
        null=True,
        blank=True,
        help_text=_("Redis channel, useful for chat"),
    )

    def __unicode__(self):
        return "%s - %s" % (self.meeting, self.status)

    def __str__(self):
        return "%s - %s" % (self.meeting, self.status)

    def save(self, *args, **kwargs):
        super(Livestream, self).save(*args, **kwargs)

    class Meta:
        verbose_name = _("Livestream")
        verbose_name_plural = _("Livestreams")
        ordering = ["start_date"]
