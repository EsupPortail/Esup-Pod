from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext as _

from pod.video.models import Video


class Quiz(models.Model):
    """Quiz model."""
    video = models.OneToOneField(Video, verbose_name=_(
        "Video"), on_delete=models.CASCADE)
    connected_user_only = models.BooleanField(
        verbose_name=_("Connected user only"),
        default=False,
        help_text=_("Please choose if this quiz is only for connected users or not."),
    )
    activated_statistics = models.BooleanField(
        verbose_name=_("Activated statistics"),
        default=False,
        help_text=_("Please choose if the statistics are activated or not."),
    )
    show_correct_answers = models.BooleanField(
        verbose_name=_("Show correct answers"),
        default=False,
        help_text=_("Please choose if the correct answers will be displayed or not."),
    )

    class Meta:
        ordering = ["id"]
        verbose_name = _("Quiz")
        verbose_name_plural = _("Quizzes")

        constraints = [
            models.UniqueConstraint(
                fields=["video"],
                name="unique_video",
            ),
        ]


class Question(models.Model):
    """Question model."""
    quiz = models.ForeignKey(Quiz, verbose_name=_(
        "Quiz"), on_delete=models.CASCADE)
    title = models.CharField(
        verbose_name=_("Title"),
        max_length=250,
        default=_("Question"),
        help_text=_("Please choose a title between 1 and 250 characters."),
    )
    explanation = models.TextField(
        verbose_name=_("Explanation"),
        blank=True,
        default="",
        help_text=_("Please choose an explanation."),
    )
    start_timestamp = models.IntegerField(
        verbose_name=_("Start timestamp"),
        null=True,
        help_text=_("Please choose the beginning time of the answer in the video."),
    )
    end_timestamp = models.IntegerField(
        verbose_name=_("End timestamp"),
        null=True,
        help_text=_("Please choose the end time of the answer in the video."),
    )

    class Meta:
        ordering = ["id"]
        abstract = True
        verbose_name = _("Question")
        verbose_name_plural = _("Questions")

        constraints = [
            models.UniqueConstraint(
                fields=["quiz", "title"],
                name="unique_title",
            ),
        ]

    def clean(self):
        super().clean()

        # Check if start_timestamp is greater than end_timestamp
        if self.start_timestamp is not None and self.end_timestamp is not None and self.start_timestamp >= self.end_timestamp:
            raise ValidationError(_("Start timestamp must be lower than end timestamp."))

        # Check if end_timestamp is defined without start_timestamp
        if self.end_timestamp is not None and self.start_timestamp is None:
            raise ValidationError(
                _("End timestamp cannot be defined without a start timestamp."))

    def __str__(self):
        return self.title
