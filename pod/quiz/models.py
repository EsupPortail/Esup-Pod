"""EsupQuiz models."""

from json import JSONDecodeError, loads
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext as _

from pod.video.models import Video


class Quiz(models.Model):
    """
    Quiz model.

    Attributes:
        video (OneToOneField <Video>): Video of the quiz.
        connected_user_only (BooleanField): Connected user only.
        activated_statistics (BooleanField): Activated statistics.
        show_correct_answers (BooleanField): Show correct answers.
    """

    video = models.OneToOneField(Video, verbose_name=_("Video"), on_delete=models.CASCADE)
    connected_user_only = models.BooleanField(
        verbose_name=_("Connected user only"),
        default=False,
        help_text=_("Please choose if this quiz is only for connected users or not."),
    )
    # activated_statistics = models.BooleanField(
    #     verbose_name=_("Activated statistics"),
    #     default=False,
    #     help_text=_("Please choose if the statistics are activated or not."),
    # )
    show_correct_answers = models.BooleanField(
        verbose_name=_("Show correct answers"),
        default=True,
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

    def clean(self):
        super().clean()

    def get_questions(self):
        from pod.quiz.utils import get_quiz_questions

        return get_quiz_questions(self)


class Question(models.Model):
    """
    Question model.

    Attributes:
        quiz (ForeignKey <Quiz>): Quiz of the question.
        title (CharField): Title of the question.
        explanation (TextField): Explanation of the question.
        start_timestamp (IntegerField): Start timestamp of the answer in the video.
        end_timestamp (IntegerField): End timestamp of the answer in the video.
    """

    quiz = models.ForeignKey(Quiz, verbose_name=_("Quiz"), on_delete=models.CASCADE)
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
        if (
            self.start_timestamp is not None
            and self.end_timestamp is not None
            and self.start_timestamp >= self.end_timestamp
        ):
            raise ValidationError(_("Start timestamp must be lower than end timestamp."))

        # Check if end_timestamp is defined without start_timestamp
        if self.end_timestamp is not None and self.start_timestamp is None:
            raise ValidationError(
                _("End timestamp cannot be defined without a start timestamp.")
            )

    def __str__(self):
        return self.title

    def get_question_form(self, data=None):
        from pod.quiz.forms import (
            LongAnswerQuestionForm,
            MultipleChoiceQuestionForm,
            ShortAnswerQuestionForm,
            UniqueChoiceQuestionForm,
        )

        if isinstance(self, UniqueChoiceQuestion):
            return UniqueChoiceQuestionForm(
                data, instance=self, prefix=f"question_{self.pk}"
            )
        elif isinstance(self, MultipleChoiceQuestion):
            return MultipleChoiceQuestionForm(
                data, instance=self, prefix=f"question_{self.pk}"
            )
        elif isinstance(self, ShortAnswerQuestion):
            return ShortAnswerQuestionForm(
                data, instance=self, prefix=f"question_{self.pk}"
            )
        elif isinstance(self, LongAnswerQuestion):
            return LongAnswerQuestionForm(
                data, instance=self, prefix=f"question_{self.pk}"
            )
        else:
            return None

    def get_answer(self):
        return None

    def get_type(self):
        return None


class UniqueChoiceQuestion(Question):
    """
    Unique choice question model.

    Attributes:
        choices (JSONField <{choice(str): is_correct(bool)}>): Choices of the question.
    """

    choices = models.JSONField(
        verbose_name=_("Choices"),
        default=dict,
        help_text=_(
            "Choices must be like this: {'choice 1': true, 'choice 2': false, ...} | true for the right choice, false for the wrong choices"
        ),
    )

    class Meta:
        verbose_name = _("Unique choice question")
        verbose_name_plural = _("Unique choice questions")

    def clean(self):
        super().clean()

        if isinstance(self.choices, str):
            try:
                self.choices = loads(self.choices)
            except JSONDecodeError:
                return

        # Check if there are at least 2 choices
        if len(self.choices) < 2:
            raise ValidationError(_("There must be at least 2 choices."))

        # Check if there is only one correct answer
        if sum([1 for choice in self.choices.values() if choice]) != 1:
            raise ValidationError(_("There must be only one correct answer."))

    def __str__(self):
        return self.title

    def get_answer(self):
        if isinstance(self.choices, str):
            try:
                self.choices = loads(self.choices)
            except JSONDecodeError:
                raise ValidationError(_("Invalid JSON format for choices."))
        correct_answer = next(
            choice for choice, is_correct in self.choices.items() if is_correct
        )
        return correct_answer

    def get_type(self):
        return "unique_choice"


class MultipleChoiceQuestion(Question):
    """
    Multiple choice question model.

    Attributes:
        choices (JSONField <{question(str): is_correct(bool)}>): Choices of the question.
    """

    choices = models.JSONField(
        verbose_name="Choices",
        default=dict,
    )

    class Meta:
        verbose_name = "Multiple choice question"
        verbose_name_plural = "Multiple choice questions"

    def clean(self):
        super().clean()

        # Check if there are at least 2 choices
        if len(self.choices) < 2:
            raise ValidationError("There must be at least 2 choices.")

        # Check if there is at least one correct answer
        if not any(self.choices.values()):
            raise ValidationError("There must be at least one correct answer.")

    def __str__(self):
        return self.title

    def get_type(self):
        return "multiple_choice"


class TrueFalseQuestion(Question):
    """
    True/false question model.

    Attributes:
        is_true (BooleanField): Is true.
    """

    is_true = models.BooleanField(
        verbose_name="Is true",
        default=True,
        help_text="Please choose if the answer is true or false.",
    )

    class Meta:
        verbose_name = "True/false question"
        verbose_name_plural = "True/false questions"

    def __str__(self):
        return self.title

    def get_type(self):
        return "true_false"


class ShortAnswerQuestion(Question):
    """
    Short answer question model.

    Attributes:
        answer (CharField): Answer of the question.
    """

    answer = models.CharField(
        verbose_name="Answer",
        max_length=250,
        default="",
        help_text="Please choose an answer between 1 and 250 characters.",
    )

    class Meta:
        verbose_name = "Short answer question"
        verbose_name_plural = "Short answer questions"

    def __str__(self):
        return self.title

    def get_answer(self):
        return self.answer

    def get_type(self):
        return "short_answer"


class LongAnswerQuestion(Question):
    """
    Long answer question model.

    Attributes:
        answer (TextField): Answer of the question.
    """

    answer = models.TextField(
        verbose_name="Answer",
        default="",
        help_text="Please choose an answer.",
    )

    class Meta:
        verbose_name = "Long answer question"
        verbose_name_plural = "Long answer questions"

    def __str__(self):
        return self.title

    def get_answer(self):
        return self.answer

    def get_type(self):
        return "long_answer"
