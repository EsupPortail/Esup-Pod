from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import slugify
from django.utils.html import format_html
from django.urls import reverse


from pod.video.models import BaseVideo
from pod.main.models import get_nextautoincrement


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
    video = models.CharField(
        _("Video source"),
        max_length=255,
        help_text=_("Video source URL"),
    )
    thumbnail = models.CharField(
        _("Thumbnails"),
        max_length=255,
        blank=True,
        null=True,
    )
    viewcount = models.IntegerField(_("Number of view"), default=0)

    def save(self, *args, **kwargs) -> None:
        """Store an external video object in db."""
        newid = -1

        # In case of creating new Video
        if not self.id:
            # previous_video_state = None
            try:
                newid = get_nextautoincrement(ExternalVideo)
            except Exception:
                try:
                    newid = ExternalVideo.objects.latest("id").id
                    newid += 1
                except Exception:
                    newid = 1
        else:
            # previous_video_state = Video.objects.get(id=self.id)
            newid = self.id
        newid = "%04d" % newid
        self.slug = "%s-%s" % (newid, slugify(self.title))
        self.is_external = True
        super(ExternalVideo, self).save(*args, **kwargs)

    @property
    def get_thumbnail_admin(self):
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

    def get_absolute_url(self) -> str:
        """Get the external video absolute URL."""
        return reverse("activitypub:external_video", args=[str(self.slug)])

    def get_marker_time_for_user(video, user):  # TODO: Check usage
        return 0
