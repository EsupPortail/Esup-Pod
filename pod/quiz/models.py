"""Esup-Pod quiz models."""

import uuid
from json import JSONDecodeError, loads
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext as _

from pod.video.models import Video


class Quiz(models.Model):
    """
    Quiz model.

    Attributes:
        video (OneToOneField <Video>): Video of the quiz.
        connected_user_only (BooleanField): Connected user only.
        show_correct_answers (BooleanField): Show correct answers.
    """

    video = models.OneToOneField(
        Video,
        verbose_name=_("Video"),
        on_delete=models.CASCADE,
        help_text=_("Choose a video associated with the quiz."),
    )
    connected_user_only = models.BooleanField(
        verbose_name=_("Connected user only"),
        default=False,
        help_text=_("Choose if this quiz is only for connected users or not."),
    )
    show_correct_answers = models.BooleanField(
        verbose_name=_("Show correct answers"),
        default=True,
        help_text=_("Choose if the correct answers will be displayed or not."),
    )

    is_draft = models.BooleanField(
        verbose_name=_("Draft"),
        help_text=_(
            "If this box is checked, "
            "the quiz will be visible and accessible only by you "
            "and the additional owners."
        ),
        default=False,
    )

    class Meta:
        """Quiz Metadata."""

        ordering = ["id"]
        verbose_name = _("Quiz")
        verbose_name_plural = _("Quizzes")

        constraints = [
            models.UniqueConstraint(
                fields=["video"],
                name="unique_video",
            ),
        ]

    def __str__(self) -> str:
        """Represent the quiz as string."""
        return _("Quiz of video") + " " + str(self.video)

    def get_questions(self) -> list:
        """
        Retrieve questions associated with the quiz.

        Returns:
            list[Question]: List of questions associated with the quiz.
        """
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

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quiz = models.ForeignKey(
        Quiz,
        verbose_name=_("Quiz"),
        on_delete=models.CASCADE,
        help_text=_("Choose a quiz associated with the question."),
    )
    title = models.CharField(
        verbose_name=_("Title"),
        max_length=250,
        help_text=_("Please choose a title between 1 and %(max)s characters.")
        % {"max": 250},
    )
    explanation = models.TextField(
        verbose_name=_("Explanation"),
        blank=True,
        default="",
        help_text=_("Please choose an explanation."),
    )
    start_timestamp = models.PositiveIntegerField(
        verbose_name=_("Start timestamp"),
        null=True,
        help_text=_("The start time of the answer in the video (in seconds)."),
    )
    end_timestamp = models.PositiveIntegerField(
        verbose_name=_("End timestamp"),
        null=True,
        help_text=_("The end time of the answer in the video (in seconds)."),
    )

    class Meta:
        """Question Metadata."""

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

    def clean(self) -> None:
        """Clean method for Question model."""
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

    def __str__(self) -> str:
        """Represent the question as string."""
        return _("Question “%s”") % self.title

    def get_question_form(self, data=None):
        """
        Get the form for the question.

        Args:
            data (dict): Form data.

        Returns:
            QuestionForm: Form for the question.
        """
        raise NotImplementedError(
            "Subclasses of Question must implement get_question_form method."
        )

    def get_answer(self) -> None:
        """
        Get the answer for the question.

        Returns:
            str: Answer for the question.
        """
        raise NotImplementedError(
            "Subclasses of Question must implement get_answer method."
        )

    def get_type(self) -> None:
        """
        Get the type of the question.

        Returns:
            str: Type of the question.
        """
        raise NotImplementedError(
            "Subclasses of Question must implement get_type method."
        )

    def calculate_score(self, user_answer):
        """
        Calculate the score for the question based on user's answer.

        Args:
            user_answer (any): Answer provided by the user.

        Returns:
            float: The calculated score, a value between 0 and 1.
        """
        correct_answer = self.get_answer()

        if correct_answer is None:
            return 0.0

        return self._calculate_score(user_answer, correct_answer)

    def _calculate_score(self, user_answer, correct_answer):
        """
        Internal method to be implemented by subclasses to calculate score.
        """
        raise NotImplementedError(
            "Subclasses of Question must implement _calculate_score method."
        )


class SingleChoiceQuestion(Question):
    """
    Single choice question model.

    Attributes:
        choices (JSONField <{choice(str): is_correct(bool)}>): Choices of the question.
    """

    choices = models.JSONField(
        verbose_name=_("Choices"),
        default=dict,
        help_text=_(
            "Choices must be like this: {'choice 1': true, 'choice 2': false, ...} | true for the right choice, false for the wrong choices."
        ),
    )

    class Meta:
        """SingleChoiceQuestion Metadata."""

        verbose_name = _("Single choice question")
        verbose_name_plural = _("Single choice questions")

    def clean(self) -> None:
        """Clean method for SingleChoiceQuestion model."""
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

    def __str__(self) -> str:
        """Represent the SingleChoiceQuestion as string."""
        return "%s choices: %s" % (super().__str__(), self.choices)

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

    def get_choices(self):
        """Return choices for this question."""
        if self.choices:
            return self.choices
        else:
            return "{}"

    def get_type(self):
        return "single_choice"

    def get_question_form(self, data=None):
        """
        Get the form for the question.

        Args:
            data (dict): Form data.

        Returns:
            SingleChoiceQuestionForm: Form for the question.
        """
        from pod.quiz.forms import SingleChoiceQuestionForm

        return SingleChoiceQuestionForm(data, instance=self, prefix=f"question_{self.pk}")

    def _calculate_score(self, user_answer, correct_answer):
        """
        Calculate the score for single choice question.

        Args:
            user_answer (any): Answer provided by the user.
            correct_answer (any): Correct answer for the question.

        Returns:
            float: The calculated score, a value between 0 and 1.
        """
        return 1.0 if user_answer.lower() == correct_answer.lower() else 0.0


