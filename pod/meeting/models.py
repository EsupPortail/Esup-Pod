import hashlib
import random
import requests
from django.utils.dateparse import parse_duration
import os
import base64

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
from django.templatetags.static import static
from django.urls import reverse
from django.utils.html import mark_safe
from django.shortcuts import get_object_or_404

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.core.validators import MinLengthValidator
from django.db.models import F, Q

from html.parser import HTMLParser
import shutil
from pod.video.models import Video
from pod.video.models import Type

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

if getattr(settings, "USE_PODFILE", False):
    from pod.podfile.models import CustomFileModel
else:
    from pod.main.models import CustomFileModel

SECRET_KEY = getattr(settings, "SECRET_KEY", "")
BBB_API_URL = getattr(settings, "BBB_API_URL", "")
BBB_SECRET_KEY = getattr(settings, "BBB_SECRET_KEY", "")
BBB_LOGOUT_URL = getattr(settings, "BBB_LOGOUT_URL", "")
MEETING_PRE_UPLOAD_SLIDES = getattr(settings, "MEETING_PRE_UPLOAD_SLIDES", "")
STATIC_ROOT = getattr(settings, "STATIC_ROOT", "")
TEST_SETTINGS = getattr(settings, "TEST_SETTINGS", False)

DEFAULT_TYPE_ID = getattr(settings, "DEFAULT_TYPE_ID", 1)

VIDEO_ALLOWED_EXTENSIONS = getattr(
    settings,
    "VIDEO_ALLOWED_EXTENSIONS",
    (
        "3gp",
        "avi",
        "divx",
        "flv",
        "m2p",
        "m4v",
        "mkv",
        "mov",
        "mp4",
        "mpeg",
        "mpg",
        "mts",
        "wmv",
        "mp3",
        "ogg",
        "wav",
        "wma",
        "webm",
        "ts",
    ),
)

