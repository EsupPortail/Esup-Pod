"""Esup-Pod "live" models."""

from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from ckeditor.fields import RichTextField
from django.template.defaultfilters import slugify
from pod.video.models import Video
from django.contrib.sites.models import Site
from select2 import fields as select2_fields
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone


if getattr(settings, "USE_PODFILE", False):
    from pod.podfile.models import CustomImageModel

    FILEPICKER = True
else:
    FILEPICKER = False
    from pod.main.models import CustomImageModel

DEFAULT_THUMBNAIL = getattr(settings, "DEFAULT_THUMBNAIL", "img/default.svg")


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


class Broadcaster(models.Model):
    name = models.CharField(_("name"), max_length=200, unique=True)
    slug = models.SlugField(
        _("Slug"),
        unique=True,
        max_length=200,
        help_text=_(
            u'Used to access this instance, the "slug" is a short label '
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
        verbose_name=_(u"Enable viewers count"),
        help_text=_("Enable viewers count on live."),
    )
    is_restricted = models.BooleanField(
        verbose_name=_(u"Restricted access"),
        help_text=_("Live is accessible only to authenticated users."),
        default=False,
    )
    public = models.BooleanField(
        verbose_name=_(u"Show in live tab"),
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
