import os
import importlib

from ckeditor.fields import RichTextField
from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.db.models import Q
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.sites.models import Site
from pod.main.lang_settings import ALL_LANG_CHOICES as __ALL_LANG_CHOICES__
from pod.main.lang_settings import PREF_LANG_CHOICES as __PREF_LANG_CHOICES__
from pod.video.models import Type
from pod.video.models import Discipline, Channel, Theme
from pod.video.models import LANG_CHOICES as __LANG_CHOICES__
from pod.video.models import CURSUS_CODES as __CURSUS_CODES__
from pod.video.models import LICENCE_CHOICES as __LICENCE_CHOICES__
from pod.video.models import RESTRICT_EDIT_VIDEO_ACCESS_TO_STAFF_ONLY as __REVATSO__
from tagging.fields import TagField
from django.utils.translation import get_language

LANG_CHOICES = getattr(
    settings,
    "LANG_CHOICES",
    ((_("-- Frequently used languages --"), __PREF_LANG_CHOICES__), (_("-- All languages --"), __ALL_LANG_CHOICES__)),
)

__LANG_CHOICES_DICT__ = {
    key: value for key, value in LANG_CHOICES[0][1] + LANG_CHOICES[1][1]
}

USE_TRANSCRIPTION = getattr(settings, "USE_TRANSCRIPTION", False)
if USE_TRANSCRIPTION:
    TRANSCRIPTION_MODEL_PARAM = getattr(settings, "TRANSCRIPTION_MODEL_PARAM", {})
    TRANSCRIPTION_TYPE = getattr(settings, "TRANSCRIPTION_TYPE", "STT")

# FUNCTIONS


def get_transcription_choices():
    """Manage the transcription language choice table."""
    if USE_TRANSCRIPTION:
        transcript_lang = TRANSCRIPTION_MODEL_PARAM.get(TRANSCRIPTION_TYPE, {}).keys()
        transcript_choices_lang = []
        for lang in transcript_lang:
            transcript_choices_lang.append((lang, __LANG_CHOICES_DICT__[lang]))
        return transcript_choices_lang
    else:
        return []


def select_recorder_user():
    if __REVATSO__:
        return lambda q: (
            Q(is_staff=True) & (Q(first_name__icontains=q) | Q(last_name__icontains=q))
        ) & Q(owner__sites=Site.objects.get_current())
    else:
        return lambda q: (Q(first_name__icontains=q) | Q(last_name__icontains=q)) & Q(
            owner__sites=Site.objects.get_current()
        )


RECORDER_TYPE = getattr(
    settings,
    "RECORDER_TYPE",
    (
        ("video", _("Video")),
        ("audiovideocast", _("Audiovideocast")),
        ("studio", _("Studio")),
    ),
)
DEFAULT_RECORDER_PATH = getattr(settings, "DEFAULT_RECORDER_PATH", "/data/ftp-pod/ftp/")
DEFAULT_RECORDER_USER_ID = getattr(settings, "DEFAULT_RECORDER_USER_ID", 1)
DEFAULT_RECORDER_ID = getattr(settings, "DEFAULT_RECORDER_ID", 1)
PUBLIC_RECORD_DIR = getattr(settings, "PUBLIC_RECORD_DIR", "records")


