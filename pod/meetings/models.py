from datetime import datetime
from hashlib import sha1
import hashlib
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

from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from pod.authentication.models import AccessGroup
from django.db.models import Q

from pod.meetings.utils import parse_xml


RESTRICT_EDIT_MEETING_ACCESS_TO_STAFF_ONLY = getattr(
    settings, "RESTRICT_EDIT_MEETING_ACCESS_TO_STAFF_ONLY", False
)

def select_meeting_owner():
    if RESTRICT_EDIT_MEETING_ACCESS_TO_STAFF_ONLY:
        return lambda q: (
            Q(is_staff=True) & (Q(first_name__icontains=q) | Q(last_name__icontains=q))
        ) & Q(owner__sites=Site.objects.get_current())
    else:
        return lambda q: (Q(first_name__icontains=q) | Q(last_name__icontains=q)) & Q(
            owner__sites=Site.objects.get_current()
        )

class Meetings(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name=_('Title')
    )
    '''
    meeting_id = models.CharField(
        max_length=110,
        verbose_name=_('Meeting ID')
    )
    '''
    meetingID = models.SlugField(
        _("meetingID"),
        unique=True, #le unique doit se faire sur la pair slug/site
        max_length=110,
        help_text=_(
            'Used to access this instance, the "meetingID" is '
            "a short label containing only letters, "
            "numbers, underscore or dash top."
        ),
        editable=False,
    )
    # sites doit etre en foreign key, pas en many to many, il n'y a pas d'interet à ce qu'une reunion soit sur pls sites. du coup, sans "s"
    site = models.ForeignKey(
        Site,
        null= True, 
        blank=True,
        on_delete=models.CASCADE
    )
    
    owner = models.ForeignKey(
        User,
        verbose_name=_('Owner'),
        null= True, 
        blank=True,
        on_delete=models.CASCADE
    )
        
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
        # help_text=_("Start date of the meeting."),
    )
    
    end_date = models.DateTimeField(
        _("End date"),
        default=timezone.now,
        null=True,
        blank=True,
        # help_text=_("End date of the meeting."),
    )

    attendeePW = models.CharField(
        max_length=50,
        verbose_name=_('Attendee password')
    )

    moderatorPW = models.CharField(
        max_length=50,
        verbose_name=_('Moderator password')
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
        verbose_name=_("Using a password"),
        # help_text=_('If this box is checked, ''the meeting will only be accessible after giving the attendee password. Except for owner and additionnal owner.'),
        default=True)

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
        verbose_name=_('Auto Save')
    )

    allow_start_stop_recording = models.BooleanField(
        default=True,
        verbose_name=_('Start/Stop button for recording the meeting'),
        # help_text=_('Allow the user to start/stop recording. (default true)')
    )

    webcam_only_for_moderators = models.BooleanField(
        default=False,
        verbose_name=_('Webcam Only for moderators?'),
        # help_text=_('will cause all webcams shared by viewers ''during this meeting to only appear for moderators')
    )

    lock_settings_disable_cam = models.BooleanField(
        default=False,
        verbose_name=_('Disable the camera'),
        # help_text=_('will prevent users from sharing their camera in the meeting')
    )

    lock_settings_disable_mic = models.BooleanField(
        default=False,
        verbose_name=_('Disable the mic'),
        # help_text=_('will only allow user to join listen only')
    )

    lock_settings_disable_private_chat = models.BooleanField(
        default=False,
        verbose_name=_('Disable Private Chat'),
        # help_text=_('if True will disable private chats in the meeting')
    )

    lock_settings_disable_public_chat = models.BooleanField(
        default=False,
        verbose_name=_('Disable Public Chat'),
        # help_text=_('if True will disable public chat in the meeting')
    )

    lock_settings_disable_note = models.BooleanField(
        default=False,
        verbose_name=_('Disable Notes'),
        # help_text=_('if True will disable notes in the meeting.')
    )

    lock_settings_locked_layout = models.BooleanField(
        default=False,
        verbose_name=_('Blocking meeting layout'),
        # help_text=_('will lock the layout in the meeting. ')
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

    @classmethod
    def api_call(self, query, call):
        checksum_val = sha1(str(call + query + BBB_SECRET_KEY).encode('utf-8')).hexdigest()
        result = "%s&checksum=%s" % (query, checksum_val)
        return result

    def is_running(self):
        call = 'isMeetingRunning'
        query = urlencode((
            ('meetingID', "%s" % self.meetingID),
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
            ('meetingID', "%s" % self.meetingID),
            ('password', "%s" % self.moderatorPW),
        ))
        hashed = self.api_call(query, call)
        url = BBB_API_URL + call + '?' + hashed
        req = requests.get(url)
        result = parse_xml(req.content)
        if result:
            return True
        return False
   
    def meeting_info(self, meetingID, password):
        call = 'getMeetingInfo'
        query = urlencode((
            ('meetingID', "%s" % meetingID),
            ('password', "%s" % password),
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
                'moderatorPW': result.find('moderatorPW').text,
                'attendeePW': result.find('attendeePW').text,
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
                    'moderatorPW': password,
                    'attendeePW': m.find('attendeePW').text,
                    'info': self.meeting_info(
                        meetingID,
                        password
                    )
                })
            return d
        else:
            return 'error'

        

    def join_url(self, name, password):
        call = 'join'
        parameters = {
            'meetingID': "%s" % self.meetingID,
            'fullName': name,
            'password': password,
        }
        query = urlencode(parameters)
        hashed = self.api_call(query, call)
        url = BBB_API_URL + call + '?' + hashed
        return url

    def create(self):
        # http://test-install.blindsidenetworks.com/bigbluebutton/api/create?allowStartStopRecording=true&attendeePW=ap&autoStartRecording=false&meetingID=random-9046073&moderatorPW=mp&name=random-9046073&record=false&voiceBridge=70809&welcome=%3Cbr%3EWelcome+to+%3Cb%3E%25%25CONFNAME%25%25%3C%2Fb%3E%21&checksum=7ab9312324878b2194f7af9db64ee16ca73fe045
        call="create"
        voicebridge = 70000 + random.randint(0,9999)
        field_to_exclude = ["id", "running", "start_date", "end_date", "max_participants", "record", "parent_meeting_id", "internal_meeting_id", "voice_bridge", "welcome_text", "owner", "additional_owners", "sites", "logout_url", "auto_start_recording", "allow_start_stop_recording", "webcam_only_for_moderators", "lock_settings_disable_cam", "lock_settings_disable_mic", "lock_settings_disable_private_chat", "lock_settings_disable_public_chat", "lock_settings_disable_note", "lock_settings_locked_layout", "ask_password", "restrict_access_to_groups", "is_restricted", "is_draft"] 
        parameters={}
        for field in self._meta.get_fields():
            print(field.name)
            if field.name not in field_to_exclude:
                parameters.update({
                    field.name: getattr(self, field.name),
                })
        print("CREATE ----------------------------")
        print(parameters)
        query = urlencode(parameters)
        print(query)
        hashed = self.api_call(query, call)
        print(hashed)
        url = BBB_API_URL + call + '?' + hashed
        print(url)
        result = parse_xml(requests.get(url).content.decode('utf-8'))
        # recuperer les mots de passes pour mettre à jour la conf
        # attendeePW et moderatorPW
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