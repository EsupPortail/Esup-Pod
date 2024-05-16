"""Esup-Pod video Enrichment."""

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.core.files import File
from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils.translation import ugettext as _
from django.utils import timezone
from django.template.defaultfilters import slugify

from ckeditor.fields import RichTextField
from tempfile import NamedTemporaryFile
from webvtt import WebVTT, Caption

from pod.video.models import Video
from pod.main.models import get_nextautoincrement

import os
import datetime

if getattr(settings, "USE_PODFILE", False):
    from pod.podfile.models import CustomImageModel
    from pod.podfile.models import CustomFileModel
    from pod.podfile.models import UserFolder

    __FILEPICKER__ = True
else:
    __FILEPICKER__ = False
    from pod.main.models import CustomImageModel
    from pod.main.models import CustomFileModel

FILES_DIR = getattr(settings, "FILES_DIR", "files")

__NAME__ = _("Enrichment")


def enrichment_to_vtt(list_enrichment, video) -> str:
    webvtt = WebVTT()
    for enrich in list_enrichment:
        start = datetime.datetime.fromtimestamp(enrich.start, tz=timezone.utc).strftime(
            "%H:%M:%S.%f"
        )[:-3]
        end = datetime.datetime.fromtimestamp(enrich.end, tz=timezone.utc).strftime(
            "%H:%M:%S.%f"
        )[:-3]
        url = enrichment_to_vtt_type(enrich)
        caption = Caption(
            "{0}".format(start),
            "{0}".format(end),
            [
                "{",
                '"title": "{0}",'.format(enrich.title),
                '"type": "{0}",'.format(enrich.type),
                '"stop_video": "{0}",'.format("%s" % 1 if enrich.stop_video else 0),
                '"url": "{0}"'.format(url),
                "}",
            ],
        )
        caption.identifier = enrich.slug
        webvtt.captions.append(caption)
    temp_vtt_file = NamedTemporaryFile(suffix=".vtt")
    with open(temp_vtt_file.name, "w") as f:
        webvtt.write(f)
    if __FILEPICKER__:
        videodir, created = UserFolder.objects.get_or_create(
            name="%s" % video.slug, owner=video.owner
        )
        previous_enrichment_file = CustomFileModel.objects.filter(
            name__startswith="enrichment",
            folder=videodir,
            created_by=video.owner,
        )
        for enr in previous_enrichment_file:
            enr.delete()  # do it like this to delete file
        enrichment_file, created = CustomFileModel.objects.get_or_create(
            name="enrichment", folder=videodir, created_by=video.owner
        )

        if enrichment_file.file and os.path.isfile(enrichment_file.file.path):
            os.remove(enrichment_file.file.path)
    else:
        enrichment_file, created = CustomFileModel.objects.get_or_create()
    enrichment_file.file.save("enrichment.vtt", File(temp_vtt_file))
    enrichment_vtt, created = EnrichmentVtt.objects.get_or_create(video=video)
    enrichment_vtt.src = enrichment_file
    enrichment_vtt.save()
    return enrichment_file.file.path


def enrichment_to_vtt_type(enrich):
    if enrich.type == "image":
        return enrich.image.file.url
    elif enrich.type == "document":
        return enrich.document.file.url
    elif enrich.type == "richtext":
        richtext = enrich.richtext.replace('"', '\\"')
        return "".join(richtext.splitlines())
    elif enrich.type == "weblink":
        return enrich.weblink
    elif enrich.type == "embed":
        return enrich.embed.replace('"', '\\"')


