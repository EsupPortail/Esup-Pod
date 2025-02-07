"""Esup-Pod Podfile models."""

from django.db import models
from django.utils.translation import gettext as _
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.conf import settings
from django.template.defaultfilters import slugify
from django.dispatch import receiver
from django.db.models.signals import post_save
from sorl.thumbnail import delete
from itertools import chain
from operator import attrgetter

import traceback
import os
import logging
import mimetypes

logger = logging.getLogger(__name__)

FILES_DIR = getattr(settings, "FILES_DIR", "files")


class UserFolder(models.Model):
    """Folder that will contain custom files."""

    name = models.CharField(_("Name"), max_length=255)
    # parent = models.ForeignKey(
    #    'self', blank=True, null=True, related_name='children')
    owner = models.ForeignKey(User, verbose_name=_("Owner"), on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    access_groups = models.ManyToManyField(
        "authentication.AccessGroup",
        blank=True,
        verbose_name=_("Groups"),
        help_text=_(
            "Select one or more groups who can access in read only to this folder"
        ),
    )
    users = models.ManyToManyField(
        User,
        blank=True,
        verbose_name=_("Users"),
        related_name="shared_files",
        help_text=_(
            "Select one or more users who can access in read only to this folder"
        ),
    )

    class Meta:
        unique_together = (("name", "owner"),)
        verbose_name = _("User directory")
        verbose_name_plural = _("User directories")
        ordering = ["name"]
        app_label = "podfile"

    def clean(self) -> None:
        if self.name == "Home":
            same_home = UserFolder.objects.filter(owner=self.owner, name="Home")
            if same_home:
                raise ValidationError(
                    "A user cannot have have multiple home directories."
                )

    def __str__(self) -> str:
        return "{0}".format(self.name)

    def get_all_files(self) -> list:
        """Get all files in a UserFolder."""
        file_list = self.customfilemodel_set.all()
        image_list = self.customimagemodel_set.all()
        result_list = sorted(chain(image_list, file_list), key=attrgetter("uploaded_at"))
        return result_list

    def delete(self) -> None:
        """Delete a UserForlder and it's content."""
        for file in self.customfilemodel_set.all():
            file.delete()
        for img in self.customimagemodel_set.all():
            img.delete()
        super(UserFolder, self).delete()


@receiver(post_save, sender=User)
def create_owner_directory(sender, instance, created: bool, **kwargs) -> None:
    if created:
        try:
            UserFolder.objects.create(owner=instance, name="home")
        except Exception as e:
            msg = _("Create owner directory has failed.")
            msg += "{0}".format(e)
            msg += "\n{0}".format(traceback.format_exc())
            logger.error(msg)
            print(msg)


def get_upload_path_files(instance, filename) -> str:
    user_rep = (
        instance.created_by.owner.hashkey
        if (instance.created_by.owner)
        else instance.created_by.username
    )
    fname, dot, extension = filename.rpartition(".")
    try:
        fname.index("/")
        return os.path.join(
            FILES_DIR,
            user_rep,
            "%s/%s.%s"
            % (
                os.path.dirname(fname),
                slugify(os.path.basename(fname)),
                extension,
            ),
        )
    except ValueError:
        return os.path.join(FILES_DIR, user_rep, "%s.%s" % (slugify(fname), extension))


class BaseFileModel(models.Model):
    """Esup-Pod Base File Model."""

    name = models.CharField(_("Name"), max_length=255)
    description = models.CharField(max_length=255, blank=True)
    folder = models.ForeignKey(UserFolder, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        related_name="%(app_label)s_%(class)s_created",
        on_delete=models.CASCADE,
    )

    def save(self, **kwargs) -> None:
        """Save a BaseFile in DB."""
        path, ext = os.path.splitext(self.file.name)
        # if not self.name or self.name == "":
        self.name = os.path.basename(path)
        return super(BaseFileModel, self).save(**kwargs)

    def class_name(self) -> str:
        """Get the BaseFileModel class name."""
        return self.__class__.__name__

    def file_exist(self) -> bool:
        """Check if a BaseFileModel exist."""
        return self.file and os.path.isfile(self.file.path)

    class Meta:
        """BaseFileModel Metadata."""

        abstract = True
        ordering = ["name"]


class CustomFileModel(BaseFileModel):
    file = models.FileField(upload_to=get_upload_path_files, max_length=255)

    @property
    def file_ext(self) -> str:
        return self.file.path.rpartition(".")[-1].lower()

    @property
    def file_type(self) -> str:
        filetype = mimetypes.guess_type(self.file.path)[0]
        if filetype is None:
            filetype = self.file_ext
        return filetype

    file_type.fget.short_description = _("Get the file type")

    @property
    def file_size(self) -> int:
        return os.path.getsize(self.file.path)

    file_size.fget.short_description = _("Get the file size")

    def delete(self) -> None:
        if self.file:
            if os.path.isfile(self.file.path):
                os.remove(self.file.path)
        super(CustomFileModel, self).delete()

    def __str__(self) -> str:
        if self.file and os.path.isfile(self.file.path):
            return "%s (%s, %s)" % (self.name, self.file_type, self.file_size)
        else:
            return "%s" % (self.name)

    class Meta:
        verbose_name = _("Document")
        verbose_name_plural = _("Documents")
        app_label = "podfile"


class CustomImageModel(BaseFileModel):
    file = models.ImageField(upload_to=get_upload_path_files, max_length=255)

    @property
    def file_type(self) -> str:
        filetype = mimetypes.guess_type(self.file.path)[0]
        if filetype is None:
            fname, dot, extension = self.file.path.rpartition(".")
            filetype = extension.lower()
        return filetype

    file_type.fget.short_description = _("Get the file type")

    @property
    def file_size(self) -> int:
        return os.path.getsize(self.file.path)

    file_size.fget.short_description = _("Get the file size")

    def delete(self) -> None:
        if self.file:
            delete(self.file)
            if os.path.isfile(self.file.path):
                os.remove(self.file.path)
        super(CustomImageModel, self).delete()

    def __str__(self):
        if self.file and os.path.isfile(self.file.path):
            return "%s (%s, %s)" % (self.name, self.file_type, self.file_size)
        else:
            return "%s" % (self.name)

    class Meta:
        verbose_name = _("Image")
        verbose_name_plural = _("Images")
        app_label = "podfile"