__MEETING_SLIDES_DOCUMENT__ = """<modules>
   <module name="presentation">
      %(document)s
   </module>
</modules>
"""


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

    name = models.CharField(
        max_length=250, verbose_name=_("Meeting Name"), validators=[MinLengthValidator(2)]
    )
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
    slides = models.ForeignKey(
        CustomFileModel,
        null=True,
        blank=True,
        verbose_name=_("Slides"),
        help_text=_(
            """
        BigBlueButton will accept Office documents (.doc .docx .pptx),
        text documents(.txt), images (.png ,.jpg) and Adobe Acrobat documents (.pdf);
        we recommend converting documents to .pdf prior to uploading for best results.
        Maximum size is 30 MB or 150 pages per document.
        """
        ),
        on_delete=models.CASCADE,
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

    # ##############################    Upload BBB recordings to Pod
    def parse_remote_file(self, source_html_url):
        """Parse the remote HTML file on the BBB server.
        In this HTML page, we found a reference to the video recording.
        This function returns the name of the video and of the recording.
        If not, an exception is raised."""
        try:
            response = requests.get(source_html_url)
            if response.status_code != 200:
                msg = {}
                msg["error"] = _(
                    "The HTML file for this recording was not found on the BBB server."
                )
                # If we want to display the 404/500... page to the user
                # msg["message"] = response.content.decode("utf-8")
                msg["message"] = "Error number : %s" % response.status_code
                raise ValueError(msg)

            # Parse the BBB video HTML file
            parser = video_parser()
            # Manage the encoding
            if response.encoding == "ISO-8859-1":
                parser.feed(response.text.encode("ISO-8859-1").decode("utf-8"))
            else:
                parser.feed(response.text)

            # Video file found
            if parser.video_check:
                # Security check about extensions
                extension = parser.video_file.split(".")[-1].lower()
                if extension not in VIDEO_ALLOWED_EXTENSIONS:
                    msg = {}
                    msg["error"] = _(
                        "The video file for this recording was not"
                        " found in the HTML file."
                    )
                    msg["message"] = _("The found file is not a valid video.")
                    raise ValueError(msg)

                # Returns the name of the video (if necessary, title is parser.title)
                return parser.video_file
            else:
                msg = {}
                msg["error"] = _(
                    "The video file for this recording was not found in the HTML file."
                )
                msg["message"] = "No video file found"
                raise ValueError(msg)
        except Exception as exc:
            msg = {}
            msg["error"] = _(
                "The video file for this recording was not found in the HTML file."
            )
            msg["message"] = exc
            raise ValueError(msg)

    def download_video_file(self, source_video_url, dest_file):
        """Download BBB video file"""
        # Check if video file exists
        try:
            with requests.get(
                source_video_url, timeout=(10, 180), stream=True
            ) as response:
                if response.status_code != 200:
                    msg = {}
                    msg["error"] = _(
                        "The video file for this recording "
                        "was not found on the BBB server."
                    )
                    # If we want to display the 404/500... page to the user
                    # msg["message"] = response.content.decode("utf-8")
                    msg["message"] = "Error number : %s" % response.status_code
                    raise ValueError(msg)

                with open(dest_file, "wb+") as file:
                    # Total size, in bytes, from response header
                    # total_size = int(response.headers.get('content-length', 0))
                    # Other possible methods
                    # Method 1 : iterate over every chunk and calculate % of total
                    # for chunk in response.iter_content(chunk_size=1024*1024):
                    #    file.write(chunk)
                    # Method 2 : Binary download
                    # file.write(response.content)
                    # Method 3 : The fastest
                    shutil.copyfileobj(response.raw, file)
        except Exception as exc:
            msg = {}
            msg["error"] = _("Impossible to download the video file from the BBB server.")
            msg["message"] = exc
            raise ValueError(msg)

    def save_video(self, request, dest_file, recording_name):
        """Save and encode the Pod video file"""
        try:
            video = Video.objects.create(
                video=dest_file,
                title=recording_name,
                owner=request.user,
                description=_(
                    "This video was uploaded to Pod from Big Blue Button server."
                ),
                is_draft=True,
                type=Type.objects.get(id=DEFAULT_TYPE_ID),
            )

            video.launch_encode = True
            video.save()
        except Exception as exc:
            msg = {}
            msg["error"] = _("Impossible to create the Pod video")
            msg["message"] = exc
            raise ValueError(msg)

    def save_recording(self, request, meeting_id, recording_id, recording_name):
        """Save the recording in database"""
        try:
            meeting = get_object_or_404(
                Meeting, meeting_id=meeting_id, site=get_current_site(request)
            )
            # Convert timestamp to datetime
            start_timestamp = request.POST.get("start_timestamp")
            end_timestamp = request.POST.get("end_timestamp")
            start_dt = dt.fromtimestamp(float(start_timestamp) / 1000)
            end_dt = dt.fromtimestamp(float(end_timestamp) / 1000)
            # Format datetime and not timestamp
            start_at = start_dt.strftime("%Y-%m-%d %H:%M:%S")
            # Management of the duration
            duration = str(end_dt - start_dt).split(".")[0]
            # Save the recording as an internal recording
            recording, created = Recording.objects.update_or_create(
                name=recording_name,
                is_internal=True,
                recording_id=recording_id,
                meeting=meeting,
                start_at=start_at,
                duration=parse_duration(duration),
                # Create a new line if uploaded by another user
                defaults={"uploaded_to_pod_by": request.user},
            )
        except Exception as exc:
            msg = {}
            msg["error"] = _("Impossible to create the recording")
            msg["message"] = exc
            raise ValueError(msg)

    def upload_recording_to_pod(self, request, meeting_id, recording_id):
        """Upload recording to Pod (main function)"""
        try:
            # Manage source URL from video playback
            source_url = request.POST.get("source_url")
            if source_url != "":
                # Step 1 : Download and parse the remote HTML file if necessary
                # Check if extension is a video extension
                extension = source_url.split(".")[-1].lower()
                if extension in VIDEO_ALLOWED_EXTENSIONS:
                    # URL corresponds to a video file
                    source_video_url = source_url
                else:
                    # Download and parse the remote HTML file
                    video_file = self.parse_remote_file(source_url)
                    source_video_url = source_url + video_file

                # Step 2 : Define destination source file
                extension = source_video_url.split(".")[-1].lower()
                dest_file = os.path.join(
                    settings.MEDIA_ROOT,
                    "videos",
                    request.user.owner.hashkey,
                    os.path.basename(recording_id + "." + extension),
                )
                os.makedirs(os.path.dirname(dest_file), exist_ok=True)

                # Step 3 : Download the video file
                self.download_video_file(source_video_url, dest_file)

                # Step 4 : Save and encode Pod video
                recording_title = request.POST.get("recording_name")
                self.save_video(request, dest_file, recording_title)

                # Step 5 : Save informations about the recording
                self.save_recording(request, meeting_id, recording_id, recording_title)

                return True
            else:
                msg = {}
                msg["error"] = _("Impossible to upload to Pod the video")
                msg["message"] = _("No URL found")
                raise ValueError(msg)
        except Exception as exc:
            msg = {}
            msg["error"] = _("Impossible to upload to Pod the video")
            try:
                # Management of error messages from sub-functions
                message = "%s (%s)" % (exc.args[0]["error"], exc.args[0]["message"])
            except Exception:
                # Management of error messages in all cases
                message = exc

            message = mark_safe(message)
            msg["message"] = message
            raise ValueError(msg)

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
        response = self.get_create_response(url)
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

    def get_create_response(self, url):
        """call BBB server in POST or GET"""
        if self.slides:
            slides_path = self.slides.file.path
        elif MEETING_PRE_UPLOAD_SLIDES != "":
            slides_path = os.path.join(STATIC_ROOT, MEETING_PRE_UPLOAD_SLIDES)
        else:
            return requests.get(url)
        doc_str = ""
        if os.path.getsize(slides_path) > 1000000:  # more than 1MO
            doc_url = self.get_doc_url()
            doc_str = '<document url="%(url)s" filename="presentation.pdf"/>' % {
                "url": doc_url
            }
        else:
            base64_str = ""
            with open(slides_path, "rb") as slides_file:
                encoded_string = base64.b64encode(slides_file.read())
                base64_str = encoded_string.decode("utf-8")
            doc_str = '<document name="presentation.pdf">%(file)s</document>' % {
                "file": base64_str
            }
        headers = {"Content-Type": "application/xml"}
        response = requests.post(
            url, data=__MEETING_SLIDES_DOCUMENT__ % {"document": doc_str}, headers=headers
        )
        return response

    def get_doc_url(self):
        """return the url of slides to preload"""
        slides_url = ""
        if self.slides:
            slides_url = "".join(
                [
                    "https://",
                    get_current_site(None).domain,
                    self.slides.file.url,
                ]
            )
        elif MEETING_PRE_UPLOAD_SLIDES != "":
            slides_url = "".join(
                [
                    "https://",
                    get_current_site(None).domain,
                    static(MEETING_PRE_UPLOAD_SLIDES),
                ]
            )
        return slides_url

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
            msg["error"] = _("Unable to end meeting!")
            msg["returncode"] = meeting_json.get("returncode", "")
            msg["messageKey"] = meeting_json.get("messageKey", "")
            msg["message"] = meeting_json.get("message", "")
            raise ValueError(msg)
        else:
            return True

    def get_recordings(self):
        action = "getRecordings"
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
            msg["error"] = _("Unable to get meeting recordings!")
            msg["returncode"] = meeting_json.get("returncode", "")
            msg["messageKey"] = meeting_json.get("messageKey", "")
            msg["message"] = meeting_json.get("message", "")
            raise ValueError(msg)
        else:
            return meeting_json

    def delete_recording(self, record_id):
        action = "deleteRecordings"
        parameters = {}
        parameters["recordID"] = record_id
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
            msg["error"] = _("Unable to delete recording!")
            msg["returncode"] = meeting_json.get("returncode", "")
            msg["messageKey"] = meeting_json.get("messageKey", "")
            msg["message"] = meeting_json.get("message", "")
            raise ValueError(msg)
        else:
            return True

    @staticmethod
    def get_all_meetings():
        action = "getMeetings"
        parameters = {}
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
            msg["error"] = _("Unable to get meeting recordings!")
            msg["returncode"] = meeting_json.get("returncode", "")
            msg["messageKey"] = meeting_json.get("messageKey", "")
            msg["message"] = meeting_json.get("message", "")
            raise ValueError(msg)
        else:
            return meeting_json

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


class Recording(models.Model):
    """This model hold information about Big Blue Button recordings.
    This model is for internal or external recordings.
    For internal recordings : only BBB recordings that have been uploaded to
    Pod are saved in the database.
    For external recordings : all recordings are saved in the database.
    """

    """ For all recording """
    name = models.CharField(max_length=250, verbose_name=_("Recording name"))

    # Type of recording : Internal / External
    is_internal = models.BooleanField(
        verbose_name=_("Is this an internal recording ?"),
        default=True,
    )

    start_at = models.DateTimeField(_("Start date"), default=timezone.now)

    duration = models.DurationField(
        verbose_name=_("Duration of recording"),
        null=True,
        blank=True,
    )

    # User who uploaded to Pod the video file
    uploaded_to_pod_by = models.ForeignKey(
        User,
        related_name="uploader_recording",
        on_delete=models.CASCADE,
        limit_choices_to={"is_staff": True},
        verbose_name=_("User"),
        null=True,
        blank=True,
        help_text=_("User who uploaded to Pod the video file"),
    )

    """ For internal recording """
    # Recording id (BBB format)
    recording_id = models.SlugField(
        max_length=255,
        verbose_name=_("Recording ID"),
        null=True,
        blank=True,
    )

    # Existant meeting
    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        verbose_name=_("Meeting"),
        null=True,
        blank=True,
    )

    """ For external recording """
    # External URL (source video URL)
    external_url = models.CharField(
        max_length=500,
        default="",
        null=True,
        blank=True,
        verbose_name=_("External recording URL"),
    )

    upload_automatically = models.BooleanField(
        default=False,
        null=True,
        blank=True,
        verbose_name=_("Upload automatically to Pod as a video"),
        help_text=_(
            "A video will be created from this external recording"
            "and will be available on this platform automatically."
        ),
    )

    # User who create this external recording
    created_by = models.ForeignKey(
        User,
        related_name="creator_recording",
        on_delete=models.CASCADE,
        limit_choices_to={"is_staff": True},
        verbose_name=_("User"),
        null=True,
        blank=True,
        help_text=_("User who create this external recording"),
    )

    # Additional owners for this external recording
    additional_owners = models.ManyToManyField(
        User,
        related_name="owners_recordings",
        limit_choices_to={"is_staff": True},
        verbose_name=_("Additional owners"),
        blank=True,
        help_text=_("You can add additional owners to this external recording."),
    )

    def __unicode__(self):
        return "%s - %s" % (self.recording_id, self.name)

    def __str__(self):
        return "%s - %s" % (self.recording_id, self.name)

    def save(self, *args, **kwargs):
        super(Recording, self).save(*args, **kwargs)

    class Meta:
        db_table = "recording"
        verbose_name = "Recording"
        verbose_name_plural = _("Recordings")
        ordering = ("-start_at",)
        get_latest_by = "start_at"


