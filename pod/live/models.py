"""Esup-Pod "live" models."""
import base64
import hashlib
import io
import qrcode
import os

from ckeditor.fields import RichTextField
from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.contrib.sites.shortcuts import get_current_site
from django.templatetags.static import static
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from pod.main.lang_settings import ALL_LANG_CHOICES as __ALL_LANG_CHOICES__
from pod.main.lang_settings import PREF_LANG_CHOICES as __PREF_LANG_CHOICES__
from django.utils.translation import get_language
from pod.authentication.models import AccessGroup
from pod.main.models import get_nextautoincrement
from pod.video.models import Video, Type

SECURE_SSL_REDIRECT = getattr(settings, "SECURE_SSL_REDIRECT", False)

if getattr(settings, "USE_PODFILE", False):
    from pod.podfile.models import CustomImageModel
else:
    from pod.main.models import CustomImageModel

DEFAULT_THUMBNAIL = getattr(settings, "DEFAULT_THUMBNAIL", "img/default.svg")
DEFAULT_EVENT_THUMBNAIL = getattr(
    settings, "DEFAULT_EVENT_THUMBNAIL", "img/default-event.svg"
)
DEFAULT_EVENT_TYPE_ID = getattr(settings, "DEFAULT_EVENT_TYPE_ID", 1)
AFFILIATION_EVENT = getattr(
    settings, "AFFILIATION_EVENT", ("faculty", "employee", "staff")
)
SECRET_KEY = getattr(settings, "SECRET_KEY", "")

LANG_CHOICES = getattr(
    settings,
    "LANG_CHOICES",
    ((" ", __PREF_LANG_CHOICES__), ("----------", __ALL_LANG_CHOICES__)),
)
MEDIA_URL = getattr(settings, "MEDIA_URL", "/media/")
LIVE_TRANSCRIPTIONS_FOLDER = getattr(
    settings, "LIVE_TRANSCRIPTIONS_FOLDER", "live_transcripts"
)
MEDIA_ROOT = getattr(settings, "MEDIA_ROOT", None)


class Building(models.Model):
    name = models.CharField(_("name"), max_length=200, unique=True)
    headband = models.ForeignKey(
        CustomImageModel,
        models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_("Headband"),
    )
    gmapurl = models.CharField(max_length=250, blank=True, null=True)
    sites = models.ManyToManyField(Site)

    def __str__(self):
        return self.name

    def get_headband_url(self):
        if self.headband:
            return self.headband.file.url
        else:
            thumbnail_url = "".join([settings.STATIC_URL, DEFAULT_THUMBNAIL])
            return thumbnail_url

    class Meta:
        verbose_name = _("Building")
        verbose_name_plural = _("Buildings")
        ordering = ["name"]
        permissions = (("acces_live_pages", "Access to all live pages"),)


@receiver(post_save, sender=Building)
def default_site_building(sender, instance, created, **kwargs):
    if len(instance.sites.all()) == 0:
        instance.sites.add(Site.objects.get_current())


def get_available_broadcasters_of_building(user, building_id, broadcaster_id=None):
    right_filter = Broadcaster.objects.filter(
        Q(enable_add_event=True)
        & Q(building_id=building_id)
        & (Q(manage_groups__isnull=True) | Q(manage_groups__in=user.groups.all()))
    )
    if broadcaster_id:
        return (
            (right_filter | Broadcaster.objects.filter(Q(id=broadcaster_id)))
            .distinct()
            .order_by("name")
        )

    return right_filter.distinct().order_by("name")


def get_building_having_available_broadcaster(user, building_id=None):
    right_filter = Building.objects.filter(
        Q(broadcaster__enable_add_event=True)
        & (
            Q(broadcaster__manage_groups__isnull=True)
            | Q(broadcaster__manage_groups__in=user.groups.all())
        )
    )
    if building_id:
        return (
            (right_filter | Building.objects.filter(Q(id=building_id)))
            .distinct()
            .order_by("name")
        )

    return right_filter.distinct().order_by("name")


