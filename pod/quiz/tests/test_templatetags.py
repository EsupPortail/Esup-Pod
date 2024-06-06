"""Unit tests for Esup-Pod quiz templatetags."""

from django.test import RequestFactory, TestCase
from django.contrib.auth.models import User
from pod.quiz.models import MultipleChoiceQuestion, Quiz, SingleChoiceQuestion
from pod.quiz.templatetags.video_quiz import is_quiz_accessible, is_quiz_exists

from pod.video.models import Type, Video

# ggignore-start
# gitguardian:ignore
PWD = "azerty1234"  # nosec
# ggignore-end


class VideoQuizTemplateTagsTestCase(TestCase):
    """TestCase for video_quiz template tags."""

    fixtures = ["initial_data.json"]

    def setUp(self) -> None:
        self.user = User.objects.create(username="pod", password=PWD)
        self.video_with_quiz = Video.objects.create(
            title="Video1",
            owner=self.user,
            video="test.mp4",
            is_draft=False,
            type=Type.objects.get(id=1),
        )
        self.quiz = Quiz.objects.create(video=self.video_with_quiz)
        SingleChoiceQuestion.objects.create(quiz=self.quiz, title="UCQ1")
        MultipleChoiceQuestion.objects.create(quiz=self.quiz, title="MCQ1")

        self.video_without_quiz = Video.objects.create(
            title="Video without quiz",
            owner=self.user,
            video="test.mp4",
            is_draft=False,
            type=Type.objects.get(id=1),
        )

    def test_is_quiz_accessible(self):
        """Test if test_is_quiz_accessible works correctly."""
        # Test when there is a quiz associated with the video
        request = RequestFactory().get("/")
        request.user = self.user
        context = {"request": request}

        result = is_quiz_accessible(context, self.video_with_quiz)
        self.assertTrue(result)

        # Test when there is no quiz associated with the video
        request = RequestFactory().get("/")
        request.user = self.user
        context = {"request": request}

        result = is_quiz_accessible(context, self.video_without_quiz)
        self.assertFalse(result)

        print(" --->  test_is_quiz_accessible ok")

    def test_is_quiz_exists(self):
        """Test if test_is_quiz_exists works correctly."""
        # Test when there is a quiz associated with the video
        result = is_quiz_exists(self.video_with_quiz)
        self.assertTrue(result)

        # Test when there is no quiz associated with the video
        result = is_quiz_exists(self.video_without_quiz)
        self.assertFalse(result)

        print(" --->  test_is_quiz_exists ok")
