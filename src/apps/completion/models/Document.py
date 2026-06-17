"""
Esup-Pod - Document model.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from src.apps.encoding.services.storage import get_storage_path_document


class Document(models.Model):
    """
    Documents attached to a video.
    Replaces V4 Document which had a foreign key to CustomFileModel.
    """

    video = models.ForeignKey(
        "video.Video",
        on_delete=models.CASCADE,
        related_name="documents",
        verbose_name=_("Video"),
    )
    title = models.CharField(max_length=250, verbose_name=_("Title"))
    file = models.FileField(upload_to=get_storage_path_document, verbose_name=_("File"))
    is_private = models.BooleanField(default=False, verbose_name=_("Private document"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Meta options for Document."""

        verbose_name = _("Document")
        verbose_name_plural = _("Documents")
        permissions = [
            ("add_document_anywhere", _("Can add/manage documents on ANY video")),
        ]

    def __str__(self):
        return f"{self.title} on {self.video}"
