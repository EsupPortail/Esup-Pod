from django.utils import timezone

from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _

from pod.meetings.utils import BBB_ALLOW_START_STOP_RECORDING, BBB_AUTO_RECORDING, BBB_LOGOUT_URL, BBB_RECORD, BBB_WELCOME_TEXT, BigBlueButton, xml_to_json
#from select2 import fields as select2_fields

User = get_user_model()

class Meetings(models.Model):
    titre = models.CharField(
        max_length=100,
        verbose_name=_('Titre')
    )

    meeting_id = models.CharField(
        max_length=100,
        verbose_name=_('Meeting ID')
    )

    slug = models.SlugField(
        _("Slug"),
        max_length=100,
        help_text=_(
            'Used to access this instance, the "slug" is '
            "a short label containing only letters, "
            "numbers, underscore or dash top."
        ),
        editable=False,
    )
    '''
    sites = models.ManyToManyField(site)
    type = models.ForeignKey(types, verbose_name=_("Type"))
    owner = select2_fields.ForeignKey(
        User,
        ajax=True,
        verbose_name=_("Owner"),
        on_delete=models.CASCADE,
    )
    additional_owners = select2_fields.ManyToManyField(
        User,
        blank=True,
        ajax=True,
        js_options={"width": "off"},
        verbose_name=_("Additional owners"),
        related_name="owners_videos",
        help_text=_(
            "You can add additional owners to the video. They "
            "will have the same rights as you except that they "
            "can't delete this video."
        ),
    )
    '''

    start_date = models.DateTimeField(
        _("Start date"),
        default=timezone.now,
        help_text=_("Start date of the live."),
    )
    
    end_date = models.DateTimeField(
        _("End date"),
        default=timezone.now,
        null=True,
        blank=True,
        help_text=_("End date of the live."),
    )

    attendee_password = models.CharField(
        max_length=50,
        verbose_name=_('Mot de passe participants')
    )

    moderator_password = models.CharField(
        max_length=50,
        verbose_name=_('Mot de passe modérateurs')
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
        return "%s - %s" % (self.titre, self.meeting_id)

    class Meta:
        db_table = 'meetings'
        verbose_name = 'Meetings'
        verbose_name_plural = _('Meetings')

    def save(self, *args, **kwargs):
        if not self.titre:
            self.titre = self.meeting_id
        super(Meetings, self).save(*args, **kwargs)

    def info(self):
        # Will return result of bbb.get_meeting_info
        return BigBlueButton().meeting_info(
            self.meeting_id,
            self.moderator_password
        )

    def check_is_running(self, commit=True):
        """ Call bbb is_running method, and see if this meeting_id is running! """
        is_running = BigBlueButton().is_running(self.meeting_id)
        self.is_running = True if is_running in ['true', True, 'True'] else False
        if commit:
            self.save()
        return self.is_running

    def start(self):
        """ Will start already created meeting again. """
        result = BigBlueButton().start(
            name=self.name,
            meeting_id=self.meeting_id,
            attendee_password=self.attendee_password,
            moderator_password=self.moderator_password
        )

        if result:
            # It's better to create hook again,
            # So if by any reason is removed from bbb, again be created
            # If already exist will just give warning and will be ignored
            self.create_hook()

        return result

    def end(self):
        # If successfully ended, will return True
        ended = BigBlueButton().end_meeting(
            meeting_id=self.meeting_id,
            password=self.moderator_password
        )
        ended = True if ended == True else False
        if ended:
            self.is_running = False
            self.save()

        return ended

    def create_join_link(self, fullname, role='moderator', **kwargs):
        pw = self.moderator_password if role == 'moderator' else self.attendee_password
        link = BigBlueButton().join_url(self.meeting_id, fullname, pw, **kwargs)
        return link

    def create(cls, titre, meeting_id, **kwargs):
        kwargs.update({
            'record': kwargs.get('record', BBB_RECORD),
            'logout_url': kwargs.get('logout_url', BBB_LOGOUT_URL),
            'welcome_text': kwargs.get('welcome_text', BBB_WELCOME_TEXT),
            'auto_start_recording': kwargs.get('auto_start_recording', BBB_AUTO_RECORDING),
            'allow_start_stop_recording': kwargs.get('allow_start_stop_recording', BBB_ALLOW_START_STOP_RECORDING),
        })

        m_xml = BigBlueButton().start(titre=titre, meeting_id=meeting_id, **kwargs)
        print(m_xml)
        meeting_json = xml_to_json(m_xml)
        if meeting_json['returncode'] != 'SUCCESS':
            raise ValueError('Unable to create meeting!')

        # Now create a model for it.
        meeting, _ = Meetings.objects.get_or_create(meeting_id=meeting_id)

        meeting.titre = titre
        meeting.is_running = True
        meeting.record = kwargs.get('record', True)
        meeting.logout_url = kwargs.get('logout_url', '')
        meeting.voice_bridge = meeting_json['voiceBridge']
        meeting.attendee_password = meeting_json['attendeePW']
        meeting.moderator_password = meeting_json['moderatorPW']
        meeting.parent_meeting_id = meeting_json['parentMeetingID']
        meeting.internal_meeting_id = meeting_json['internalMeetingID']
        meeting.welcome_text = kwargs.get('welcome_text', BBB_WELCOME_TEXT)
        meeting.auto_start_recording = kwargs.get('auto_start_recording', True)
        meeting.allow_start_stop_recording = kwargs.get('allow_start_stop_recording', True)
        meeting.save()

        return meeting
