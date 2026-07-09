"""
Esup-Pod - Comment model.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Case, When, Value, BooleanField
from django.db.models.functions import Concat
from .Video import Video

from django.core.files.storage import default_storage

User = get_user_model()


class Comment(models.Model):
    """
    Model representing a comment on a video.
    Supports hierarchical threading with parent and direct_parent.
    """

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_("Author"),
        related_name="comments",
    )
    content = models.TextField(_("Content"))
    parent = models.ForeignKey(
        "self",
        related_name="children",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        verbose_name=_("Root Parent"),
        help_text=_("The top-level comment in the thread."),
    )
    direct_parent = models.ForeignKey(
        "self",
        related_name="direct_children",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        verbose_name=_("Direct Parent"),
        help_text=_("The comment being replied to directly."),
    )
    video = models.ForeignKey(
        Video,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name=_("Video"),
    )
    added = models.DateTimeField(_("Added At"), auto_now_add=True)

    class Meta:
        """Video comment metadata."""

        verbose_name = _("Comment")
        verbose_name_plural = _("Comments")
        ordering = ["added"]

    @property
    def number_vote(self) -> int:
        """Returns the number of votes for this comment."""
        return self.votes.count()

    @property
    def get_children(self):
        """Returns all children belonging to this root parent."""
        return Comment.objects.filter(parent_id=self.id).order_by("added")

    def get_json_children(self, user_id) -> list:
        """
        Optimized method to retrieve children in a dictionary format
        for JSON response, including annotations for votes and ownership.
        """
        children = list(
            self.get_children.annotate(nbr_vote=Count("votes", distinct=True))
            .annotate(
                author_name=Concat("author__last_name", Value(" "), "author__first_name")
            )
            .annotate(author_username=models.F("author__username"))
            .annotate(author_picture=models.F("author__owner__userpicture"))
            .annotate(
                is_owner=Case(
                    When(author__id=user_id, then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField(),
                )
            )
            .values(
                "id",
                "parent__id",
                "direct_parent__id",
                "is_owner",
                "author_name",
                "author_username",
                "author_picture",
                "added",
                "content",
                "nbr_vote",
            )
        )
        for child in children:
            if child["author_picture"]:
                child["author_picture"] = default_storage.url(child["author_picture"])
        return children

    def __str__(self) -> str:
        """Render the comment as string."""
        return self.content[:50]