class Enrichment(models.Model):
    ENRICH_CHOICES = (
        ("image", _("image")),
        ("richtext", _("richtext")),
        ("weblink", _("weblink")),
        ("document", _("document")),
        ("embed", _("embed")),
    )

    video = models.ForeignKey(Video, verbose_name=_("video"), on_delete=models.CASCADE)
    title = models.CharField(_("title"), max_length=100)
    slug = models.SlugField(
        _("slug"),
        unique=True,
        max_length=105,
        help_text=_(
            'Used to access this instance, the "slug" is a short'
            + " label containing only letters, numbers, underscore"
            + " or dash top."
        ),
        editable=False,
    )
    stop_video = models.BooleanField(
        _("Stop video"),
        default=False,
        help_text=_("The video will pause when displaying the enrichment."),
    )
    start = models.PositiveIntegerField(
        _("Start"),
        default=0,
        help_text=_("Start of enrichment display in seconds."),
    )
    end = models.PositiveIntegerField(
        _("End"),
        default=1,
        help_text=_("End of enrichment display in seconds."),
    )
    type = models.CharField(
        _("Type"), max_length=10, choices=ENRICH_CHOICES, null=True, blank=True
    )

    image = models.ForeignKey(
        CustomImageModel,
        verbose_name=_("Image"),
        null=True,
        on_delete=models.CASCADE,
        blank=True,
    )
    document = models.ForeignKey(
        CustomFileModel,
        verbose_name=_("Document"),
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        help_text=_("Integrate a document (PDF, text, html)"),
    )
    richtext = RichTextField(_("Richtext"), config_name="complete", blank=True)
    weblink = models.URLField(_("Web link"), max_length=200, null=True, blank=True)
    embed = models.TextField(
        _("Embed code"),
        null=True,
        blank=True,
        help_text=_("Paste here a code from an external source to embed it."),
    )

    class Meta:
        verbose_name = _("Enrichment")
        verbose_name_plural = _("Enrichments")
        ordering = ["start"]

    @property
    def sites(self):
        return self.video.sites

    def clean(self) -> None:
        msg = list()
        msg = self.verify_all_fields()
        if len(msg) > 0:
            raise ValidationError(msg)
        msg = self.verify_end_start_item() + self.overlap()
        if len(msg) > 0:
            raise ValidationError(msg)

    def verify_type(self, type):
        typelist = {
            "image": self.image,
            "richtext": self.richtext,
            "weblink": self.weblink,
            "document": self.document,
            "embed": self.embed,
        }
        if type not in typelist:
            return _("Please enter a correct {0}.".format(type))

    def verify_all_fields(self) -> list:
        """Validate all Enrichment fields."""
        msg = list()
        if (
            not self.title
            or self.title == ""
            or len(self.title) < 2
            or len(self.title) > 100
        ):
            msg.append(_("Please enter a title from 2 to 100 characters."))
        if (
            self.start is None
            or self.start == ""
            or self.start < 0
            or self.start >= self.video.duration
        ):
            msg.append(
                _(
                    "Please enter a correct start field between 0 and "
                    + "{0}.".format(self.video.duration - 1)
                )
            )
        if (
            not self.end
            or self.end == ""
            or self.end <= 0
            or self.end > self.video.duration
        ):
            msg.append(
                _(
                    "Please enter a correct end field between 1 and "
                    + "{0}.".format(self.video.duration)
                )
            )
        if self.type:
            if self.verify_type(self.type):
                msg.append(self.verify_type(self.type))
        else:
            msg.append(_("Please enter a type."))
        return msg

    def verify_end_start_item(self) -> list:
        """Check validity of start and end values."""
        msg = list()
        if self.start > self.end:
            msg.append(
                _(
                    "The value of the start field is greater than the value "
                    + "of end field."
                )
            )
        if self.end > self.video.duration:
            msg.append(_("The value of end field is greater than the video duration."))
        if self.end and self.start == self.end:
            msg.append(_("End field and start field can’t be equal."))

        return msg

    def overlap(self) -> list:
        """Check that there is no overlap between this enrichment and existing ones."""
        msg = list()
        instance = None
        if self.slug:
            instance = Enrichment.objects.get(slug=self.slug)
        list_enrichment = Enrichment.objects.filter(video=self.video)
        if instance:
            list_enrichment = list_enrichment.exclude(id=instance.id)
        if len(list_enrichment) > 0:
            for element in list_enrichment:
                if not (
                    (self.start < element.start and self.end <= element.start)
                    or (self.start >= element.end and self.end > element.end)
                ):
                    msg.append(
                        _(
                            "There is an overlap with the enrichment {0},"
                            " please change time start and/or "
                            "time end values."
                        ).format(element.title)
                    )
        return msg

    def save(self, *args, **kwargs) -> None:
        """Store this enrichment in DB."""
        newid = -1
        if not self.id:
            try:
                newid = get_nextautoincrement(Enrichment)
            except Exception:
                try:
                    newid = Enrichment.objects.latest("id").id
                    newid += 1
                except Exception:
                    newid = 1
        else:
            newid = self.id
        newid = "{0}".format(newid)
        self.slug = "{0} - {1}".format(newid, slugify(self.title))
        super(Enrichment, self).save(*args, **kwargs)

    def __str__(self):
        return "Media: {0} - Video: {1}".format(self.title, self.video)


@receiver(post_save, sender=Enrichment)
def update_vtt(sender, instance=None, created=False, **kwargs) -> None:
    list_enrichment = instance.video.enrichment_set.all()
    enrichment_to_vtt(list_enrichment, instance.video)


@receiver(post_delete, sender=Enrichment)
def delete_vtt(sender, instance=None, created=False, **kwargs) -> None:
    list_enrichment = instance.video.enrichment_set.all()
    if list_enrichment.count() > 0:
        enrichment_to_vtt(list_enrichment, instance.video)
    else:
        EnrichmentVtt.objects.filter(video=instance.video).delete()


class EnrichmentVtt(models.Model):
    video = models.OneToOneField(
        Video,
        verbose_name=_("Video"),
        editable=False,
        null=True,
        on_delete=models.CASCADE,
    )
    src = models.ForeignKey(
        CustomFileModel,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        verbose_name=_("Subtitle file"),
    )

    @property
    def sites(self):
        return self.video.sites

    def clean(self) -> None:
        """Validate EnrichmentVTT fields and eventually raise ValidationError."""
        msg = list()
        msg = self.verify_attributs() + self.verify_not_same_track()
        if len(msg) > 0:
            raise ValidationError(msg)

    def verify_attributs(self) -> list:
        """Validate EnrichmentVTT fields."""
        msg = list()
        if "vtt" not in self.src.file_type:
            msg.append(_("Only “.vtt” format is allowed."))
        return msg

    class Meta:
        ordering = ["video"]
        verbose_name = _("Enrichment Vtt")
        verbose_name_plural = _("Enrichments Vtt")


class EnrichmentGroup(models.Model):
    video = models.OneToOneField(Video, verbose_name=_("Video"), on_delete=models.CASCADE)
    groups = models.ManyToManyField(
        Group,
        blank=True,
        verbose_name=_("Groups"),
        help_text=_(
            "Select one or more groups who"
            " can access to the"
            " enrichment of the video"
        ),
    )

    class Meta:
        ordering = ["video"]
        verbose_name = _("Enrichment Video Group")
        verbose_name_plural = _("Enrichment Video Groups")

    @property
    def sites(self):
        return self.video.sites

    def __str__(self) -> str:
        return "Enrichment group %s" % (self.video)
