"""
Esup-Pod - Vote model.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from .Comment import Comment

User = get_user_model()


class Vote(models.Model):
    """
    Model representing a vote on a comment by a specific user.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_("User"),
        related_name="comment_votes",
    )
    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        verbose_name=_("Comment"),
        related_name="votes",
    )

    class Meta:
        """Vote metadata."""

        verbose_name = _("Vote")
        verbose_name_plural = _("Votes")
        unique_together = ("user", "comment")

    def __str__(self) -> str:
        """Render the vote as string."""
        return f"Vote by {self.user} on Comment {self.comment.id}"