class Broadcaster(models.Model):
    name = models.CharField(_("name"), max_length=200, unique=True)
    slug = models.SlugField(
        _("Slug"),
        unique=True,
        max_length=200,
        help_text=_(
            'Used to access this instance, the "slug" is a short label '
            + "containing only letters, numbers, underscore or dash top."
        ),
        editable=False,
        default="",
    )  # default empty, fill it in save
    building = models.ForeignKey(
        "Building", verbose_name=_("Building"), on_delete=models.CASCADE
    )
    description = RichTextField(_("description"), config_name="complete", blank=True)
    poster = models.ForeignKey(
        CustomImageModel, models.SET_NULL, blank=True, null=True, verbose_name=_("Poster")
    )
    url = models.URLField(_("URL"), help_text=_("Url of the stream"), unique=True)
    status = models.BooleanField(
        default=0,
        help_text=_("Check if the broadcaster is currently sending stream."),
    )
    enable_add_event = models.BooleanField(
        default=0,
        verbose_name=_("Enable add event"),
        help_text=_("If checked, it will allow to create an event to this broadcaster."),
    )
    enable_viewer_count = models.BooleanField(
        default=1,
        verbose_name=_("Enable viewers count"),
        help_text=_("Enable viewers count on live."),
    )
    is_restricted = models.BooleanField(
        verbose_name=_("Restricted access"),
        help_text=_("Live is accessible only to authenticated users."),
        default=False,
    )
    public = models.BooleanField(
        verbose_name=_("Show in live tab"),
        help_text=_("Live is accessible from the Live tab"),
        default=True,
    )

    manage_groups = models.ManyToManyField(
        Group,
        blank=True,
        verbose_name=_("Groups"),
        help_text=_(
            "Select one or more groups who can manage event to this broadcaster."
        ),
        related_name="managegroups",
    )

    piloting_implementation = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_("Piloting implementation"),
        help_text=_("Select the piloting implementation for to this broadcaster."),
    )

    piloting_conf = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Piloting configuration parameters"),
        help_text=_("Add piloting configuration parameters in Json format."),
    )
    main_lang = models.CharField(
        _("Main language"),
        max_length=2,
        choices=LANG_CHOICES,
        default=get_language(),
        help_text=_("Select the main language used in the content."),
    )
    transcription_file = models.FileField(
        upload_to="media/" + LIVE_TRANSCRIPTIONS_FOLDER,
        max_length=255,
        null=True,
        editable=False,
    )

    def get_absolute_url(self):
        return reverse("live:direct", args=[str(self.slug)])

    def __str__(self):
        return "%s - %s" % (self.name, self.url)

    def get_poster_url(self):
        if self.poster:
            return self.poster.file.url
        else:
            thumbnail_url = "".join([settings.STATIC_URL, DEFAULT_THUMBNAIL])
            return thumbnail_url

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        filename = self.slug + ".vtt"
        self.set_broadcaster_file(filename)
        super(Broadcaster, self).save(*args, **kwargs)

    class Meta:
        verbose_name = _("Broadcaster")
        verbose_name_plural = _("Broadcasters")
        ordering = ["building", "name"]

    @property
    def sites(self):
        return self.building.sites

    def check_recording(self):
        from pod.live.pilotingInterface import get_piloting_implementation

        impl = get_piloting_implementation(self)
        if impl:
            return impl.is_recording()
        else:
            return False

    def is_recording(self):
        try:
            return self.check_recording()
        except Exception:
            return False

    def is_recording_admin(self):
        try:
            if self.check_recording():
                return format_html('<img src="/static/admin/img/icon-yes.svg" alt="Yes">')
            else:
                return format_html('<img src="/static/admin/img/icon-no.svg" alt="No">')
        except Exception:
            return format_html('<img src="/static/admin/img/icon-alert.svg" alt="Error">')

    is_recording_admin.short_description = _("Is recording?")

    @property
    def qrcode(self, request=None):
        url_scheme = "https" if SECURE_SSL_REDIRECT else "http"
        url_immediate_event = reverse("live:event_immediate_edit", args={self.id})
        data = "".join(
            [
                url_scheme,
                "://",
                get_current_site(request).domain,
                url_immediate_event,
            ]
        )
        img = qrcode.make(data)
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
        alt = _("QR code to record immediately an event")
        return mark_safe(
            f'<img src="data:image/png;base64, {img_str}" '
            + f'width="300px" height="300px" alt={alt}>'
        )

    def set_broadcaster_file(self, filename):
        trans_folder = os.path.join(MEDIA_ROOT, LIVE_TRANSCRIPTIONS_FOLDER)
        trans_file = os.path.join(MEDIA_ROOT, LIVE_TRANSCRIPTIONS_FOLDER, filename)
        empty_trans_file = os.path.join(
            MEDIA_ROOT, LIVE_TRANSCRIPTIONS_FOLDER, "%s_empty.vtt" % filename
        )
        if not os.path.exists(trans_folder):
            os.makedirs(trans_folder)
        if not os.path.exists(trans_file):
            open(trans_file, "a").close()
        if not os.path.exists(empty_trans_file):
            open(empty_trans_file, "a").close()
        self.transcription_file = os.path.join(LIVE_TRANSCRIPTIONS_FOLDER, filename)


