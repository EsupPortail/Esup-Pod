import json
import logging

from django.db import models
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from pod.main.models import get_nextautoincrement
from pod.video.models import BaseVideo
from pod.video.models import __LANG_CHOICES_DICT__

logger = logging.getLogger(__name__)


class Follower(models.Model):
    actor = models.CharField(
        _("Actor"),
        max_length=255,
        help_text=_("Actor who initiated the Follow activity"),
    )


class Following(models.Model):
    class Status(models.IntegerChoices):
        NONE = 0, _("None")
        REQUESTED = 1, _("Following request sent")
        ACCEPTED = 2, _("Following request accepted")
        REFUSED = 3, _("Following request refused")

    object = models.CharField(
        _("Object"),
        max_length=255,
        help_text=_("URL of the instance to follow"),
    )
    status = models.IntegerField(
        _("Status"),
        help_text=_("URL of the instance to follow"),
        choices=Status.choices,
        default=Status.NONE,
    )

    def __str__(self) -> str:
        return self.object


class ExternalVideo(BaseVideo):
    source_instance = models.ForeignKey(
        Following,
        on_delete=models.CASCADE,
        verbose_name=_("Source instance"),
        help_text=_("Video origin instance"),
    )
    ap_id = models.CharField(
        _("Video identifier"),
        max_length=255,
        help_text=_("Video identifier URL"),
        unique=True,
    )
    thumbnail = models.CharField(
        _("Thumbnails"),
        max_length=255,
        blank=True,
        null=True,
    )
    viewcount = models.IntegerField(_("Number of view"), default=0)
    videos = models.JSONField(
        verbose_name=_("Mp4 resolutions list"),
    )

    def __init__(self, *args, **kwargs):
        super(ExternalVideo, self).__init__(is_external=True, *args, **kwargs)

    def save(self, *args, **kwargs) -> None:
        """Store an external video object in db."""
        newid = -1

        if not self.id:
            try:
                newid = get_nextautoincrement(ExternalVideo)
            except Exception:
                try:
                    newid = ExternalVideo.objects.latest("id").id
                    newid += 1
                except Exception:
                    newid = 1
        else:
            newid = self.id
        newid = "%04d" % newid
        self.slug = "%s-%s" % (newid, slugify(self.title))
        super(ExternalVideo, self).save(*args, **kwargs)

    @property
    def get_thumbnail_admin(self):
        """Return thumbnail image card of current external video for admin."""
        return format_html(
            '<img style="max-width:100px" '
            'src="%s" alt="%s" loading="lazy">'
            % (
                self.thumbnail,
                self.title,
            )
        )

    def get_thumbnail_card(self) -> str:
        """Return thumbnail image card of current external video."""
        return (
            '<img class="pod-thumbnail" src="%s" alt="%s"\
            loading="lazy">'
            % (self.thumbnail, self.title)
        )

    get_thumbnail_admin.fget.short_description = _("Thumbnails")

    def get_thumbnail_url(self, default="img/default.png") -> str:
        """Get a thumbnail url for the video."""
        return self.thumbnail

    def get_absolute_url(self) -> str:
        """Get the external video absolute URL."""
        return reverse("activitypub:external_video", args=[str(self.slug)])

    def get_marker_time_for_user(video, user):
        return 0

    def get_video_mp4_json(self) -> list:
        """Get the JSON representation of the MP4 video."""
        videos = [
            {
                "type": video["type"],
                "src": video["src"],
                "size": video["size"],
                "width": video["width"],
                "height": video["height"],
                "extension": f".{video['src'].split('.')[-1]}",
                "label": f"{video['height']}p",
            }
            for video in sorted(self.videos, key=lambda v: v["width"])
        ]
        videos[-1]["selected"] = True
        return json.dumps(videos)

    def get_json_to_index(self):
        """Get json attributes for elasticsearch indexation."""
        try:
            data_to_dump = {
                "id": f"{self.id}_external",
                "title": "%s" % self.title,
                "owner": "%s" % self.source_instance.object,
                "owner_full_name": "%s" % self.source_instance.object,
                "date_added": (
                    "%s" % self.date_added.strftime("%Y-%m-%dT%H:%M:%S")
                    if self.date_added
                    else None
                ),
                "date_evt": (
                    "%s" % self.date_evt.strftime("%Y-%m-%dT%H:%M:%S")
                    if self.date_evt
                    else None
                ),
                "description": "%s" % self.description,
                "thumbnail": "%s" % self.get_thumbnail_url(),
                "duration": "%s" % self.duration,
                "tags": [],
                "type": {},
                "disciplines": [],
                "channels": [],
                "themes": [],
                "contributors": [],
                "chapters": [],
                "overlays": [],
                "full_url": self.get_absolute_url(),
                "is_restricted": False,
                "password": False,
                "duration_in_time": self.duration_in_time,
                "mediatype": "video" if self.is_video else "audio",
                "cursus": "",
                "main_lang": "%s" % __LANG_CHOICES_DICT__[self.main_lang],
                "is_external": self.is_external,
            }
            return json.dumps(data_to_dump)
        except ExternalVideo.DoesNotExist as e:
            logger.error(
                "An error occured during get_json_to_index"
                " for external video %s: %s" % (self.id, e)
            )
            return json.dumps({})
