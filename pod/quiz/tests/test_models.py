"""Unit tests for Esup-Pod quiz models.

test with `python manage.py test pod.quiz.tests.test_models`
"""

from unittest.mock import patch
from django.contrib.auth.models import User
from django.forms import ValidationError
from django.utils.translation import gettext as _
from django.test import TestCase
from pod.quiz.forms import (
    MultipleChoiceQuestionForm,
    ShortAnswerQuestionForm,
    SingleChoiceQuestionForm,
)
from pod.quiz.models import (
    MultipleChoiceQuestion,
    Quiz,
    ShortAnswerQuestion,
    SingleChoiceQuestion,
)

from pod.video.models import Type, Video


class QuizModelTests(TestCase):
    """TestCase for Quiz model."""

    fixtures = ["initial_data.json"]

    def setUp(self) -> None:
        """Set up the tests."""
        self.user = User.objects.create_user(username="testuser", password="testpassword")
        self.video = Video.objects.create(
            title="Video1",
            owner=self.user,
            video="test.mp4",
            is_draft=False,
            type=Type.objects.get(id=1),
        )
        self.quiz = Quiz.objects.create(video=self.video)

    def test_get_questions(self) -> None:
        """Test if test_get_questions works correctly."""
        question1 = SingleChoiceQuestion.objects.create(quiz=self.quiz, title="UCQ1")
        question2 = MultipleChoiceQuestion.objects.create(quiz=self.quiz, title="MCQ1")

        with patch.object(Quiz, "get_questions") as mock_get_questions:
            mock_get_questions.return_value = [question1, question2]

            questions = self.quiz.get_questions()
            self.assertEqual(len(questions), 2)
            self.assertIn(question1, questions)
            self.assertIn(question2, questions)
        print(" --->  test_get_questions ok")

    def test_string_representation(self) -> None:
        """Check Quiz string representation."""
        expected_string = f"{_('Quiz of video')} {self.video}"
        self.assertEqual(str(self.quiz), expected_string)
        print(" --->  test_get_questions ok")


class QuestionModelTests(TestCase):
    """TestCase for Question model."""

    fixtures = ["initial_data.json"]

    def setUp(self) -> None:
        """Set up the tests."""
        self.user = User.objects.create_user(username="testuser", password="testpassword")
        self.video = Video.objects.create(
            title="Video1",
            owner=self.user,
            video="test.mp4",
            is_draft=False,
            type=Type.objects.get(id=1),
        )
        self.quiz = Quiz.objects.create(video=self.video)
        self.UCQ1 = SingleChoiceQuestion.objects.create(quiz=self.quiz, title="UCQ1")

    def test_string_representation(self) -> None:
        """Test if test_string_representation works correctly."""
        expected_string = (
            f"{_('Question “%s”') % self.UCQ1.title} choices: {self.UCQ1.choices}"
        )
        self.assertEqual(str(self.UCQ1), expected_string)
        print(" --->  test_string_representation ok")

    def test_clean(self) -> None:
        """Test if test_clean works correctly."""
        question_start_timestamp_more_than_end_timestamp = SingleChoiceQuestion(
            quiz=self.quiz,
            title="question_start_timestamp_more_than_end_timestamp",
            start_timestamp=2,
            end_timestamp=1,
        )
        self.assertRaises(
            ValidationError, question_start_timestamp_more_than_end_timestamp.clean
        )

        question_end_timestamp_withou_start_timestamp = SingleChoiceQuestion(
            quiz=self.quiz,
            title="question_end_timestamp_withou_start_timestamp",
            end_timestamp=1,
        )
        self.assertRaises(
            ValidationError, question_end_timestamp_withou_start_timestamp.clean
        )
        print(" --->  test_clean ok")


class SingleChoiceQuestionModelTests(TestCase):
    """TestCase for SingleChoiceQuestion model."""

    fixtures = ["initial_data.json"]

    def setUp(self) -> None:
        """Set up the tests."""
        self.user = User.objects.create_user(username="testuser", password="testpassword")
        self.video = Video.objects.create(
            title="Video1",
            owner=self.user,
            video="test.mp4",
            is_draft=False,
            type=Type.objects.get(id=1),
        )
        self.quiz = Quiz.objects.create(video=self.video)

        self.normal_question = SingleChoiceQuestion(
            quiz=self.quiz, title="UCQ1", choices='{"choice 1": true, "choice 2": false}'
        )

    def test_clean(self) -> None:
        """Test if test_clean works correctly."""
        question_with_one_choice = SingleChoiceQuestion(
            quiz=self.quiz, title="question_with_one_choice", choices='{"choice 1": true}'
        )
        self.assertRaises(ValidationError, question_with_one_choice.clean)

        question_with_no_correct_choice = SingleChoiceQuestion(
            quiz=self.quiz,
            title="question_with_no_choice",
            choices='{"choice 1": false, "choice 2": false}',
        )
        self.assertRaises(ValidationError, question_with_no_correct_choice.clean)

        question_with_more_than_one_correct_choice = SingleChoiceQuestion(
            quiz=self.quiz,
            title="question_with_more_than_one_correct_choice",
            choices='{"choice 1": true, "choice 2": true}',
        )
        self.assertRaises(
            ValidationError, question_with_more_than_one_correct_choice.clean
        )

        print(" --->  test_clean ok")

    def test_scq_str_representation(self) -> None:
        """Check single choice question string representation."""
        expected_string = f"{_('Question “%s”') % self.normal_question.title} choices: {self.normal_question.choices}"
        self.assertEqual(str(self.normal_question), expected_string)
        print(" --->  test_string_representation ok")

    def test_get_answer(self) -> None:
        """Test if test_get_answer works correctly."""
        self.assertEqual(self.normal_question.get_answer(), "choice 1")
        print(" --->  test_get_answer ok")

    def test_get_type(self) -> None:
        """Test if test_get_type works correctly."""
        self.assertEqual(self.normal_question.get_type(), "single_choice")
        print(" --->  test_get_type ok")

    def test_get_question_form(self) -> None:
        """Test if test_get_question_form works correctly."""
        expected_form = SingleChoiceQuestionForm(
            instance=self.normal_question, prefix=f"question_{self.normal_question.pk}"
        )
        actual_form = self.normal_question.get_question_form()

        self.assertEqual(
            expected_form.fields["selected_choice"].widget.choices,
            actual_form.fields["selected_choice"].widget.choices,
        )
        self.assertEqual(expected_form.prefix, actual_form.prefix)

        print(" --->  test_get_question_form ok")


