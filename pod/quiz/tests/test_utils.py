"""Unit tests for Esup-Pod quiz utilities."""

from django.test import TestCase
from django.contrib.auth.models import User
from pod.quiz.models import LongAnswerQuestion, MultipleChoiceQuestion, Quiz, ShortAnswerQuestion, UniqueChoiceQuestion
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

    def test_get_quiz_questions(self):
        quiz = Quiz.objects.create(video=self.video)
        UniqueChoiceQuestion.objects.create(quiz=quiz, title="UCQ1")
        MultipleChoiceQuestion.objects.create(quiz=quiz, title="MCQ1")
        ShortAnswerQuestion.objects.create(quiz=quiz, title="SAQ1")
        LongAnswerQuestion.objects.create(quiz=quiz, title="LAQ1")

        questions = get_quiz_questions(quiz)
        self.assertEqual(len(questions), 4)

    def test_get_video_quiz(self):
        video_without_quiz = Video.objects.create(
            title="Video2",
            owner=self.user,
            video="test2.mp4",
            is_draft=False,
            type=Type.objects.get(id=1),
        )

        video_with_quiz = Video.objects.create(
            title="Video3",
            owner=self.user,
            video="test3.mp4",
            is_draft=False,
            type=Type.objects.get(id=1),
        )
        Quiz.objects.create(video=video_with_quiz)

        self.assertIsNone(get_video_quiz(video_without_quiz))
        self.assertIsNotNone(get_video_quiz(video_with_quiz))