def current_time():
    return timezone.now().replace(second=0, microsecond=0)


def one_hour_hence():
    return current_time() + timezone.timedelta(hours=1)


def get_default_event_type():
    return DEFAULT_EVENT_TYPE_ID


def present_or_future_date(value):
    if value < current_time():  # timezone.now():
        raise ValidationError(_("An event cannot be planned in the past"))
    return value


def select_event_owner():
    return (
        lambda q: (Q(first_name__icontains=q) | Q(last_name__icontains=q))
        & Q(owner__sites=Site.objects.get_current())
        & Q(owner__accessgroups__code_name__in=AFFILIATION_EVENT)
    )


class Event(models.Model):
    slug = models.SlugField(
        _("Slug"),
        unique=True,
        max_length=255,
        editable=False,
    )
    title = models.CharField(
        _("Title"),
        max_length=250,
        help_text=_(
            "Please choose a title as short and accurate as "
            "possible, reflecting the main subject / context "
            "of the content. (max length: 250 characters)"
        ),
    )
    description = RichTextField(
        _("Description"),
        config_name="complete",
        blank=True,
        help_text=_(
            "In this field you can describe your content, "
            "add all needed related information, and "
            "format the result using the toolbar."
        ),
    )
    owner = models.ForeignKey(User, verbose_name=_("Owner"), on_delete=models.CASCADE)
    additional_owners = models.ManyToManyField(
        User,
        blank=True,
        verbose_name=_("Additional owners"),
        related_name="owners_events",
        help_text=_(
            "You can add additional owners to the event. They "
            "will have the same rights as you except that they "
            "can't delete this event."
        ),
    )
    start_date = models.DateTimeField(
        _("Start date"), help_text=_("Start of the live event."), default=current_time
    )
    end_date = models.DateTimeField(
        _("End date"), help_text=_("End of the live event."), default=one_hour_hence
    )
    broadcaster = models.ForeignKey(
        Broadcaster,
        verbose_name=_("Broadcaster"),
        help_text=_("Broadcaster name."),
        on_delete=models.CASCADE,
    )
    type = models.ForeignKey(
        Type,
        default=DEFAULT_EVENT_TYPE_ID,
        verbose_name=_("Type"),
        on_delete=models.CASCADE,
    )
    iframe_url = models.URLField(
        _("Embedded Site URL"),
        help_text=_("Url of the embedded site to display"),
        null=True,
        blank=True,
    )
    iframe_height = models.IntegerField(
        _("Embedded Site Height"),
        null=True,
        blank=True,
        help_text=_("Height of the embedded site (in pixels)"),
    )
    aside_iframe_url = models.URLField(
        _("Embedded aside Site URL"),
        help_text=_("Url of the embedded site to display on aside"),
        null=True,
        blank=True,
    )
    is_draft = models.BooleanField(
        verbose_name=_("Draft"),
        help_text=_(
            "If this box is checked, the event will be visible "
            "only by you and the additional owners "
            "but accessible to anyone having the url link."
        ),
        default=True,
    )
    is_restricted = models.BooleanField(
        verbose_name=_("Restricted access"),
        help_text=_(
            "If this box is checked, "
            "the event will only be accessible to authenticated users."
        ),
        default=False,
    )
    restrict_access_to_groups = models.ManyToManyField(
        AccessGroup,
        blank=True,
        verbose_name=_("Groups"),
        help_text=_("Select one or more groups who can access to this event"),
    )
    is_auto_start = models.BooleanField(
        verbose_name=_("Auto start"),
        help_text=_("If this box is checked, the record will start automatically."),
        default=False,
    )
    is_recording_stopped = models.BooleanField(
        default=False,
    )
    video_on_hold = models.ForeignKey(
        Video,
        help_text=_("This video will be displayed when there is no live stream."),
        blank=True,
        null=True,
        verbose_name=_("Video on hold"),
        on_delete=models.CASCADE,
    )
    thumbnail = models.ForeignKey(
        CustomImageModel,
        models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_("Thumbnails"),
    )
    password = models.CharField(
        _("password"),
        help_text=_("Viewing this event will not be possible without this password."),
        max_length=50,
        blank=True,
        null=True,
    )
    max_viewers = models.IntegerField(
        _("Max viewers"),
        null=False,
        default=0,
        help_text=_("Maximum of distinct viewers"),
    )
    viewers = models.ManyToManyField(User, related_name="viewers_events", editable=False)
    videos = models.ManyToManyField(
        Video,
        editable=False,
        related_name="event_videos",
    )
    enable_transcription = models.BooleanField(
        verbose_name=_("Enable transcription"),
        help_text=_("If this box is checked, the transcription will be enabled."),
        default=False,
    )

    class Meta:
        verbose_name = _("Event")
        verbose_name_plural = _("Events")
        ordering = ["start_date"]

    def save(self, *args, **kwargs):
        if not self.id:
            try:
                new_id = get_nextautoincrement(Event)
            except Exception:
                try:
                    new_id = Event.objects.latest("id").id
                    new_id += 1
                except Exception:
                    new_id = 1
        else:
            new_id = self.id
        new_id = "%04d" % new_id
        self.slug = "%s-%s" % (new_id, slugify(self.title))
        super(Event, self).save(*args, **kwargs)

    def __str__(self):
        if self.id:
            return "%s - %s" % ("%04d" % self.id, self.title)
        else:
            return "None"

    def get_absolute_url(self):
        return reverse("live:event", args=[str(self.slug)])

    def get_full_url(self, request=None):
        """Get the video full URL."""
        full_url = "".join(
            ["//", get_current_site(request).domain, self.get_absolute_url()]
        )
        return full_url

    def get_hashkey(self):
        return hashlib.sha256(
            ("%s-%s" % (SECRET_KEY, self.id)).encode("utf-8")
        ).hexdigest()

    def get_thumbnail_card(self):
        if self.thumbnail:
            return self.thumbnail.file.url
        else:
            thumbnail_url = static(DEFAULT_EVENT_THUMBNAIL)
            return thumbnail_url

    def is_current(self):
        """Test if event is currently open."""
        # TODO: FIX this to have possibility to run test between 2 days
        """
        print("IS CURRENT")
        print(self.start_date)
        print(date.today())
        print("=================")
        print(timezone.now().time())
        IS CURRENT
        2022-08-30
        2022-08-30
        =================
        23:35:00
        23:35:01.913570
        00:35:00
        """
        if self.end_date and self.start_date:
            return self.start_date <= timezone.localtime(timezone.now()) <= self.end_date
        else:
            return False

    def is_past(self):
        """Test if event has happened in past."""
        if self.end_date:
            return self.end_date <= timezone.localtime(timezone.now())
        else:
            return False

    def is_coming(self):
        """Test if event will happen in future."""
        if self.start_date:
            return timezone.localtime(timezone.now()) < self.start_date
        else:
            return False


class LiveTranscriptRunningTask(models.Model):
    task_id = models.CharField(max_length=255, unique=True)
    broadcaster = models.ForeignKey(
        Broadcaster,
        verbose_name=_("Broadcaster"),
        help_text=_("Broadcaster name."),
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = _("Running task")
        verbose_name_plural = _("Running tasks")


class HeartBeat(models.Model):
    user = models.ForeignKey(
        User, null=True, verbose_name=_("Viewer"), on_delete=models.CASCADE
    )
    viewkey = models.CharField(_("Viewkey"), max_length=200, unique=True)
    event = models.ForeignKey(
        Event, null=True, verbose_name=_("Event"), on_delete=models.CASCADE
    )
    last_heartbeat = models.DateTimeField(_("Last heartbeat"), default=timezone.now)

    class Meta:
        verbose_name = _("Heartbeat")
        verbose_name_plural = _("Heartbeats")
        ordering = ["event"]
