"""Esup-Pod "live" models."""
import hashlib
from datetime import date, datetime

from ckeditor.fields import RichTextField
from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from select2 import fields as select2_fields
from sorl.thumbnail import get_thumbnail

from pod.main.models import get_nextautoincrement
from pod.video.models import Video, Type

if getattr(settings, "USE_PODFILE", False):
    from pod.podfile.models import CustomImageModel

    FILEPICKER = True
else:
    FILEPICKER = False
    from pod.main.models import CustomImageModel

DEFAULT_THUMBNAIL = getattr(settings, "DEFAULT_THUMBNAIL", "img/default.svg")
DEFAULT_EVENT_THUMBNAIL = getattr(
    settings, "DEFAULT_EVENT_THUMBNAIL", "img/default-event.svg"
)
DEFAULT_EVENT_TYPE_ID = getattr(settings, "DEFAULT_EVENT_TYPE_ID", 1)
RESTRICT_EDIT_EVENT_ACCESS_TO_STAFF_ONLY = getattr(
    settings, "RESTRICT_EDIT_EVENT_ACCESS_TO_STAFF_ONLY", True
)
SECRET_KEY = getattr(settings, "SECRET_KEY", "")


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
        permissions = (
            (
                "view_building_supervisor",
                "Can see the supervisor page for building",
            ),
        )


@receiver(post_save, sender=Building)
def default_site_building(sender, instance, created, **kwargs):
    if len(instance.sites.all()) == 0:
        instance.sites.add(Site.objects.get_current())


