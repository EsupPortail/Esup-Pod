"""Unit tests for Esup-Pod quiz models."""

from unittest.mock import patch
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _
from django.test import TestCase
from pod.quiz.models import MultipleChoiceQuestion, Quiz, SingleChoiceQuestion

from pod.video.models import Type, Video


class QuizModelTests(TestCase):
    """TestCase for quiz model."""

    fixtures = ["initial_data.json"]

    def setUp(self):
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

    def test_get_questions(self):
        """Test if test_get_questions works correctly."""
        question1 = SingleChoiceQuestion.objects.create(quiz=self.quiz, title="UCQ1")
        question2 = MultipleChoiceQuestion.objects.create(quiz=self.quiz, title="MCQ1")

        with patch.object(Quiz, 'get_questions') as mock_get_questions:
            mock_get_questions.return_value = [question1, question2]

            questions = self.quiz.get_questions()
            self.assertEqual(len(questions), 2)
            self.assertIn(question1, questions)
            self.assertIn(question2, questions)
        print(" --->  test_get_questions ok")

    def test_quiz_string_representation(self):
        """Test if test_quiz_string_representation works correctly."""
        expected_string = _("Quiz of video") + f" {self.video}"
        quiz_string = str(self.quiz)
        self.assertEqual(quiz_string, expected_string)
        print(" --->  test_get_questions ok")
