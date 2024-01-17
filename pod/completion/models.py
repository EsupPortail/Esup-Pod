import base64

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import slugify
from ckeditor.fields import RichTextField
from pod.video.models import Video
from pod.main.models import get_nextautoincrement
from pod.main.lang_settings import ALL_LANG_CHOICES, PREF_LANG_CHOICES

if getattr(settings, "USE_PODFILE", False):
    from pod.podfile.models import CustomFileModel
else:
    from pod.main.models import CustomFileModel

ROLE_CHOICES = getattr(
    settings,
    "ROLE_CHOICES",
    (
        ("actor", _("actor")),
        ("author", _("author")),
        ("designer", _("designer")),
        ("consultant", _("consultant")),
        ("contributor", _("contributor")),
        ("editor", _("editor")),
        ("speaker", _("speaker")),
        ("soundman", _("soundman")),
        ("director", _("director")),
        ("writer", _("writer")),
        ("technician", _("technician")),
        ("voice-over", _("voice-over")),
    ),
)
KIND_CHOICES = getattr(
    settings,
    "KIND_CHOICES",
    (
        ("subtitles", _("subtitles")),
        ("captions", _("captions")),
    ),
)

LANG_CHOICES = getattr(
    settings,
    "LANG_CHOICES",
    (
        (_("-- Frequently used languages --"), PREF_LANG_CHOICES),
        (_("-- All languages --"), ALL_LANG_CHOICES),
    ),
)
__LANG_CHOICES_DICT__ = {
    key: value for key, value in LANG_CHOICES[0][1] + LANG_CHOICES[1][1]
}
DEFAULT_LANG_TRACK = getattr(settings, "DEFAULT_LANG_TRACK", "fr")


class Contributor(models.Model):
    """Class for Contributor object."""

    video = models.ForeignKey(Video, verbose_name=_("video"), on_delete=models.CASCADE)
    name = models.CharField(
        verbose_name=_("lastname / firstname"), max_length=200, default=""
    )
    email_address = models.EmailField(
        verbose_name=_("mail"), null=True, blank=True, default=""
    )
    role = models.CharField(
        verbose_name=_("role"), max_length=200, choices=ROLE_CHOICES, default="author"
    )
    weblink = models.URLField(
        verbose_name=_("Web link"), max_length=200, null=True, blank=True
    )

    class Meta:
        verbose_name = _("Contributor")
        verbose_name_plural = _("Contributors")

    @property
    def sites(self):
        return self.video.sites

    def clean(self):
        msg = list()
        msg = self.verify_attributs() + self.verify_not_same_contributor()
        if len(msg) > 0:
            raise ValidationError(msg)

    def verify_attributs(self):
        msg = list()
        if not self.name or self.name == "":
            msg.append(_("Please enter a name."))
        elif len(self.name) < 2 or len(self.name) > 200:
            msg.append(_("Please enter a name from 2 to 200 caracters."))
        if self.weblink and len(self.weblink) > 200:
            msg.append(_("You cannot enter a weblink with more than 200 caracters."))
        if not self.role:
            msg.append(_("Please enter a role."))
        if len(msg) > 0:
            return msg
        else:
            return list()

    def verify_not_same_contributor(self):
        msg = list()
        list_contributor = Contributor.objects.filter(video=self.video)
        if self.id:
            list_contributor = list_contributor.exclude(id=self.id)
        if len(list_contributor) > 0:
            for element in list_contributor:
                if self.name == element.name and self.role == element.role:
                    msg.append(
                        _(
                            "There is already a contributor with the same "
                            + "name and role in the list."
                        )
                    )
                    return msg
        return list()

    def __str__(self):
        return "Video:{0} - Name:{1} - Role:{2}".format(self.video, self.name, self.role)

    def get_base_mail(self):
        data = base64.b64encode(self.email_address.encode())
        return data

    def get_noscript_mail(self):
        return self.email_address.replace("@", "__AT__")


