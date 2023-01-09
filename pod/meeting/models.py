import hashlib
import random
import requests
from datetime import timedelta, datetime as dt

from urllib.parse import urlencode
import xml.etree.ElementTree as et

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.contrib.sites.models import Site
from django.contrib.auth.models import User
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.template.defaultfilters import slugify
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db.models import F, Q

from pod.authentication.models import AccessGroup
from pod.main.models import get_nextautoincrement

from .utils import (
    api_call,
    parseXmlToJson,
    slash_join,
    get_nth_week_number,
    get_weekday_in_nth_week,
)
from dateutil.relativedelta import relativedelta

SECRET_KEY = getattr(settings, "SECRET_KEY", "")
BBB_API_URL = getattr(settings, "BBB_API_URL", "")
BBB_SECRET_KEY = getattr(settings, "BBB_SECRET_KEY", "")
BBB_LOGOUT_URL = getattr(settings, "BBB_LOGOUT_URL", "")
TEST_SETTINGS = getattr(settings, "TEST_SETTINGS", False)


meeting_to_bbb = {
    "name": "name",
    "meetingID": "meeting_id",
    "attendeePW": "attendee_password",
    "moderatorPW": "moderator_password",
    "welcome": "welcome_text",
    # "dialNumber",
    "voiceBridge": "voice_bridge",
    "maxParticipants": "max_participants",
    "logoutURL": "logout_url",
    "record": "record",
    # "duration": "-",
    # "isBreakout",
    "parentMeetingID": "parent_meeting_id",
    # "sequence",
    # "freeJoin",
    # "breakoutRoomsEnabled",
    # "breakoutRoomsPrivateChatEnabled",
    # "breakoutRoomsRecord",
    # "meta",
    # "moderatorOnlyMessage",
    "autoStartRecording": "auto_start_recording",
    "allowStartStopRecording": "allow_start_stop_recording",
    "webcamsOnlyForModerator": "webcam_only_for_moderators",
    # "bannerText",
    # "bannerColor",
    # "muteOnStart",
    # "allowModsToUnmuteUsers",
    "lockSettingsDisableCam": "lock_settings_disable_cam",
    "lockSettingsDisableMic": "lock_settings_disable_mic",
    "lockSettingsDisablePrivateChat": "lock_settings_disable_private_chat",
    "lockSettingsDisablePublicChat": "lock_settings_disable_public_chat",
    "lockSettingsDisableNote": "lock_settings_disable_note",
    "lockSettingsLockedLayout": "lock_settings_locked_layout",
    # "lockSettingsLockOnJoin",
    # "lockSettingsLockOnJoinConfigurable",
    # "lockSettingsHideViewersCursor",
    # "guestPolicy",
    # "meetingKeepEvents",
    # "endWhenNoModerator",
    # "endWhenNoModeratorDelayInMinutes",
    # "meetingLayout",
    # "learningDashboardEnabled",
    # "learningDashboardCleanupDelayInMinutes",
    # "allowModsToEjectCameras",
    # "allowRequestsWithoutSession",
    # "userCameraCap",
    # "meetingCameraCap",
    # "meetingExpireIfNoUserJoinedInMinutes",
    # "meetingExpireWhenLastUserLeftInMinutes",
    # "groups",
    # "logo",
    # "disabledFeatures",
    # "preUploadedPresentationOverrideDefault"
}


def two_hours_hence():
    return timezone.now() + timezone.timedelta(hours=2)


def get_random():
    return 70000 + random.randint(0, 9999)


