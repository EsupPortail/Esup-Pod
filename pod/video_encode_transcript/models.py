"""Models for Esup-Pod video_encode."""

import os

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator
from django.db import models
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from pod.recorder.models import Recording
from pod.video.models import Video, get_storage_path_video

ENCODING_CHOICES = getattr(
    settings,
    "ENCODING_CHOICES",
    (
        ("audio", "audio"),
        ("360p", "360p"),
        ("480p", "480p"),
        ("720p", "720p"),
        ("1080p", "1080p"),
        ("playlist", "playlist"),
    ),
)

FORMAT_CHOICES = getattr(
    settings,
    "FORMAT_CHOICES",
    (
        ("video/mp4", "video/mp4"),
        ("video/mp2t", "video/mp2t"),
        ("video/webm", "video/webm"),
        ("audio/mp3", "audio/mp3"),
        ("audio/wav", "audio/wav"),
        ("application/x-mpegURL", "application/x-mpegURL"),
    ),
)

SITE_ID = getattr(settings, "SITE_ID", 1)


class VideoRendition(models.Model):
    """Model representing the rendition video."""

    resolution = models.CharField(
        _("resolution"),
        max_length=50,
        unique=True,
        help_text=_(
            "Please use the only format x. i.e.: "
            + "<em>640x360</em> or <em>1280x720</em>"
            + " or <em>1920x1080</em>."
        ),
    )
    minrate = models.CharField(
        _("minrate"),
        max_length=50,
        help_text=_(
            "Please use the only format k. i.e.: "
            + "<em>300k</em> or <em>600k</em>"
            + " or <em>1000k</em>."
        ),
    )
    video_bitrate = models.CharField(
        _("bitrate video"),
        max_length=50,
        help_text=_(
            "Please use the only format k. i.e.: "
            + "<em>300k</em> or <em>600k</em>"
            + " or <em>1000k</em>."
        ),
    )
    maxrate = models.CharField(
        _("maxrate"),
        max_length=50,
        help_text=_(
            "Please use the only format k. i.e.: "
            + "<em>300k</em> or <em>600k</em>"
            + " or <em>1000k</em>."
        ),
    )
    encoding_resolution_threshold = models.PositiveIntegerField(
        _("encoding resolution threshold"),
        default=0,
        validators=[MaxValueValidator(100)],
    )
    audio_bitrate = models.CharField(
        _("bitrate audio"),
        max_length=50,
        help_text=_(
            "Please use the only format k. i.e.: "
            + "<em>300k</em> or <em>600k</em>"
            + " or <em>1000k</em>."
        ),
    )
    encode_mp4 = models.BooleanField(_("Make a MP4 version"), default=False)
    sites = models.ManyToManyField(Site)

    @property
    def height(self) -> int:
        """The height of the video rendition based on the resolution."""
        return int(self.resolution.split("x")[1])

    @property
    def width(self) -> int:
        """The width of the video rendition based on the resolution."""
        return int(self.resolution.split("x")[0])

    class Meta:
        # ordering = ['height'] # Not work
        verbose_name = _("rendition")
        verbose_name_plural = _("renditions")

    def __str__(self) -> str:
        return "VideoRendition num %s with resolution %s" % (
            "%04d" % self.id,
            self.resolution,
        )

    def bitrate(self, field_value, field_name, name=None) -> None:
        """Validate the bitrate field value."""
        if name is None:
            name = field_name
        if field_value and "k" not in field_value:
            msg = "Error in %s: " % _(name)
            raise ValidationError(
                "%s %s" % (msg, VideoRendition._meta.get_field(field_name).help_text)
            )
        else:
            vb = field_value.replace("k", "")
            if not vb.isdigit():
                msg = "Error in %s: " % _(name)
                raise ValidationError(
                    "%s %s"
                    % (msg, VideoRendition._meta.get_field(field_name).help_text)
                )

    def clean_bitrate(self) -> None:
        """Clean the bitrate-related fields."""
        self.bitrate(self.video_bitrate, "video_bitrate", "bitrate video")
        self.bitrate(self.maxrate, "maxrate")
        self.bitrate(self.minrate, "minrate")

    def clean(self) -> None:
        """Clean the fields of the VideoRendition model."""
        if self.resolution and "x" not in self.resolution:
            raise ValidationError(
                VideoRendition._meta.get_field("resolution").help_text
            )
        else:
            res = self.resolution.replace("x", "")
            if not res.isdigit():
                raise ValidationError(
                    VideoRendition._meta.get_field("resolution").help_text
                )

        self.clean_bitrate()
        self.bitrate(self.audio_bitrate, "audio_bitrate", "bitrate audio")