class Document(models.Model):
    video = models.ForeignKey(Video, verbose_name=_("Video"), on_delete=models.CASCADE)
    document = models.ForeignKey(
        CustomFileModel,
        null=True,
        blank=True,
        verbose_name=_("Document"),
        on_delete=models.CASCADE,
    )
    private = models.BooleanField(
        verbose_name=_("Private document"),
        default=False,
        help_text=_("Document is private."),
    )

    class Meta:
        verbose_name = _("Document")
        verbose_name_plural = _("Documents")

    @property
    def sites(self):
        return self.video.sites

    def clean(self):
        msg = list()
        msg = self.verify_document() + self.verify_not_same_document()
        if len(msg) > 0:
            raise ValidationError(msg)

    def verify_document(self):
        msg = list()
        if not self.document:
            msg.append(_("Please enter a document."))
        if len(msg) > 0:
            return msg
        else:
            return list()

    def verify_not_same_document(self):
        msg = list()
        list_doc = Document.objects.filter(video=self.video)
        if self.id:
            list_doc = list_doc.exclude(id=self.id)
        if len(list_doc) > 0:
            for element in list_doc:
                if self.document == element.document:
                    msg.append(_("This document is already contained " + "in the list"))
            if len(msg) > 0:
                return msg
        return list()

    def __str__(self):
        return "Document: {0} - Video: {1}".format(self.document.name, self.video)


class EnrichModelQueue(models.Model):
    title = models.TextField(_("Title"), null=True, blank=True)
    text = models.TextField(_("Text"), null=False, blank=False)
    model_type = models.CharField(
        _("Model Type"), null=False, blank=False, max_length=100, default="STT"
    )
    lang = models.CharField(
        _("Language"), max_length=2, choices=LANG_CHOICES, default="fr"
    )
    in_treatment = models.BooleanField(_("In Treatment"), default=False)

    def get_label_lang(self):
        return "%s" % __LANG_CHOICES_DICT__[self.lang]

    class Meta:
        verbose_name = _("EnrichModelQueue")
        verbose_name_plural = _("EnrichModelQueue")

    def verify_attributs(self):
        msg = list()
        if not self.text:
            msg.append(_("Please enter a text."))
        if not self.model_type:
            msg.append(_("Please enter a model type."))
        if not self.lang:
            msg.append(_("Please enter a language."))
        if len(msg) > 0:
            return msg
        else:
            return list()


class Track(models.Model):
    video = models.ForeignKey(Video, verbose_name=_("Video"), on_delete=models.CASCADE)
    kind = models.CharField(
        _("Kind"), max_length=10, choices=KIND_CHOICES, default="subtitles"
    )
    lang = models.CharField(
        _("Language"), max_length=2, choices=LANG_CHOICES, default=DEFAULT_LANG_TRACK
    )
    src = models.ForeignKey(
        CustomFileModel,
        blank=True,
        null=True,
        verbose_name=_("Subtitle file"),
        on_delete=models.CASCADE,
    )
    enrich_ready = models.BooleanField(_("Enrich Ready"), default=False)

    @property
    def sites(self):
        return self.video.sites

    def get_label_lang(self):
        return "%s" % __LANG_CHOICES_DICT__[self.lang]

    class Meta:
        verbose_name = _("Track")
        verbose_name_plural = _("Tracks")

    def clean(self):
        msg = list()
        msg = self.verify_attributs() + self.verify_not_same_track()
        if len(msg) > 0:
            raise ValidationError(msg)

    def verify_attributs(self):
        msg = list()
        if not self.kind:
            msg.append(_("Please enter a kind."))
        elif self.kind != "subtitles" and self.kind != "captions":
            msg.append(_("Please enter a correct kind."))
        if not self.lang:
            msg.append(_("Please enter a language."))
        if not self.src:
            msg.append(_("Please specify a track file."))
        elif "vtt" not in self.src.file_type:
            msg.append(_("Only “.vtt” format is allowed."))
        if len(msg) > 0:
            return msg
        else:
            return list()

    def verify_not_same_track(self):
        msg = list()
        list_track = Track.objects.filter(video=self.video)
        if self.id:
            list_track = list_track.exclude(id=self.id)
        if len(list_track) > 0:
            for element in list_track:
                if self.kind == element.kind and self.lang == element.lang:
                    msg.append(
                        _(
                            "There is already a subtitle with the "
                            + "same kind and language in the list."
                        )
                    )
                    return msg
        return list()

    def __str__(self):
        return "{0} - File: {1} - Video: {2}".format(self.kind, self.src.name, self.video)