class Meeting(models.Model):
    """This models hold information about each meeting room.
    When creating a big blue button room with BBB APIs,
    Will store it's info here for later usages.
    // Recurring code come from
    // https://github.com/openfun/jitsi-magnify/blob/main/src/magnify/apps/core/models.py
    // Thanks to FUN Team for helping us
    """

    DAILY, WEEKLY, MONTHLY, YEARLY = "daily", "weekly", "monthly", "yearly"

    INTERVAL_CHOICES = (
        (DAILY, _("Daily")),
        (WEEKLY, _("Weekly")),
        (MONTHLY, _("Monthly")),
        (YEARLY, _("Yearly")),
    )

    DATE_DAY, NTH_DAY = "date_day", "nth_day"
    MONTHLY_TYPE_CHOICES = (
        (DATE_DAY, _("Every month on this date")),
        (NTH_DAY, _("Every month on the nth week, the same day of week")),
        # Every month on the nth week day of the month
    )

    weekdays_validator = RegexValidator(
        "^[0-6]{0,7}$",
        message=_("Weekdays must contain the numbers of the active days."),
    )

    name = models.CharField(max_length=250, verbose_name=_("Meeting Name"))
    meeting_id = models.SlugField(
        max_length=255,
        verbose_name=_("Meeting ID"),
        editable=False,
    )
    owner = models.ForeignKey(
        User,
        verbose_name=_("Owner"),
        related_name="owner_meeting",
        on_delete=models.CASCADE,
    )
    additional_owners = models.ManyToManyField(
        User,
        blank=True,
        verbose_name=_("Additional owners"),
        related_name="owners_meetings",
        help_text=_("You can add additional owners to the meeting."),
    )
    attendee_password = models.CharField(
        max_length=50, verbose_name=_("Attendee Password")
    )
    moderator_password = models.CharField(
        max_length=50, verbose_name=_("Moderator Password"), editable=False
    )

    start_at = models.DateTimeField(_("Start date"), default=timezone.now)
    expected_duration = models.DurationField(
        verbose_name=_("Meeting duration"),
        help_text=_("Specify the duration of the meeting."),
        default=timezone.timedelta(hours=2),
    )

    # recurrence
    recurrence = models.CharField(
        verbose_name=_("Custom recurrence"),
        help_text=_(
            "Specify the recurrence of the meeting : daily, weekly, monthly or yearly"
        ),
        max_length=10,
        choices=INTERVAL_CHOICES,
        null=True,
        blank=True,
    )
    frequency = models.PositiveIntegerField(
        verbose_name=_("Repeat each time"),
        default=1,
        help_text=_(
            "The meeting will be repeat each time of value specify."
            " i.e: each 3 days if recurring daily"
        ),
    )
    recurring_until = models.DateField(
        verbose_name=_("End date of recurring meeting"),
        help_text=_("Recurring meeting until the specified date"),
        null=True,
        blank=True,
    )
    nb_occurrences = models.PositiveIntegerField(
        verbose_name=_("Number of occurrences"),
        help_text=_("Recurring meeting until the specified number of occurrences"),
        null=True,
        blank=True,
    )
    weekdays = models.CharField(
        verbose_name=_("Day(s) of week for the meeting"),
        help_text=_("Recurring meeting each day(s) specified"),
        max_length=7,
        blank=True,
        null=True,
        validators=[weekdays_validator],
    )
    monthly_type = models.CharField(
        max_length=10, choices=MONTHLY_TYPE_CHOICES, default=DATE_DAY
    )

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
        verbose_name=_("Is running"),
        help_text=_("Indicates whether this meeting is running in BigBlueButton or not!"),
        editable=False,
    )
    site = models.ForeignKey(Site, verbose_name=_("Site"), on_delete=models.CASCADE)

    # #################### Configs
    max_participants = models.IntegerField(
        default=100, verbose_name=_("Max Participants")
    )
    welcome_text = models.TextField(
        default=_("Welcome!"), verbose_name=_("Meeting Text in Bigbluebutton")
    )
    logout_url = models.CharField(
        max_length=500,
        default="",
        null=True,
        blank=True,
        verbose_name=_("URL to visit after user logged out"),
    )
    webcam_only_for_moderators = models.BooleanField(
        default=False,
        verbose_name=_("Webcam Only for moderators?"),
        help_text=_(
            "Will cause all webcams shared by viewers "
            "during this meeting to only appear for moderators."
        ),
    )

    # #################### RECORD PART
    record = models.BooleanField(
        default=False,
        verbose_name=_("Active record"),
        help_text=_("Will active the recording of the meeting"),
    )
    auto_start_recording = models.BooleanField(
        default=False, verbose_name=_("Auto Start Recording")
    )
    allow_start_stop_recording = models.BooleanField(
        default=True,
        verbose_name=_("Allow Stop/Start Recording"),
        help_text=_("Allow the user to start/stop recording. (default true)"),
    )

    # #################### Lock settings
    lock_settings_disable_cam = models.BooleanField(
        default=False,
        verbose_name=_("Disable Camera"),
        help_text=_("Will prevent users from sharing their camera in the meeting."),
    )
    lock_settings_disable_mic = models.BooleanField(
        default=False,
        verbose_name=_("Disable Mic"),
        help_text=_("Will only allow user to join listen only."),
    )
    lock_settings_disable_private_chat = models.BooleanField(
        default=False,
        verbose_name=_("Disable Private chat"),
        help_text=_("If True, will disable private chats in the meeting."),
    )
    lock_settings_disable_public_chat = models.BooleanField(
        default=False,
        verbose_name=_("Disable public chat"),
        help_text=_("If True, will disable public chat in the meeting."),
    )
    lock_settings_disable_note = models.BooleanField(
        default=False,
        verbose_name=_("Disable Note"),
        help_text=_("If True, will disable notes in the meeting."),
    )
    lock_settings_locked_layout = models.BooleanField(
        default=False,
        verbose_name=_("Locked Layout"),
        help_text=_("Will lock the layout in the meeting."),
    )

    # Not important Info
    parent_meeting_id = models.CharField(
        null=True,
        blank=True,
        max_length=100,
        verbose_name=_("Parent Meeting ID"),
    )
    internal_meeting_id = models.CharField(
        null=True,
        blank=True,
        max_length=100,
        verbose_name=_("Internal Meeting ID"),
        editable=False,
    )
    voice_bridge = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Voice Bridge"),
        default=get_random,
    )
    bbb_create_time = models.CharField(
        null=True,
        blank=True,
        max_length=100,
        verbose_name=_("BBB Create Time"),
        editable=False,
    )

    # Time related Info
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "{}-{}".format("%04d" % self.id, self.name)

    @property
    def start(self):
        return self.start_at.date()

    @property
    def start_time(self):
        return self.start_at.time()

    def reset_recurrence(self):
        """
        Reset recurrence so everything indicates that the event occurs only once.
        Saving is left up to the caller.
        """
        self.recurrence = None
        self.weekdays = str(self.start.weekday())
        self.nb_occurrences = 1
        self.recurring_until = self.start

    def check_recurrence(self):  # noqa: C901
        """
        Compute the `recurring_until` field
        which is the date at which the recurrence ends.
        """
        if self.start and self.frequency:
            if self.recurrence == Meeting.WEEKLY:
                if self.weekdays is None:
                    self.reset_recurrence()

                if str(self.start.weekday()) not in self.weekdays:
                    raise ValidationError(
                        {
                            "weekdays": _(
                                "The day of the start date of the meeting must "
                                + "be included in the recurrence weekdays."
                            )
                        }
                    )
            else:
                self.weekdays = None
            if self.recurrence:
                if self.recurring_until:
                    if self.recurring_until < self.start:
                        self.recurring_until = self.start
                    all_occurrences = self.get_occurrences(
                        self.start, self.recurring_until
                    )
                    self.nb_occurrences = len(all_occurrences)
                    # Correct the date of end of recurrence
                    self.recurring_until = all_occurrences[-1]
                    if self.nb_occurrences <= 1:
                        self.reset_recurrence()

                elif self.nb_occurrences is not None:
                    if self.nb_occurrences <= 1:
                        self.reset_recurrence()
                    next_occurrence = self.start
                    for _i in range(self.nb_occurrences - 1):
                        next_occurrence = self.next_occurrence(next_occurrence)
                    self.recurring_until = next_occurrence
                # Infinite recurrence... do nothing
            else:
                self.reset_recurrence()
        else:
            self.reset_recurrence()

    def save(self, *args, **kwargs):
        """Store a video object in db."""
        self.check_recurrence()
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
            ("%s-%s-%s" % (SECRET_KEY, self.id, self.attendee_password)).encode("utf-8")
        ).hexdigest()

    # ##############################    Meeting occurences
    def next_occurrence_from_today(self):
        if self.start == timezone.now().date():
            # start_datetime = dt.combine(self.start, self.start_time)
            # start_datetime = timezone.make_aware(start_datetime)
            start_datetime = self.start_at + self.expected_duration
            if start_datetime > timezone.now():
                return self.start
        next_one = self.next_occurrence(self.start)
        while next_one < timezone.now().date():
            next_one = self.next_occurrence(next_one)
        return next_one

    def next_occurrence(self, current_date):  # noqa: C901
        """
        This method takes as assumption that the current date passed in argument
        IS a valid occurrence. If it is not the case, it will return an irrelevant date.
        Returns the next occurrence without consideration for the end of the recurrence.
        """
        if self.recurrence == Meeting.DAILY:
            return current_date + timedelta(days=self.frequency)

        if self.recurrence == Meeting.WEEKLY:
            increment = 1
            # Look in the current week
            weekday = current_date.weekday()
            while weekday + increment <= 6:
                if str(weekday + increment) in self.weekdays:
                    return current_date + timedelta(days=increment)
                increment += 1
            # Skip the weeks not covered by frequency
            next_date = (
                current_date
                + timedelta(days=increment)
                + timedelta(weeks=self.frequency - 1)
            )

            # Look in this week and be sure to find
            weekday = 0
            increment = 1
            while weekday + increment <= 6:
                if str(weekday + increment) in self.weekdays:
                    return next_date + timedelta(days=increment)
                increment += 1

            raise RuntimeError("You should have found the next weekly occurrence by now.")

        if self.recurrence == Meeting.MONTHLY:
            next_date = current_date + relativedelta(months=self.frequency)
            if self.monthly_type == Meeting.DATE_DAY:
                return next_date

            if self.monthly_type == Meeting.NTH_DAY:
                weekday = current_date.weekday()
                week_number = get_nth_week_number(current_date)
                return get_weekday_in_nth_week(
                    next_date.year, next_date.month, week_number, weekday
                )

            raise RuntimeError(
                "You should have found the next monthly occurrence by now."
            )

        if self.recurrence == Meeting.YEARLY:
            return current_date + relativedelta(years=self.frequency)

        raise RuntimeError("Non recurrent meetings don't have next occurences.")

    def get_occurrences(self, start, end=None):
        """
        Returns a list of occurrences for this meeting between start and end dates passed
        as arguments.
        """
        real_end = end or start
        if self.recurrence:
            if self.recurring_until and self.recurring_until < real_end:
                real_end = self.recurring_until

            occurrences = []
            new_start = self.start
            while new_start <= real_end:
                if new_start >= start:
                    occurrences.append(new_start)
                new_start = self.next_occurrence(new_start)
            return occurrences

        # check if event is in the period
        if self.start <= real_end and self.start + self.expected_duration >= start:
            return [self.start]

        return []

    @property
    def is_active(self):
        """
        Compute meeting to know if it is past or not.
        """
        start_datetime = self.start_at + self.expected_duration
        if self.recurrence is None and start_datetime > timezone.now():
            return True
        end_datetime = dt.combine(self.recurring_until, self.start_time)
        end_datetime = timezone.make_aware(end_datetime)
        end_datetime = end_datetime + self.expected_duration
        if self.recurrence and end_datetime > timezone.now():
            return True
        return False

    # ##############################    BBB API
    def create(self, request=None):
        action = "create"
        parameters = {}
        for param in meeting_to_bbb:
            if getattr(self, meeting_to_bbb[param], "") not in ["", None]:
                parameters.update(
                    {
                        param: getattr(self, meeting_to_bbb[param], ""),
                    }
                )
        # let duration and voiceBridge to default value
        if BBB_LOGOUT_URL == "":
            parameters["logoutURL"] = "".join(["https://", get_current_site(None).domain])
        else:
            parameters["logoutURL"] = BBB_LOGOUT_URL
        endCallbackUrl = "".join(
            [
                "https://",
                get_current_site(None).domain,
                reverse("meeting:end_callback", kwargs={"meeting_id": self.meeting_id}),
            ]
        )
        parameters["meta_endCallbackUrl"] = endCallbackUrl
        query = urlencode(parameters)
        hashed = api_call(query, action)
        url = slash_join(BBB_API_URL, action, "?%s" % hashed)
        response = requests.get(url)
        if response.status_code != 200:
            msg = {}
            msg["error"] = "Unable to call BBB server."
            msg["returncode"] = response.status_code
            msg["message"] = response.content.decode("utf-8")
            raise ValueError(msg)
        result = response.content.decode("utf-8")
        xmldoc = et.fromstring(result)
        meeting_json = {}
        for elt in xmldoc:
            meeting_json[elt.tag] = elt.text
        if meeting_json.get("returncode", "") != "SUCCESS":
            msg = {}
            msg["error"] = "Unable to create meeting ! "
            msg["returncode"] = meeting_json.get("returncode", "")
            msg["messageKey"] = meeting_json.get("messageKey", "")
            msg["message"] = meeting_json.get("message", "")
            raise ValueError(msg)
        else:
            self.update_data_from_bbb(meeting_json)
            return True

    def get_join_url(self, fullname, role, userID=""):
        """
        fullName  (required)
        meetingID  (required)
        password  (required)
        role  (required) : MODERATOR or VIEWER
        createTime
        userID
        """
        if role not in ["MODERATOR", "VIEWER"]:
            msg = {}
            msg[
                "error"
            ] = """
                Define user role for the meeting. Valid values are MODERATOR or VIEWER
            """
            msg["returncode"] = ""
            msg["messageKey"] = ""
            msg["message"] = ""
            raise ValueError(msg)
        action = "join"
        parameters = {}
        parameters["fullName"] = fullname
        parameters["meetingID"] = self.meeting_id
        parameters["role"] = role
        if role == "MODERATOR":
            parameters["password"] = self.moderator_password
        if role == "VIEWER":
            parameters["password"] = self.attendee_password
        if userID != "":
            parameters["userID"] = userID
        if self.bbb_create_time:
            parameters["createTime"] = self.bbb_create_time
        query = urlencode(parameters)
        hashed = api_call(query, action)
        url = slash_join(BBB_API_URL, action, "?%s" % hashed)
        return url

    def update_data_from_bbb(self, meeting_json):
        for key in meeting_json:
            if (
                key in meeting_to_bbb.keys()
                and getattr(self, meeting_to_bbb[key], "") != meeting_json[key]
            ):
                setattr(self, meeting_to_bbb[key], meeting_json[key])
        if meeting_json.get("internalMeetingID"):
            self.internal_meeting_id = meeting_json["internalMeetingID"]
        if meeting_json.get("createTime"):
            self.bbb_create_time = meeting_json["createTime"]
        self.is_running = True
        self.save()

    def get_is_meeting_running(self):
        if TEST_SETTINGS:
            return self.is_running
        action = "isMeetingRunning"
        parameters = {}
        parameters["meetingID"] = self.meeting_id
        query = urlencode(parameters)
        hashed = api_call(query, action)
        url = slash_join(BBB_API_URL, action, "?%s" % hashed)
        response = requests.get(url)
        if response.status_code != 200:
            msg = {}
            msg["error"] = "Unable to call BBB server."
            msg["returncode"] = response.status_code
            msg["message"] = response.content.decode("utf-8")
            raise ValueError(msg)
        result = response.content.decode("utf-8")
        xmldoc = et.fromstring(result)
        meeting_json = {}
        for elt in xmldoc:
            meeting_json[elt.tag] = elt.text
        if meeting_json.get("returncode", "") != "SUCCESS":
            msg = {}
            msg["error"] = "Unable to get meeting status ! "
            msg["returncode"] = meeting_json.get("returncode", "")
            msg["messageKey"] = meeting_json.get("messageKey", "")
            msg["message"] = meeting_json.get("message", "")
            raise ValueError(msg)
        else:
            status = True if meeting_json.get("running", False) == "true" else False
            self.is_running = status
            self.save()
            return status

    def get_meeting_info(self):
        action = "getMeetingInfo"
        parameters = {}
        parameters["meetingID"] = self.meeting_id
        query = urlencode(parameters)
        hashed = api_call(query, action)
        url = slash_join(BBB_API_URL, action, "?%s" % hashed)
        response = requests.get(url)
        if response.status_code != 200:
            msg = {}
            msg["error"] = "Unable to call BBB server."
            msg["returncode"] = response.status_code
            msg["message"] = response.content.decode("utf-8")
            raise ValueError(msg)
        result = response.content.decode("utf-8")
        xmldoc = et.fromstring(result)
        meeting_json = parseXmlToJson(xmldoc)
        if meeting_json.get("returncode", "") != "SUCCESS":
            msg = {}
            msg["error"] = "Unable to get meeting info ! "
            msg["returncode"] = meeting_json.get("returncode", "")
            msg["messageKey"] = meeting_json.get("messageKey", "")
            msg["message"] = meeting_json.get("message", "")
            raise ValueError(msg)
        else:
            return meeting_json

    def end(self):
        action = "end"
        parameters = {}
        parameters["meetingID"] = self.meeting_id
        parameters["password"] = self.moderator_password
        query = urlencode(parameters)
        hashed = api_call(query, action)
        url = slash_join(BBB_API_URL, action, "?%s" % hashed)
        response = requests.get(url)
        if response.status_code != 200:
            msg = {}
            msg["error"] = "Unable to call BBB server."
            msg["returncode"] = response.status_code
            msg["message"] = response.content.decode("utf-8")
            raise ValueError(msg)
        result = response.content.decode("utf-8")
        xmldoc = et.fromstring(result)
        meeting_json = {}
        for elt in xmldoc:
            meeting_json[elt.tag] = elt.text
        if meeting_json.get("returncode", "") != "SUCCESS":
            msg = {}
            msg["error"] = "Unable to end meeting ! "
            msg["returncode"] = meeting_json.get("returncode", "")
            msg["messageKey"] = meeting_json.get("messageKey", "")
            msg["message"] = meeting_json.get("message", "")
            raise ValueError(msg)
        else:
            return True

    class Meta:
        db_table = "meeting"
        verbose_name = "Meeting"
        verbose_name_plural = _("Meeting")
        ordering = ("-start_at",)
        get_latest_by = "start_at"
        constraints = [
            models.UniqueConstraint(
                fields=["meeting_id", "site"], name="meeting_unique_slug_site"
            ),
            models.CheckConstraint(
                check=Q(recurring_until__gte=F("start_at__date"))
                | Q(recurring_until__isnull=True),
                name="recurring_until_greater_than_start",
            ),
            models.CheckConstraint(check=Q(frequency__gte=1), name="frequency_gte_1"),
            models.CheckConstraint(
                check=Q(recurring_until__isnull=True, nb_occurrences__isnull=True)
                | Q(recurring_until__isnull=False, nb_occurrences__isnull=False),
                name="recurring_until_and_nb_occurrences_mutually_null_or_not",
            ),
        ]


@receiver(pre_save, sender=Meeting)
def default_site_meeting(sender, instance, **kwargs):
    if not hasattr(instance, "site"):
        instance.site = Site.objects.get_current()
    if instance.recurring_until and instance.start > instance.recurring_until:
        raise ValueError(_("Start date must be less than recurring until date"))