@receiver(post_save, sender=VideoRendition)
def default_site_videorendition(sender, instance, created: bool, **kwargs) -> None:
    """Add the current site as a default site."""
    if instance.sites.count() == 0:
        instance.sites.add(Site.objects.get_current())


class EncodingVideo(models.Model):
    """Model representing the encoding video for a video."""

    name = models.CharField(
        _("Name"),
        max_length=10,
        choices=ENCODING_CHOICES,
        default="360p",
        help_text=_("Please use the only format in encoding choices:")
        + " %s" % " ".join(str(key) for key, value in ENCODING_CHOICES),
    )
    video = models.ForeignKey(Video, verbose_name=_("Video"), on_delete=models.CASCADE)
    rendition = models.ForeignKey(
        VideoRendition, verbose_name=_("rendition"), on_delete=models.CASCADE
    )
    encoding_format = models.CharField(
        _("Format"),
        max_length=22,
        choices=FORMAT_CHOICES,
        default="video/mp4",
        help_text=_("Please use the only format in format choices:")
        + " %s" % " ".join(str(key) for key, value in FORMAT_CHOICES),
    )
    source_file = models.FileField(
        _("encoding source file"),
        upload_to=get_storage_path_video,
        max_length=255,
    )

    @property
    def sites(self):
        """Property representing the sites associated with the video."""
        return self.video.sites

    @property
    def sites_all(self):
        """Property representing all the sites associated with the video."""
        return self.video.sites_set.all()

    def clean(self) -> None:
        """Validate the encoding video model."""
        if self.name:
            if self.name not in dict(ENCODING_CHOICES):
                raise ValidationError(EncodingVideo._meta.get_field("name").help_text)
        if self.encoding_format:
            if self.encoding_format not in dict(FORMAT_CHOICES):
                raise ValidationError(
                    EncodingVideo._meta.get_field("encoding_format").help_text
                )

    class Meta:
        ordering = ["name"]
        verbose_name = _("Encoding video")
        verbose_name_plural = _("Encoding videos")

    def __str__(self) -> str:
        return "EncodingVideo num: %s with resolution %s for video %s in %s" % (
            "%04d" % self.id,
            self.name,
            self.video.id,
            self.encoding_format,
        )

    @property
    def owner(self):
        """Property representing the owner of the video."""
        return self.video.owner

    @property
    def height(self) -> int:
        """Property representing the height of the video rendition."""
        return int(self.rendition.resolution.split("x")[1])

    @property
    def width(self) -> int:
        """Property representing the width of the video rendition."""
        return int(self.rendition.resolution.split("x")[0])

    def delete(self) -> None:
        """Delete the encoding video."""
        if self.source_file:
            if os.path.isfile(self.source_file.path):
                os.remove(self.source_file.path)
        super(EncodingVideo, self).delete()


class EncodingAudio(models.Model):
    """Model representing the encoding audio for a video."""

    name = models.CharField(
        _("Name"),
        max_length=10,
        choices=ENCODING_CHOICES,
        default="audio",
        help_text=_("Please use the only format in encoding choices:")
        + " %s" % " ".join(str(key) for key, value in ENCODING_CHOICES),
    )
    video = models.ForeignKey(Video, verbose_name=_("Video"), on_delete=models.CASCADE)
    encoding_format = models.CharField(
        _("Format"),
        max_length=22,
        choices=FORMAT_CHOICES,
        default="audio/mp3",
        help_text=_("Please use the only format in format choices:")
        + " %s" % " ".join(str(key) for key, value in FORMAT_CHOICES),
    )
    source_file = models.FileField(
        _("encoding source file"),
        upload_to=get_storage_path_video,
        max_length=255,
    )

    @property
    def sites(self):
        """Property representing the sites associated with the video."""
        return self.video.sites

    @property
    def sites_all(self):
        """Property representing all the sites associated with the video."""
        return self.video.sites_set.all()

    class Meta:
        ordering = ["name"]
        verbose_name = _("Encoding audio")
        verbose_name_plural = _("Encoding audios")

    def clean(self) -> None:
        """Validate the encoding audio model."""
        if self.name:
            if self.name not in dict(ENCODING_CHOICES):
                raise ValidationError(EncodingAudio._meta.get_field("name").help_text)
        if self.encoding_format:
            if self.encoding_format not in dict(FORMAT_CHOICES):
                raise ValidationError(
                    EncodingAudio._meta.get_field("encoding_format").help_text
                )

    def __str__(self) -> str:
        return "EncodingAudio num: %s for video %s in %s" % (
            "%04d" % self.id,
            self.video.id,
            self.encoding_format,
        )

    @property
    def owner(self):
        """Property representing the owner of the video."""
        return self.video.owner

    def delete(self) -> None:
        """Delete the encoding audio, including the source file if it exists."""
        if self.source_file:
            if os.path.isfile(self.source_file.path):
                os.remove(self.source_file.path)
        super(EncodingAudio, self).delete()


