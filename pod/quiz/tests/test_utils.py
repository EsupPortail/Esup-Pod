"""Unit tests for Esup-Pod quiz utilities."""

from django.test import TestCase
from django.contrib.auth.models import User
from pod.quiz.models import (
    MultipleChoiceQuestion,
    Quiz,
    ShortAnswerQuestion,
    SingleChoiceQuestion,
)
from pod.quiz.utils import get_quiz_questions, get_video_quiz

from pod.video.models import Type, Video


class QuizTestUtils(TestCase):
    """TestCase for Esup-Pod quiz utilities."""

    fixtures = ["initial_data.json"]

    def setUp(self) -> None:
        self.user = User.objects.create(username="pod", password="pod1234pod")
        self.video = Video.objects.create(
            title="Video1",
            owner=self.user,
            video="test.mp4",
            is_draft=False,
            type=Type.objects.get(id=1),
        )
        self.video2 = Video.objects.create(
            title="Video2",
            owner=self.user,
            video="test.mp4",
            is_draft=False,
            type=Type.objects.get(id=1),
        )
        self.video3 = Video.objects.create(
            title="Video3",
            owner=self.user,
            video="test.mp4",
            is_draft=False,
            type=Type.objects.get(id=1),
        )

    def test_get_quiz_questions(self):
        """Test if test_get_quiz_questions works correctly."""
        quiz = Quiz.objects.create(video=self.video)
        SingleChoiceQuestion.objects.create(quiz=quiz, title="UCQ1")
        MultipleChoiceQuestion.objects.create(quiz=quiz, title="MCQ1")
        ShortAnswerQuestion.objects.create(quiz=quiz, title="SAQ1")

        questions = get_quiz_questions(quiz)
        self.assertEqual(len(questions), 3)

        quiz_with_single_choice = Quiz.objects.create(video=self.video2)
        SingleChoiceQuestion.objects.create(quiz=quiz_with_single_choice, title="UCQ2")
        questions_with_single_choice = get_quiz_questions(quiz_with_single_choice)
        self.assertEqual(len(questions_with_single_choice), 1)

        quiz_with_all_question_types = Quiz.objects.create(video=self.video3)
        UCQ3 = SingleChoiceQuestion.objects.create(
            quiz=quiz_with_all_question_types, title="UCQ3"
        )
        MCQ2 = MultipleChoiceQuestion.objects.create(
            quiz=quiz_with_all_question_types, title="MCQ2"
        )
        SAQ2 = ShortAnswerQuestion.objects.create(
            quiz=quiz_with_all_question_types, title="SAQ2"
        )
        questions_with_all_types = get_quiz_questions(quiz_with_all_question_types)

        self.assertIsInstance(questions_with_all_types, list)
        self.assertEqual(len(questions_with_all_types), 3)
        self.assertListEqual(
            questions_with_all_types,
            [UCQ3, MCQ2, SAQ2],
        )
        print(" --->  test_get_quiz_questions ok")

    def test_get_video_quiz(self):
        """Test if test_get_video_quiz works correctly."""
        Quiz.objects.create(video=self.video2)
        self.assertIsNone(get_video_quiz(self.video))
        self.assertIsNotNone(get_video_quiz(self.video2))
        print(" --->  test_get_video_quiz ok")