class Recorder(models.Model):
    # Recorder name
    name = models.CharField(_("name"), max_length=200, unique=True)
    # Description of the recorder
    description = RichTextField(_("description"), config_name="complete", blank=True)
    # IP address of the recorder
    address_ip = models.GenericIPAddressField(
        _("Address IP"), unique=True, help_text=_("IP address of the recorder.")
    )
    # Salt for
    salt = models.CharField(
        _("salt"), max_length=50, blank=True, help_text=_("Recorder salt.")
    )

    # Recording type (video, AUdioVideoCasst, etc)
    recording_type = models.CharField(
        _("Recording Type"),
        max_length=50,
        choices=RECORDER_TYPE,
        default=RECORDER_TYPE[0][0],
    )
    # Manager of the recorder who received mails
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={"is_staff": True},
        help_text=_(
            "Manager of this recorder. This manager will receive recorder "
            "emails and he will be the owner of the published videos. If no "
            "user is selected, this recorder will use manual assign system."
        ),
        verbose_name=_("User"),
        null=True,
        blank=True,
    )
    # Additionnal additional_users
    additional_users = models.ManyToManyField(
        User,
        blank=True,
        verbose_name=_("Additional users"),
        related_name="users_recorders",
        help_text=_(
            "You can add additionals users to the recorder. They "
            "will become the additionnals owners of the published videos "
            "and will have the same rights as the owner except that they "
            "can't delete the published videos."
        ),
    )
    # Default type of published videos by this recorder
    type = models.ForeignKey(
        Type, on_delete=models.CASCADE, help_text=_("Video type by default.")
    )
    is_draft = models.BooleanField(
        verbose_name=_("Draft"),
        help_text=_(
            "If this box is checked, "
            "the video will be visible and accessible only by you "
            "and the additional owners."
        ),
        default=True,
    )
    is_restricted = models.BooleanField(
        verbose_name=_("Restricted access"),
        help_text=_(
            "If this box is checked, "
            "the video will only be accessible to authenticated users."
        ),
        default=False,
    )
    restrict_access_to_groups = models.ManyToManyField(
        Group,
        blank=True,
        verbose_name=_("Groups"),
        help_text=_("Select one or more groups who can access to this video"),
    )
    password = models.CharField(
        _("password"),
        help_text=_("Viewing this video will not be possible without this password."),
        max_length=50,
        blank=True,
        null=True,
    )
    cursus = models.CharField(
        _("University course"),
        max_length=1,
        choices=__CURSUS_CODES__,
        default="0",
        help_text=_("Select an university course as audience target of the content."),
    )
    main_lang = models.CharField(
        _("Main language"),
        max_length=2,
        choices=__LANG_CHOICES__,
        default=get_language(),
        help_text=_("Select the main language used in the content."),
    )
    transcript = models.CharField(
        _("Transcript"),
        max_length=2,
        choices=get_transcription_choices(),
        blank=True,
        help_text=_("Select an available language to transcribe the audio."),
    )
    tags = TagField(
        help_text=_(
            "Separate tags with spaces, "
            "enclose the tags consist of several words in quotation marks."
        ),
        verbose_name=_("Tags"),
    )
    discipline = models.ManyToManyField(
        Discipline, blank=True, verbose_name=_("Disciplines")
    )
    licence = models.CharField(
        _("Licence"), max_length=8, choices=__LICENCE_CHOICES__, blank=True, null=True
    )
    channel = models.ManyToManyField(Channel, verbose_name=_("Channels"), blank=True)
    theme = models.ManyToManyField(
        Theme,
        verbose_name=_("Themes"),
        blank=True,
        help_text=_(
            'Hold down "Control", or "Command" ' "on a Mac, to select more than one."
        ),
    )
    allow_downloading = models.BooleanField(
        _("allow downloading"),
        default=False,
        help_text=_("Check this box if you to allow downloading of the encoded files"),
    )
    is_360 = models.BooleanField(
        _("video 360"),
        default=False,
        help_text=_("Check this box if you want to use the 360 player for the video"),
    )
    disable_comment = models.BooleanField(
        _("Disable comment"),
        help_text=_("Allows you to turn off all comments on this video."),
        default=False,
    )

    # Directory name where videos of this recorder are published
    directory = models.CharField(
        _("Publication directory"),
        max_length=50,
        unique=True,
        help_text=_("Basic directory containing the videos published by the recorder."),
    )
    sites = models.ManyToManyField(Site)

    def __unicode__(self):
        return "%s - %s" % (self.name, self.address_ip)

    def __str__(self):
        return "%s - %s" % (self.name, self.address_ip)

    def ipunder(self):
        return self.address_ip.replace(".", "_")

    def save(self, *args, **kwargs):
        super(Recorder, self).save(*args, **kwargs)

    class Meta:
        verbose_name = _("Recorder")
        verbose_name_plural = _("Recorders")
        ordering = ["name"]


@receiver(post_save, sender=Recorder)
def default_site(sender, instance, created, **kwargs):
    if len(instance.sites.all()) == 0:
        instance.sites.add(Site.objects.get_current())