class EncodingLog(models.Model):
    """Model representing the encoding log for a video."""

    video = models.OneToOneField(
        Video, verbose_name=_("Video"), editable=False, on_delete=models.CASCADE
    )
    log = models.TextField(null=True, blank=True, editable=False)
    logfile = models.FileField(max_length=255, blank=True, null=True)

    @property
    def sites(self):
        """Property representing the sites associated with the video."""
        return self.video.sites

    @property
    def sites_all(self):
        """Property representing all the sites associated with the video."""
        return self.video.sites_set.all()

    class Meta:
        ordering = ["video"]
        verbose_name = _("Encoding log")
        verbose_name_plural = _("Encoding logs")

    def __str__(self):
        return "Log for encoding video %s" % (self.video.id)


class EncodingStep(models.Model):
    """Model representing an encoding step for a video."""

    video = models.OneToOneField(
        Video, verbose_name=_("Video"), editable=False, on_delete=models.CASCADE
    )
    num_step = models.IntegerField(default=0, editable=False)
    desc_step = models.CharField(null=True, max_length=255, blank=True, editable=False)

    @property
    def sites(self):
        """Property representing the sites associated with the video."""
        return self.video.sites

    @property
    def sites_all(self):
        """Property representing all the sites associated with the video."""
        return self.video.sites_set.all()

    class Meta:
        ordering = ["video"]
        verbose_name = _("Encoding step")
        verbose_name_plural = _("Encoding steps")

    def __str__(self):
        return "Step for encoding video %s" % (self.video.id)


class PlaylistVideo(models.Model):
    name = models.CharField(
        _("Name"),
        max_length=10,
        choices=ENCODING_CHOICES,
        default="360p",
        help_text=_("Please use the only format in encoding choices:")
        + " %s" % " ".join(str(key) for key, value in ENCODING_CHOICES),
    )
    video = models.ForeignKey(Video, verbose_name=_("Video"), on_delete=models.CASCADE)
    encoding_format = models.CharField(
        _("Format"),
        max_length=22,
        choices=FORMAT_CHOICES,
        default="application/x-mpegURL",
        help_text=_("Please use the only format in format choices:")
        + " %s" % " ".join(str(key) for key, value in FORMAT_CHOICES),
    )
    source_file = models.FileField(
        _("encoding source file"),
        upload_to=get_storage_path_video,
        max_length=255,
    )

    class Meta:
        verbose_name = _("Video Playlist")
        verbose_name_plural = _("Video Playlists")

    @property
    def sites(self):
        return self.video.sites

    @property
    def sites_all(self):
        return self.video.sites_set.all()

    def clean(self) -> None:
        """Validate some PlaylistVideomodels fields."""
        if self.name:
            if self.name not in dict(ENCODING_CHOICES):
                raise ValidationError(
                    PlaylistVideo._meta.get_field("name").help_text, code="invalid_name"
                )
        if self.encoding_format:
            if self.encoding_format not in dict(FORMAT_CHOICES):
                raise ValidationError(
                    PlaylistVideo._meta.get_field("encoding_format").help_text,
                    code="invalid_encoding",
                )

    def __str__(self) -> str:
        return "Playlist num: %s for video %s in %s" % (
            "%04d" % self.id,
            self.video.id,
            self.encoding_format,
        )

    @property
    def owner(self):
        return self.video.owner

    def delete(self) -> None:
        if self.source_file:
            if os.path.isfile(self.source_file.path):
                os.remove(self.source_file.path)
        super(PlaylistVideo, self).delete()