class MultipleChoiceQuestionModelTests(TestCase):
    """TestCase for MultipleChoiceQuestion model."""

    fixtures = ["initial_data.json"]

    def setUp(self) -> None:
        """Set up the tests."""
        self.user = User.objects.create_user(username="testuser", password="testpassword")
        self.video = Video.objects.create(
            title="Video1",
            owner=self.user,
            video="test.mp4",
            is_draft=False,
            type=Type.objects.get(id=1),
        )
        self.quiz = Quiz.objects.create(video=self.video)

        self.normal_question = MultipleChoiceQuestion(
            quiz=self.quiz,
            title="MCQ1",
            choices='{"choice 1": true, "choice 2": false, "choice 3": true}',
        )

    def test_clean(self) -> None:
        """Test if test_clean works correctly."""
        question_with_one_choice = MultipleChoiceQuestion(
            quiz=self.quiz, title="question_with_one_choice", choices='{"choice 1": true}'
        )
        self.assertRaises(ValidationError, question_with_one_choice.clean)

        question_with_no_correct_choice = MultipleChoiceQuestion(
            quiz=self.quiz,
            title="question_with_no_choice",
            choices='{"choice 1": false, "choice 2": false}',
        )
        self.assertRaises(ValidationError, question_with_no_correct_choice.clean)

        print(" --->  test_clean ok")

    def test_mcq_str_representation(self) -> None:
        """Check Multiple choice question string representation."""
        expected_string = f"{_('Question “%s”') % self.normal_question.title} choices: {self.normal_question.choices}"
        self.assertEqual(str(self.normal_question), expected_string)
        print(" --->  test_string_representation ok")

    def test_get_type(self) -> None:
        """Test if test_get_type works correctly."""
        self.assertEqual(self.normal_question.get_type(), "multiple_choice")
        print(" --->  test_get_type ok")

    def test_get_answer(self) -> None:
        """Test if test_get_answer works correctly."""
        self.assertEqual(self.normal_question.get_answer(), ["choice 1", "choice 3"])
        print(" --->  test_get_answer ok")

    def test_get_question_form(self) -> None:
        """Test if test_get_question_form works correctly."""
        expected_form = MultipleChoiceQuestionForm(
            instance=self.normal_question, prefix=f"question_{self.normal_question.pk}"
        )

        actual_form = self.normal_question.get_question_form()

        self.assertEqual(
            expected_form.fields["selected_choice"].widget.choices,
            actual_form.fields["selected_choice"].widget.choices,
        )
        self.assertEqual(expected_form.prefix, actual_form.prefix)

        print(" --->  test_get_question_form ok")


class ShortAnwerQuestionTest(TestCase):
    """TestCase for ShortAnswerQuestion model."""

    fixtures = ["initial_data.json"]

    def setUp(self) -> None:
        """Set up the tests."""
        self.user = User.objects.create_user(username="testuser", password="testpassword")
        self.video = Video.objects.create(
            title="Video1",
            owner=self.user,
            video="test.mp4",
            is_draft=False,
            type=Type.objects.get(id=1),
        )
        self.quiz = Quiz.objects.create(video=self.video)

        self.normal_question = ShortAnswerQuestion(
            quiz=self.quiz, title="SAQ1", answer="answer"
        )

    def test_string_representation(self) -> None:
        """Check short answer question string representation."""
        expected_string = _("Question “%s”") % self.normal_question.title
        self.assertEqual(str(self.normal_question), expected_string)
        print(" --->  test_string_representation ok")

    def test_get_type(self) -> None:
        """Test if test_get_type works correctly."""
        self.assertEqual(self.normal_question.get_type(), "short_answer")
        print(" --->  test_get_type ok")

    def test_get_answer(self) -> None:
        """Test if test_get_answer works correctly."""
        self.assertEqual(self.normal_question.get_answer(), "answer")
        print(" --->  test_get_answer ok")

    def test_get_question_form(self) -> None:
        """Test if test_get_question_form works correctly."""
        expected_form = ShortAnswerQuestionForm(
            instance=self.normal_question, prefix=f"question_{self.normal_question.pk}"
        )

        actual_form = self.normal_question.get_question_form()

        self.assertEqual(
            expected_form.fields["user_answer"].widget.attrs,
            actual_form.fields["user_answer"].widget.attrs,
        )
        self.assertEqual(expected_form.prefix, actual_form.prefix)

        print(" --->  test_get_question_form ok")