class MultipleChoiceQuestion(Question):
    """
    Multiple choice question model.

    Attributes:
        choices (JSONField <{question(str): is_correct(bool)}>): Choices of the question.
    """

    choices = models.JSONField(
        verbose_name=_("Choices"),
        default=dict,
        help_text=_(
            "Choices must be like this: {'choice 1': true, 'choice 2': true, 'choice 3': false, ...} | true for the right choice, false for the wrong choices."
        ),
    )

    class Meta:
        """MultipleChoiceQuestion Metadata."""

        verbose_name = _("Multiple choice question")
        verbose_name_plural = _("Multiple choice questions")

    def clean(self) -> None:
        """Clean method for MultipleChoiceQuestion model."""
        super().clean()

        if isinstance(self.choices, str):
            try:
                choices = loads(self.choices)
            except JSONDecodeError:
                return

        # Check if there are at least 2 choices
        if len(choices) < 2:
            raise ValidationError(_("There must be at least 2 choices."))

        # Check if there is at least one correct answer
        if not any(choices.values()):
            raise ValidationError(_("There must be at least one correct answer."))

    def __str__(self) -> str:
        """Represent the MultipleChoiceQuestion as string."""
        return "%s choices: %s" % (super().__str__(), self.choices)

    def get_type(self):
        return "multiple_choice"

    def get_answer(self):
        if isinstance(self.choices, str):
            try:
                self.choices = loads(self.choices)
            except JSONDecodeError:
                raise ValidationError(_("Invalid JSON format for choices."))
        correct_answer = [
            choice for choice, is_correct in self.choices.items() if is_correct
        ]
        return correct_answer

    def get_choices(self):
        """Return choices for this question."""
        if self.choices:
            return self.choices
        else:
            return "{}"

    def get_question_form(self, data=None):
        """
        Get the form for the question.

        Args:
            data (dict): Form data.

        Returns:
            MultipleChoiceQuestionForm: Form for the question.
        """
        from pod.quiz.forms import (
            MultipleChoiceQuestionForm,
        )

        return MultipleChoiceQuestionForm(
            data, instance=self, prefix=f"question_{self.pk}"
        )

    def _calculate_score(self, user_answer, correct_answer):
        """
        Calculate the score for multiple choice question.

        Args:
            user_answer (list): Answers provided by the user.
            correct_answer (list): Correct answers for the question.

        Returns:
            float: The calculated score, a value between 0 and 1.
        """
        user_answer_set = set(user_answer) if user_answer else set()
        correct_answer_set = set(correct_answer)
        intersection = user_answer_set & correct_answer_set
        score = len(intersection) / len(correct_answer_set)

        len_incorrect = len(user_answer_set - correct_answer_set)
        penalty = len_incorrect / len(correct_answer_set)
        score = max(0, score - penalty)
        return score


class TrueFalseQuestion(Question):  # TODO
    """
    True/false question model.

    Attributes:
        is_true (BooleanField): Is true.
    """

    is_true = models.BooleanField(
        verbose_name="Is true",
        default=True,
        help_text=_("Please choose if the answer is true or false."),
    )

    class Meta:
        verbose_name = _("True/false question")
        verbose_name_plural = _("True/false questions")

    def __str__(self) -> str:
        """Represent the TrueFalseQuestion as string."""
        return super().__str__()

    def get_type(self):
        return "true_false"


class ShortAnswerQuestion(Question):
    """
    Short answer question model.

    Attributes:
        answer (CharField): Answer of the question.
    """

    answer = models.CharField(
        verbose_name=_("Answer"),
        max_length=250,
        default="",
        help_text=_("Please choose an answer between 1 and 250 characters."),
    )

    class Meta:
        verbose_name = _("Short answer question")
        verbose_name_plural = _("Short answer questions")

    def __str__(self) -> str:
        """Represent the ShortAnswerQuestion as string."""
        return super().__str__()

    def get_answer(self) -> str:
        return self.answer

    def get_type(self):
        return "short_answer"

    def get_question_form(self, data=None):
        """
        Get the form for the question.

        Args:
            data (dict): Form data.
        Returns:
            ShortAnswerQuestionForm: Form for the question.
        """
        from pod.quiz.forms import (
            ShortAnswerQuestionForm,
        )

        return ShortAnswerQuestionForm(data, instance=self, prefix=f"question_{self.pk}")

    def _calculate_score(self, user_answer, correct_answer):
        """
        Calculate the score for short answer question.

        Args:
            user_answer (str): Answer provided by the user.
            correct_answer (str): Correct answer for the question.

        Returns:
            float: The calculated score, a value between 0 and 1.
        """
        if (
            user_answer is not None
            and user_answer.strip() != ""
            and correct_answer is not None
        ):
            return 1.0 if user_answer.lower() == correct_answer.lower() else 0.0
        return 0.0
