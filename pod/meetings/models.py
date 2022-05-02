import datetime
from django.utils import timezone

from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _

User = get_user_model()

class Meetings(models.Model):
    meeting_name = models.CharField(
        max_length=100,
        verbose_name=_('Meeting Name')
    )

    meeting_id = models.CharField(
        max_length=100, unique=True,
        verbose_name=_('Meeting ID')
    )

    slug = models.SlugField(
        _("Slug"),
        unique=True,
        max_length=100,
        help_text=_(
            'Used to access this instance, the "slug" is '
            "a short label containing only letters, "
            "numbers, underscore or dash top."
        ),
        editable=False,
    )

    start_date = models.DateTimeField(
        _("Start date"),
        default=timezone.now,
        help_text=_("Start date of the live."),
    )
    
    end_date = models.DateTimeField(
        _("End date"),
        null=True,
        blank=True,
        help_text=_("End date of the live."),
    )

    attendee_password = models.CharField(
        max_length=50,
        verbose_name=_('Vieweur Password')
    )

    moderator_password = models.CharField(
        max_length=50,
        verbose_name=_('Moderator Password')
    )

    is_running = models.BooleanField(
        default=False,
        verbose_name=_('Is running'),
        help_text=_('Indicates whether this meeting is running in BigBlueButton or not!')
    )

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
        verbose_name=('Record')
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

    def __str__(self):
        return (self.meetings_name, self.meetings_id)

    class Meta:
        db_table = 'meetings'
        verbose_name = 'Meetings'
        verbose_name_plural = _('Meetings')

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if not self.name:
            self.name = self.meeting_id
        super(Meetings, self).save()

'''
class Attendee(models.Model):
    meetings = models.ForeignKey(
        null=True,
        blank=True,
        to=Meetings,
        db_index=True,
        related_name='attendee',
        verbose_name=_('Meetings'),
        on_delete=models.SET_NULL
    )

    fullname = models.CharField(
        null=True,
        blank=True,
        default='',
        max_length=50,
        verbose_name=_('User fullname')
    )

    role = models.CharField(
        max_length=200,
        verbose_name=_('Role')
    )

    username = models.CharField(
        max_length=150,
        verbose_name=_('User nameWelcome!')
    )

    user = models.ForeignKey(
        to=User,
        null=True,
        blank=True,
        db_index=True,
        verbose_name=_('User'),
        on_delete=models.SET_NULL,
        related_name='meetings_attendee'
    )

    def __str__(self):
        return (self.fullname, self.role)

    class Meta:
        db_table = 'meetings_attendee'
        verbose_name = 'Attendee'
        verbose_name_plural = _('Attendees')

class Stream(models.Model):
    user = models.ForeignKey(
        to=User,
        null=True,
        blank=True,
        db_index=True,
        verbose_name=_('User'),
        on_delete=models.SET_NULL,
        related_name='meetings_room'
    )

    meetings = models.ForeignKey(
        null=True,
        blank=True,
        to=Meetings,
        related_name='logs',
        verbose_name=_('Meetings'),
        on_delete=models.SET_NULL
    )

    start_date = models.DateTimeField(
        _("Start date"),
        default=timezone.now,
        help_text=_("Start date of the live."),
    )
    
    end_date = models.DateTimeField(
        _("End date"),
        null=True,
        blank=True,
        help_text=_("End date of the live."),
    )

    def __str__(self):
        return (self.meetings)

    class Meta:
        verbose_name = 'Stream'
        verbose_name_plural = _('Streams')
        ordering = ["start_date"]
'''