class Recording(models.Model):
    recorder = models.ForeignKey(
        Recorder,
        on_delete=models.CASCADE,
        verbose_name=_("Recorder"),
        default=DEFAULT_RECORDER_ID,
        help_text=_("Recorder that made this recording."),
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={"is_staff": True},
        default=DEFAULT_RECORDER_USER_ID,
        help_text=_("User who has made the recording"),
    )
    title = models.CharField(_("title"), max_length=200)
    type = models.CharField(
        _("Recording Type"),
        max_length=50,
        choices=RECORDER_TYPE,
        default=RECORDER_TYPE[0][0],
    )
    source_file = models.FilePathField(
        max_length=200, path=DEFAULT_RECORDER_PATH, unique=True, recursive=True
    )
    comment = models.TextField(_("Comment"), blank=True, default="")
    date_added = models.DateTimeField("date added", default=timezone.now, editable=False)

    @property
    def sites(self):
        return self.recorder.sites

    def __str__(self):
        return "%s" % self.title

    class Meta:
        verbose_name = _("Recording")
        verbose_name_plural = _("Recordings")

    def save(self, *args, **kwargs):
        super(Recording, self).save(*args, **kwargs)

    def clean(self):
        msg = list()
        msg = self.verify_attributs()
        if len(msg) > 0:
            raise ValidationError(msg)

    def verify_attributs(self):
        msg = list()
        if not self.type:
            msg.append(_("Please specify a type."))
        elif self.type not in dict(RECORDER_TYPE):
            msg.append(_("Please use the only type in type choices."))
        if not self.source_file:
            msg.append(_("Please specify a source file."))
        elif not os.path.exists(self.source_file):
            msg.append(_("Source file doesn't exists"))
        return msg


@receiver(post_save, sender=Recording)
def process_recording(sender, instance, created, **kwargs):
    if created and os.path.exists(instance.source_file):
        mod = importlib.import_module("%s.plugins.type_%s" % (__package__, instance.type))
        mod.process(instance)


class RecordingFileTreatment(models.Model):
    file = models.FilePathField(
        path=DEFAULT_RECORDER_PATH,
        recursive=True,
        unique=True,
        help_text=_("Source file of the published video."),
    )
    file_size = models.BigIntegerField(_("File size"), default=0)
    recorder = models.ForeignKey(
        Recorder,
        on_delete=models.CASCADE,
        verbose_name=_("Recorder"),
        null=True,
        help_text=_("Recorder that made this recording."),
    )
    date_added = models.DateTimeField(
        _("Date added"), default=timezone.now, editable=True
    )
    require_manual_claim = models.BooleanField(
        _("Require manual claim?"),
        default=False,
        help_text=_("Has this recording file require a manual claim by a user?"),
    )
    email_sent = models.BooleanField(
        _("Email sent?"),
        default=False,
        help_text=_("Has an email been sent to the manager of the concerned recorder?"),
    )
    date_email_sent = models.DateTimeField(
        _("Date email sent"), blank=True, null=True, editable=False
    )
    type = models.CharField(
        max_length=50, choices=RECORDER_TYPE, default=RECORDER_TYPE[0][0]
    )

    @property
    def sites(self):
        return self.recorder.sites

    def filename(self):
        return os.path.basename(self.file)

    def publicfileurl(self):
        return os.path.join(
            settings.MEDIA_URL,
            PUBLIC_RECORD_DIR,
            self.recorder.directory,
            os.path.basename(self.file),
        )

    class Meta:
        verbose_name = _("Recording file treatment")
        verbose_name_plural = _("Recording file treatments")


class RecordingFile(models.Model):
    file = models.FileField(upload_to="uploads/")
    recorder = models.ForeignKey(
        Recorder,
        on_delete=models.CASCADE,
        default=DEFAULT_RECORDER_ID,
        verbose_name=_("Recorder"),
        help_text=_("Recorder that made this recording."),
    )

    class Meta:
        verbose_name = _("Recording file")
        verbose_name_plural = _("Recording files")

    @property
    def sites(self):
        return self.recorder.sites


@receiver(post_save, sender=RecordingFile)
def process_recording_file(sender, instance, created, **kwargs):
    if created and instance.file and os.path.isfile(instance.file.path):
        # deplacement du fichier source vers destination
        create_recording(instance)


def create_recording(recordingFile):
    new_path = os.path.join(
        DEFAULT_RECORDER_PATH, os.path.basename(recordingFile.file.path)
    )
    nom, ext = os.path.splitext(os.path.basename(recordingFile.file.path))
    ext = ext.lower()
    os.rename(recordingFile.file.path, new_path)
    user = User.objects.get(id=DEFAULT_RECORDER_USER_ID)
    Recording.objects.create(
        user=user,
        title=nom,
        source_file=new_path,
        recorder=recordingFile.recorder,
        type=recordingFile.recorder.recording_type,
    )