class StatelessRecording:
    """Recording model, not saved in database.
    Useful to manage BBB recordings.
    """

    recordID = ""
    playback = {}
    name = ""
    state = ""
    startTime = ""
    endTime = ""
    # Source URL for the video presentation
    sourceURL = ""
    # Rights
    canUpload = False
    canDelete = False
    # User that has uploaded this recording to Pod
    uploadedToPodBy = ""

    def __init__(self, recordID, name, state):
        self.recordID = recordID
        self.name = name
        self.state = state

    def add_playback(self, type, url):
        self.playback[type] = url
        if type == "video":
            self.sourceURL = url

    def get_start_time(self):
        # BBB epoch in milliseconds
        return dt.fromtimestamp(float(self.startTime) / 1000)

    def get_end_time(self):
        # BBB epoch in milliseconds
        return dt.fromtimestamp(float(self.endTime) / 1000)

    def get_duration(self):
        return str(self.get_end_time() - self.get_start_time()).split(".")[0]


class video_parser(HTMLParser):
    """Useful to parse the BBB Web page and search for video file
    Used to parse BBB 2.6 URL for video recordings.
    """

    def __init__(self):
        super().__init__()
        self.reset()
        # Variables for title
        self.title_check = False
        self.title = ""
        # Variables for video file
        self.video_check = False
        self.video_file = ""
        self.video_type = ""

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        # Search for source tag
        if tag == "source":
            # Found the line. Managed format :
            # attrs = {'src': 'video-0.m4v', 'type': 'video/mp4'}
            # print("video line : %s" % attrs)
            self.video_check = True
            self.video_file = attrs.get("src", "")
            self.video_type = attrs.get("type", "")
        # Search for title tag
        if tag == "title":
            # Found the title line
            self.title_check = True

    def handle_data(self, data):
        # Search for title tag
        if self.title_check:
            # Get the title that corresponds to recording's name
            self.title = data
            self.title_check = False