class Overlay(models.Model):
    POSITION_CHOICES = (
        ("top-left", _("top-left")),
        ("top", _("top")),
        ("top-right", _("top-right")),
        ("right", _("right")),
        ("bottom-right", _("bottom-right")),
        ("bottom", _("bottom")),
        ("bottom-left", _("bottom-left")),
        ("left", _("left")),
    )

    video = models.ForeignKey(Video, verbose_name=_("Video"), on_delete=models.CASCADE)
    title = models.CharField(_("Title"), max_length=100)
    slug = models.SlugField(
        _("Slug"),
        unique=True,
        max_length=105,
        help_text=_(
            'Used to access this instance, the "slug" is a short'
            + " label containing only letters, numbers, underscore"
            + " or dash top."
        ),
        editable=False,
    )
    time_start = models.PositiveIntegerField(
        _("Start time"),
        default=1,
        help_text=_("Start time of the overlay, in seconds."),
    )
    time_end = models.PositiveIntegerField(
        _("End time"),
        default=2,
        help_text=_("End time of the overlay, in seconds."),
    )
    content = RichTextField(_("Content"), null=False, blank=False, config_name="complete")
    position = models.CharField(
        _("Position"),
        max_length=100,
        null=True,
        blank=False,
        choices=POSITION_CHOICES,
        default="bottom-right",
        help_text=_("Position of the overlay."),
    )
    background = models.BooleanField(
        _("Show background"),
        default=True,
        help_text=_("Show the background of the overlay."),
    )

    @property
    def sites(self):
        return self.video.sites

    class Meta:
        verbose_name = _("Overlay")
        verbose_name_plural = _("Overlays")
        ordering = ["time_start"]

    def clean(self):
        msg = list()
        msg += self.verify_title_items()
        msg += self.verify_time_items()
        msg += self.verify_overlap()
        if len(msg) > 0:
            raise ValidationError(msg)

    def verify_title_items(self):
        msg = list()
        if not self.title or self.title == "":
            msg.append(_("Please enter a title."))
        elif len(self.title) < 2 or len(self.title) > 100:
            msg.append(_("Please enter a title from 2 to 100 characters."))
        if len(msg) > 0:
            return msg
        else:
            return list()

    def verify_time_items(self):
        msg = list()
        if self.time_start > self.time_end:
            msg.append(
                _(
                    "The value of the time start field is greater than "
                    + "the value of the end time field."
                )
            )
        elif self.time_end > self.video.duration:
            msg.append(
                _("The value of time end field is greater than the " + "video duration.")
            )
        elif self.time_start == self.time_end:
            msg.append(_("Time end field and time start field can't " + "be equal."))
        if len(msg) > 0:
            return msg
        else:
            return list()

    def verify_overlap(self):
        msg = list()
        instance = None
        if self.slug:
            instance = Overlay.objects.get(slug=self.slug)
        list_overlay = Overlay.objects.filter(video=self.video)
        if instance:
            list_overlay = list_overlay.exclude(id=instance.id)
        if len(list_overlay) > 0:
            for element in list_overlay:
                if not (
                    self.time_start < element.time_start
                    and self.time_end <= element.time_start
                    or self.time_start >= element.time_end
                    and self.time_end > element.time_end
                ):
                    msg.append(
                        _(
                            "There is an overlap with the overlay {0},"
                            " please change time start and/or "
                            "time end values."
                        ).format(element.title)
                    )
            if len(msg) > 0:
                return msg
        return list()

    def save(self, *args, **kwargs):
        newid = -1
        if not self.id:
            try:
                newid = get_nextautoincrement(Overlay)
            except Exception:
                try:
                    newid = Overlay.objects.latest("id").id
                    newid += 1
                except Exception:
                    newid = 1
        else:
            newid = self.id
        newid = "{0}".format(newid)
        self.slug = "{0}-{1}".format(newid, slugify(self.title))
        super(Overlay, self).save(*args, **kwargs)

    def __str__(self):
        return "Overlay: {0} - Video: {1}".format(self.title, self.video)