def get_available_broadcasters_of_building(user, building_id, broadcaster_id=None):
    right_filter = Broadcaster.objects.filter(
        Q(status=True)
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
        Q(broadcaster__status=True)
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
    building = models.ForeignKey("Building", verbose_name=_("Building"))
    description = RichTextField(_("description"), config_name="complete", blank=True)
    poster = models.ForeignKey(
        CustomImageModel,
        models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_("Poster"),
    )
    url = models.URLField(_("URL"), help_text=_("Url of the stream"), unique=True)
    video_on_hold = select2_fields.ForeignKey(
        Video,
        help_text=_("This video will be displayed when there is no live stream."),
        blank=True,
        null=True,
        verbose_name=_("Video on hold"),
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
    status = models.BooleanField(
        default=0,
        help_text=_("Check if the broadcaster is currently sending stream."),
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
    password = models.CharField(
        _("password"),
        help_text=_("Viewing this live will not be possible without this password."),
        max_length=50,
        blank=True,
        null=True,
    )
    viewcount = models.IntegerField(_("Number of viewers"), default=0, editable=False)
    viewers = models.ManyToManyField(User, editable=False)
    # restrict_access_to_groups = select2_fields.ManyToManyField(
    #     AccessGroup,
    #     blank=True,
    #     verbose_name=_("Access Groups"),
    #     help_text=_("Select one or more groups who can access to this broadcater."),
    #     related_name='restrictaccesstogroups',
    # )

    manage_groups = select2_fields.ManyToManyField(
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

    def get_absolute_url(self):
        return reverse("live:video_live", args=[str(self.slug)])

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
        super(Broadcaster, self).save(*args, **kwargs)

    class Meta:
        verbose_name = _("Broadcaster")
        verbose_name_plural = _("Broadcasters")
        ordering = ["building", "name"]

    @property
    def sites(self):
        return self.building.sites

    def is_recording_admin(self):
        from pod.live.pilotingInterface import get_piloting_implementation

        impl = get_piloting_implementation(self)
        try:
            if impl:
                if impl.is_recording():
                    return format_html(
                        '<img src="/static/admin/img/icon-yes.svg" alt="Yes">'
                    )
                else:
                    return format_html(
                        '<img src="/static/admin/img/icon-no.svg" alt="No">'
                    )
        except Exception:
            pass
        return format_html('<img src="/static/admin/img/icon-alert.svg" alt="Error">')

    is_recording_admin.short_description = _("Is recording ?")


class HeartBeat(models.Model):
    user = models.ForeignKey(User, null=True, verbose_name=_("Viewer"))
    viewkey = models.CharField(_("Viewkey"), max_length=200, unique=True)
    broadcaster = models.ForeignKey(
        Broadcaster, null=False, verbose_name=_("Broadcaster")
    )
    last_heartbeat = models.DateTimeField(_("Last heartbeat"), default=timezone.now)

    class Meta:
        verbose_name = _("Heartbeat")
        verbose_name_plural = _("Heartbeats")
        ordering = ["broadcaster"]


def current_time():
    return datetime.now().replace(second=0, microsecond=0)


def one_hour_hence():
    return current_time() + timezone.timedelta(hours=1)


def get_default_event_type():
    return DEFAULT_EVENT_TYPE_ID


def present_or_future_date(value):
    if value < date.today():
        raise ValidationError(_("An event cannot be planned in the past"))
    return value


def select_event_owner():
    if RESTRICT_EDIT_EVENT_ACCESS_TO_STAFF_ONLY:
        return lambda q: (
            Q(is_staff=True) & (Q(first_name__icontains=q) | Q(last_name__icontains=q))
        ) & Q(owner__sites=Site.objects.get_current())
    else:
        return lambda q: (Q(first_name__icontains=q) | Q(last_name__icontains=q)) & Q(
            owner__sites=Site.objects.get_current()
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

    owner = select2_fields.ForeignKey(
        User,
        ajax=True,
        verbose_name=_("Owner"),
        search_field=select_event_owner(),
        on_delete=models.CASCADE,
    )

    additional_owners = select2_fields.ManyToManyField(
        User,
        blank=True,
        ajax=True,
        js_options={"width": "off"},
        verbose_name=_("Additional owners"),
        search_field=select_event_owner(),
        related_name="owners_events",
        help_text=_(
            "You can add additional owners to the event. They "
            "will have the same rights as you except that they "
            "can't delete this event."
        ),
    )

    start_date = models.DateField(
        _("Date of event"),
        default=date.today,
        help_text=_("Start date of the live."),
        validators=[present_or_future_date],
    )
    start_time = models.TimeField(
        _("Start time"),
        default=current_time,
        help_text=_("Start time of the live event."),
    )
    end_time = models.TimeField(
        _("End time"),
        default=one_hour_hence,
        help_text=_("End time of the live event."),
    )

    broadcaster = models.ForeignKey(
        Broadcaster,
        verbose_name=_("Broadcaster"),
        help_text=_("Broadcaster name."),
    )

    type = models.ForeignKey(Type, default=DEFAULT_EVENT_TYPE_ID, verbose_name=_("Type"))

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
        default=True,
    )

    is_auto_start = models.BooleanField(
        verbose_name=_("Auto start"),
        help_text=_("If this box is checked, " "the record will start automatically."),
        default=False,
    )

    thumbnail = models.ForeignKey(
        CustomImageModel,
        models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_("Thumbnails"),
    )

    # password = models.CharField(
    #     _("password"),
    #     help_text=_("Viewing this video will not be possible without this password."),
    #     max_length=50,
    #     blank=True,
    #     null=True,
    # )

    videos = models.ManyToManyField(
        Video,
        editable=False,
    )

    class Meta:
        verbose_name = _("Event")
        verbose_name_plural = _("Events")
        ordering = ["start_date", "start_time"]

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

    def get_thumbnail_url(self):
        """Get a thumbnail url for the event."""
        request = None
        if self.thumbnail and self.thumbnail.file_exist():
            thumbnail_url = "".join(
                [
                    "//",
                    get_current_site(request).domain,
                    self.thumbnail.file.url,
                ]
            )
        else:
            thumbnail_url = static(DEFAULT_EVENT_THUMBNAIL)
        return thumbnail_url

    @property
    def get_thumbnail_admin(self):
        if self.thumbnail and self.thumbnail.file_exist():
            im = get_thumbnail(self.thumbnail.file, "100x100", crop="center", quality=72)
            thumbnail_url = im.url
        else:
            thumbnail_url = static(DEFAULT_EVENT_THUMBNAIL)
        return format_html(
            '<img style="max-width:100px" '
            'src="%s" alt="%s" loading="lazy"/>'
            % (
                thumbnail_url,
                self.title.replace("{", "").replace("}", "").replace('"', "'"),
            )
        )

    get_thumbnail_admin.fget.short_description = _("Thumbnails")

    def get_thumbnail_card(self):
        """Return thumbnail image card of current event."""
        if self.thumbnail and self.thumbnail.file_exist():
            im = get_thumbnail(self.thumbnail.file, "x170", crop="center", quality=72)
            thumbnail_url = im.url
        else:
            thumbnail_url = static(DEFAULT_EVENT_THUMBNAIL)
        return (
            '<img class="card-img-top" src="%s" alt=""\
            loading="lazy"/>'
            % thumbnail_url
        )

    def is_current(self):
        return self.start_date == date.today() and (
            self.start_time <= datetime.now().time() <= self.end_time
        )

    def is_past(self):
        return self.start_date < date.today() or (
            self.start_date == date.today() and self.end_time < datetime.now().time()
        )

    def is_coming(self):
        return self.start_date > date.today() or (
            self.start_date == date.today() and datetime.now().time() < self.start_time
        )

    def get_start(self):
        return datetime.combine(self.start_date, self.start_time)

    def get_end(self):
        return datetime.combine(self.start_date, self.end_time)
