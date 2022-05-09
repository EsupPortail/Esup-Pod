from hashlib import sha1
import random
from urllib.parse import urlencode
from urllib.request import urlopen
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django import forms

from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _
import requests

from pod.meetings.utils import parse_xml

User = get_user_model()

class Meetings(models.Model):
    name = models.CharField(
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

    def __str__(self):
        return "%s - %s" % (self.name, self.meeting_id)

    class Meta:
        db_table = 'meetings'
        verbose_name = 'Meetings'
        verbose_name_plural = _('Meetings')

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = self.meeting_id
        super(Meetings, self).save(*args, **kwargs)

    def api_call(self, query, call):
        prepared = "%s%s%s" % (call, query, settings.SALT)
        print(prepared)
        checksum = sha1(str(prepared).encode("utf-8")).hexdigest()
        result = "%s&checksum=%s" % (query, checksum)
        return result

    def is_running(self):
        call = 'isMeetingRunning'
        query = urlencode((
            ('meetingID', self.meeting_id),
        ))
        hashed = self.api_call(query, call)
        url = settings.BBB_API_URL + call + '?' + hashed
        result = parse_xml(urlopen(url).read())
        if result:
            return result.find('running').text
        else:
            return 'error'

    def meeting_info(self, meeting_id, password):
        call = 'getMeetingInfo'
        query = urlencode((
            ('meetingID', meeting_id),
            ('password', password),
        ))
        hashed = self.api_call(query, call)
        url = settings.BBB_API_URL + call + '?' + hashed
        r = parse_xml(urlopen(url).read())
        if r:
            # Create dict of values for easy use in template
            d = {
                'start_time': r.find('startTime').text,
                'end_time': r.find('endTime').text,
                'participant_count': r.find('participantCount').text,
                'moderator_count': r.find('moderatorCount').text,
                'moderator_password': r.find('moderatorPassword').text,
                'attendee_password': r.find('attendeePassword').text,
                'invite_url': reverse('join', args=[meeting_id]),
            }
            return d
        else:
            return None

    def get_meetings(self):
        """ Will return list of running meetings. """
        call = 'getMeetings'
        query = urlencode((
            ('random', 'random'),
        ))
        hashed = self.api_call(query, call)
        url = settings.BBB_API_URL + call + '?' + hashed
        result = parse_xml(requests.get(url).content)
        # Create dict of values for easy use in template
        d = []
        if result:
            r = result[1].findall('meeting')
            for m in r:
                meeting_id = m.find('meetingID').text
                password = m.find('moderatorPassword').text
                d.append({
                    'meeting_id': meeting_id,
                    'running': m.find('running').text,
                    'moderator_password': password,
                    'attendee_password': m.find('attendeePassword').text,
                    'info': self.meeting_info(
                        meeting_id,
                        password
                    )
                })
        return d

    def join_url(self, meeting_id, name, password):
        call = 'join'
        query = urlencode((
            ('fullName', name),
            ('meetingID', meeting_id),
            ('password', password),
        ))
        hashed = self.api_call(query, call)
        url = settings.BBB_API_URL + call + '?' + hashed
        return url

    def end_meeting(self, meeting_id, password):
        call = 'end'
        query = urlencode((
            ('meetingID', meeting_id),
            ('password', password),
        ))
        hashed = self.api_call(query, call)
        url = settings.BBB_API_URL + call + '?' + hashed
        result = parse_xml(urlopen(url).read())
        if result:
            pass
        else:
            return 'error'

    def start(self):
        call = 'create' 
        voicebridge = 70000 + random.randint(0,9999)
        query = urlencode((
            ('name', self.name),
            ('meetingID', self.meeting_id),
            ('attendeePW', self.attendee_password),
            ('moderatorPW', self.moderator_password),
            ('voiceBridge', voicebridge),
            ('welcome', "Welcome!"),
        ))
        print(query)
        hashed = self.api_call(query, call)
        print(hashed)
        url = settings.BBB_API_URL + call + '?' + hashed
        print(url)
        result = parse_xml(urlopen(url).read())
        print(result)
        if result:
            return result
        else:
            return "error"