class RunnerManager(models.Model):
    """Hold information about runner manager."""

    # Runner manager name
    name = models.CharField(
        max_length=250,
        verbose_name=_("Runner manager name"),
        help_text=_("Runner manager name"),
    )

    # Priority
    priority = models.IntegerField(
        verbose_name=_("Priority"),
        help_text=_(
            "Priority of the runner manager. Lower values indicate higher priority."
        ),
        default=1,
    )

    # Runner manager URL
    # Format: https://manager.univ.fr:port/
    url = models.CharField(
        max_length=250,
        verbose_name=_("URL of the runner manager"),
        help_text=_("Example format: https://manager.univ.fr:port/"),
    )

    # Bearer token for the runner manager server (e.g. `6YqG_73xt-9s8v5aBz`)
    token = models.CharField(
        max_length=50,
        verbose_name=_("Bearer token for the runner manager."),
        help_text=_("Example format: 6YqG_73xt-9s8v5aBz"),
    )

    # Site
    site = models.ForeignKey(
        Site,
        verbose_name=_("Site"),
        on_delete=models.CASCADE,
        default=1,
    )

    def __unicode__(self):
        return "%s (%s)" % (self.name, self.site.id)

    def __str__(self):
        return "%s (%s)" % (self.name, self.site.id)

    def save(self, *args, **kwargs):
        super(RunnerManager, self).save(*args, **kwargs)

    class Meta:
        db_table = "runner_manager"
        verbose_name = _("Runner manager")
        verbose_name_plural = _("Runner managers")
        constraints = [
            models.UniqueConstraint(
                fields=["url", "site"],
                name="runner_manager_unique_url_site",
            ),
        ]


@receiver(pre_save, sender=RunnerManager)
def default_site_runner_manager(sender, instance, **kwargs):
    """Save default site for this runner manager."""
    if not hasattr(instance, "site"):
        instance.site = Site.objects.get_current()


class Task(models.Model):
    """Hold information about tasks managed by the runner managers."""

    # Task type
    TYPE = (
        ("encoding", _("Encoding task")),
        ("studio", _("Studio task")),
        ("transcription", _("Transcription task")),
    )
    type = models.CharField(
        max_length=30,
        verbose_name=_("Task type"),
        choices=TYPE,
        default=TYPE[0][0],
    )

    # Task status
    STATUS = (
        ("pending", _("Task pending")),
        ("running", _("Task in progress")),
        ("completed", _("Task completed")),
        ("failed", _("Task failed")),
        ("timeout", _("Task timeouted")),
    )
    status = models.CharField(
        max_length=30,
        verbose_name=_("Task status"),
        choices=STATUS,
        default=STATUS[0][0],
    )
    # Task identifier from runner manager
    task_id = models.CharField(
        max_length=100,
        verbose_name=_("Task identifier from runner manager"),
        help_text=_("Identifier of the task provided by the runner manager"),
        null=True,
        blank=True,
    )

    # Video associated to the task
    video = models.ForeignKey(
        Video,
        on_delete=models.CASCADE,
        verbose_name=_("Video"),
        help_text=_("Video associated to the task"),
        null=True,
        blank=True,
    )

    # Recording associated to the task (for Studio tasks)
    recording = models.ForeignKey(
        Recording,
        on_delete=models.CASCADE,
        verbose_name=_("Recording"),
        help_text=_("Studio recording associated to the task"),
        null=True,
        blank=True,
    )

    # Runner manager that manages this task
    runner_manager = models.ForeignKey(
        RunnerManager,
        on_delete=models.CASCADE,
        verbose_name=_("Runner manager that manages this task"),
        help_text=_("Runner manager that achieves this task"),
        null=True,
        blank=True,
    )

    # Date task added
    date_added = models.DateTimeField(
        verbose_name=_("Date added"), default=timezone.now, editable=False
    )

    # Queue rank for pending tasks
    rank = models.IntegerField(
        verbose_name=_("Queue rank"),
        help_text=_("Rank of the task in the pending queue"),
        null=True,
        blank=True,
        default=None,
    )

    # Script output
    script_output = models.TextField(
        verbose_name=_("Script output"),
        help_text=_("Output from the runner manager script"),
        null=True,
        blank=True,
    )

    def __unicode__(self):
        ref = (
            self.video.id
            if self.video_id
            else (self.recording.id if self.recording_id else "-")
        )
        return "%s - %s - %s" % (ref, self.type, self.status)

    def __str__(self):
        ref = (
            self.video.id
            if self.video_id
            else (self.recording.id if self.recording_id else "-")
        )
        return "%s - %s - %s" % (ref, self.type, self.status)

    def save(self, *args, **kwargs):
        super(Task, self).save(*args, **kwargs)

    class Meta:
        db_table = "runner_manager_task"
        verbose_name = _("Task")
        verbose_name_plural = _("Tasks")
        ordering = ["id"]
