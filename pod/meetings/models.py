from datetime import datetime
from hashlib import sha1
import random
import re
from urllib.parse import urlencode
from urllib.request import urlopen
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _
import requests
from pod.main.models import get_nextautoincrement
from django.template.defaultfilters import slugify

from django.contrib.sites.models import Site
from pod.authentication.models import AccessGroup



from pod.meetings.utils import parse_xml
BBB_SECRET_KEY = getattr(
    settings, "BBB_SECRET_KEY", "GOI6t9lAHdO996UiKWqIvjGNvHHVfA00hTRX2GBM"
)
BBB_API_URL = getattr(
    settings, "BBB_API_URL", "https://bbb-21-e.uphf.fr/bigbluebutton/api/"
)

User = get_user_model()

class Meetings(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name=_('Titre')
    )
    '''
    meeting_id = models.CharField(
        max_length=110,
        verbose_name=_('Meeting ID')
    )
    '''
    meetingID = models.SlugField(
        _("meetingID"),
        unique=True,
        max_length=110,
        help_text=_(
            'Used to access this instance, the "meetingID" is '
            "a short label containing only letters, "
            "numbers, underscore or dash top."
        ),
        editable=False,
    )
    sites = models.ManyToManyField(Site)
    
    owner = models.ForeignKey(
        User,
        verbose_name=_('Owner'),
        on_delete=models.CASCADE)
        
    additional_owners = models.ManyToManyField(
        User,
        blank=True,
        verbose_name=_("Additional owners"),
        related_name="owner_meetings",
        help_text=_(
            "You can add additional owners to the video. They will have the same rights as you except that they can't delete this video."
        ),
    )

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

    is_restricted = models.BooleanField(
        verbose_name=_("Restricted access"),
        help_text=_(
            'If this box is checked, '
            'the meeting will only be accessible to authenticated users.'),
        default=False)
        
    restrict_access_to_groups = models.ManyToManyField(
        AccessGroup, blank=True, verbose_name=_('Groups'),
        help_text=_('Select one or more groups who can access to this meeting'))
    
    ask_password = models.BooleanField(
        verbose_name=_("Utilisation d'un mot de passe"),
        help_text=_(
            'If this box is checked, '
            'the meeting will only be accessible after giving the attendee password. Except for owner and additionnal owner.'),
        default=True)

    running = models.BooleanField(
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
        verbose_name=_('Enregistrement Automatique')
    )

    allow_start_stop_recording = models.BooleanField(
        default=True,
        verbose_name=_('Bouton Start/Stop pour enregistrement de la réunion'),
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
        verbose_name=_('Désactiver la caméra'),
        help_text=_('will prevent users from sharing their camera in the meeting')
    )

    lock_settings_disable_mic = models.BooleanField(
        default=False,
        verbose_name=_('Désactiver le micro'),
        help_text=_('will only allow user to join listen only')
    )

    lock_settings_disable_private_chat = models.BooleanField(
        default=False,
        verbose_name=_('Désactiver le chat privé'),
        help_text=_('if True will disable private chats in the meeting')
    )

    lock_settings_disable_public_chat = models.BooleanField(
        default=False,
        verbose_name=_('Désactiver le chat publique'),
        help_text=_('if True will disable public chat in the meeting')
    )

    lock_settings_disable_note = models.BooleanField(
        default=False,
        verbose_name=_('Désactiver les notes'),
        help_text=_('if True will disable notes in the meeting.')
    )

    lock_settings_locked_layout = models.BooleanField(
        default=False,
        verbose_name=_('Blocage disposition réunion'),
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
        return "%s - %s" % (self.name, self.meetingID)

    class Meta:
        db_table = 'meetings'
        verbose_name = 'Meetings'
        verbose_name_plural = _('Meetings')

    def save(self, *args, **kwargs):
        newid = -1
        if not self.id:
            try:
                newid = get_nextautoincrement(Meetings)
            except Exception:
                try:
                    newid = Meetings.objects.latest("id").id
                    newid += 1
                except Exception:
                    newid = 1
        else:
            newid = self.id
        newid = "%04d" % newid
        self.meetingID = "%s-%s" % (newid, slugify(self.name))
        super(Meetings, self).save(*args, **kwargs)

    def api_call(self, query, call):
        checksum_val = sha1(str(call + query + BBB_SECRET_KEY).encode('utf-8')).hexdigest()
        result = "%s&checksum=%s" % (query, checksum_val)
        return result

    def is_running(self):
        call = 'isMeetingRunning'
        query = urlencode((
            ('meetingID', self.meetingID),
        ))
        hashed = self.api_call(query, call)
        url = BBB_API_URL + call + '?' + hashed
        result = parse_xml(requests.get(url).content)
        if result:
            return result.find('running').text
        else:
            return 'error'

    def end_meeting(self):
        call = 'end'
        query = urlencode((
            ('meetingID', self.meetingID),
            ('password', self.moderator_password),
        ))
        hashed = self.api_call(query, call)
        url = BBB_API_URL + call + '?' + hashed
        req = requests.get(url)
        result = parse_xml(req.content)
        if result:
            return True
        return False
        
    def meeting_info(self):
        call = 'getMeetingInfo'
        query = urlencode((
            ('meetingID', self.meetingID),
            ('password', self.moderator_password),
        ))
        hashed = self.api_call(query, call)
        url = BBB_API_URL + call + '?' + hashed
        result = parse_xml(requests.get(url).content)
        if result:
            d = {
                'start_time': result.find('startTime').text,
                'end_time': result.find('endTime').text,
                'participant_count': result.find('participantCount').text,
                'moderator_count': result.find('moderatorCount').text,
                'moderator_password': result.find('moderatorPW').text,
                'attendee_password': result.find('attendeePW').text,
                #'invite_url': reverse('join', args=[self.meetingID]),
            }
            return d
        else:
            return None

    def get_meetings(self):
        call = 'getMeetings'
        query = urlencode((
            ('random', 'random'),
        ))
        hashed = self.api_call(query, call)
        url = BBB_API_URL + call + '?' + hashed
        result = parse_xml(requests.get(url).content)
        if result:
            d = []
            result = result[1].findall('meeting')
            for m in result:
                meetingID = m.find('meetingID').text
                password = m.find('moderatorPW').text
                d.append({
                    'name': meetingID,
                    'running': m.find('running').text,
                    'moderator_pw': password,
                    'attendee_pw': m.find('attendeePW').text,
                })
            return d
        else:
            return 'error'

        '''
        'info': self.meeting_info(
            meetingID,
            password)
        '''

    def join_url(self, name, password):
        call = 'join'
        parameters={}
        parameters.update({
            'fullName': name,
            'meetingID': self.meetingID,
            'password': password,
        })
        query = urlencode(parameters)
        hashed = self.api_call(query, call)
        url = BBB_API_URL + call + '?' + hashed
        return url

    def create(self):
        call_api="create"
        voicebridge = 70000 + random.randint(0,9999)
        field_to_exclude = ["id", "running", "parent_meeting_id", "internal_meeting_id", "voice_bridge", "welcome_text", "owner", "additional_owners", "sites", "logout_url", "auto_start_recording", "allow_start_stop_recording", "webcam_only_for_moderators", "lock_settings_disable_cam", "lock_settings_disable_mic", "lock_settings_disable_private_chat", "lock_settings_disable_public_chat", "lock_settings_disable_note", "lock_settings_locked_layout"] 
        parameters={}
        for field in self._meta.get_fields():
            print(field.name)
            if field.name not in field_to_exclude:
                parameters.update({
                    field.name: getattr(self, field.name),
                })
        print(parameters)
        query = urlencode(parameters)
        print(query)
        hashed = self.api_call(query, call_api)
        print(hashed)
        url = BBB_API_URL + call_api + '?' + hashed
        print(url)
        result = parse_xml(requests.get(url).content.decode('utf-8'))
        print(result)
        if result:
            return result
        else:
            return "error"
        '''
        parameters={}
        parameters.update({"name":self.name}),
        parameters.update({"meetingID":self.meetingID}),
        parameters.update({"start_date":self.start_date}),
        parameters.update({"end_date":self.end_date}),
        parameters.update({"attendeePW":self.attendee_password}),
        parameters.update({"moderatorPW":self.moderator_password})
        parameters.update({"maxParticipants":self.max_participants})
        parameters.update({"record":self.record}),
        parameters.update({"autoStartRecording":self.auto_start_recording}),
        parameters.update({"allowStartStopRecording":self.allow_start_stop_recording}),
        parameters.update({"lock_settings_disable_cam":self.lock_settings_disable_cam}),
        parameters.update({"lock_settings_disable_mic":self.lock_settings_disable_mic}),
        parameters.update({"lock_settings_disable_private_chat":self.lock_settings_disable_private_chat}),
        parameters.update({"lock_settings_disable_public_chat":self.lock_settings_disable_public_chat}),
        parameters.update({"lock_settings_disable_note":self.lock_settings_disable_note}),
        parameters.update({"lock_settings_locked_layout":self.lock_settings_locked_layout}),
        query = urlencode(parameters)

        '''
        ('attendeePW', self.attendee_password),
        ('moderatorPW', self.moderator_password),
        ('voiceBridge', voicebridge),
        ('welcome', "Welcome!"),
        '''
        
        print(query)
        hashed = self.api_call(query, call_api)
        print(hashed)
        url = BBB_API_URL + call_api + '?' + hashed
        print(url)
        result = parse_xml(requests.get(url).content.decode('utf-8'))
        print(result)
        if result:
            return result
        else:
            return "error"
        '''