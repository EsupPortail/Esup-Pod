"""Unit tests for Esup-Pod quiz views.

test with `python manage.py test pod.quiz.tests.test_views`
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib.messages import get_messages
from django.utils.translation import gettext_lazy as _

from pod.main.models import Configuration
from pod.quiz.forms import QuizDeleteForm, QuizForm
from pod.quiz.models import (
    MultipleChoiceQuestion,
    Quiz,
    ShortAnswerQuestion,
    SingleChoiceQuestion,
)
from pod.video.models import Type, Video

# ggignore-start
# gitguardian:ignore
PWD = "azerty1234"  # nosec
# ggignore-end


class QuizCreateViewsTest(TestCase):
    """TestCase for Esup-Pod quiz creation views."""

    fixtures = ["initial_data.json"]

    def setUp(self) -> None:
        """Set up QuizCreateViewsTest."""
        self.user = User.objects.create(username="test", password=PWD, is_staff=True)
        self.user2 = User.objects.create(username="test2", password=PWD)
        self.video = Video.objects.create(
            title="videotest",
            owner=self.user,
            video="test.mp4",
            duration=20,
            type=Type.objects.get(id=1),
        )
        self.add_quiz_url = reverse(
            "quiz:add_quiz", kwargs={"video_slug": self.video.slug}
        )
        self.edit_quiz_url = reverse(
            "quiz:edit_quiz", kwargs={"video_slug": self.video.slug}
        )

    def test_maintenance(self) -> None:
        """Test Pod maintenance mode in QuizCreateViewsTest."""
        self.client.force_login(self.user)
        response = self.client.get(self.add_quiz_url)
        self.assertEqual(response.status_code, 200)

        conf = Configuration.objects.get(key="maintenance_mode")
        conf.value = "1"
        conf.save()

        response = self.client.get(self.add_quiz_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/maintenance/")

        print(" --->  test_maintenance ok")

    def test_quiz_already_exists(self) -> None:
        """Test quiz_already_exists."""
        self.client.force_login(self.user)
        response = self.client.get(self.add_quiz_url)
        self.assertEqual(response.status_code, 200)
        quiz = Quiz.objects.create(video=self.video)
        ShortAnswerQuestion.objects.create(quiz=quiz, title="SAQ1", answer="answer")
        response = self.client.get(self.add_quiz_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.edit_quiz_url)

        print(" ---> test_quiz_already_exists ok")

    def test_quiz_create_view_permission_denied(self) -> None:
        """Test quiz_create_view_permission_denied."""
        self.client.force_login(self.user2)
        response = self.client.get(self.add_quiz_url)
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn(_("You cannot create a quiz for this video."), messages)
        self.assertRaises(PermissionError)

        print(" ---> test_quiz_create_view_permission_denied ok")

    def test_get_request_for_create_quiz_view(self) -> None:
        """Test get_request_for_create_quiz_view."""
        self.client.force_login(self.user)
        response = self.client.get(self.add_quiz_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "quiz/create_edit_quiz.html")

        self.assertIn("quiz_form", response.context)
        self.assertIsInstance(response.context["quiz_form"], QuizForm)
        self.assertIn("question_formset", response.context)
        self.assertEqual(response.context["question_formset"].extra, 1)
        self.assertEqual(response.context["question_formset"].prefix, "questions")

        print(" ---> test_get_request_for_create_quiz_view ok")


class VideoQuizViewsTest(TestCase):
    """TestCase for Esup-Pod video quiz views."""

    fixtures = ["initial_data.json"]

    def setUp(self) -> None:
        """Set up VideoQuizViewsTest."""
        self.user = User.objects.create(username="test", password="azerty")
        self.user2 = User.objects.create(username="test2", password="azerty")
        self.video = Video.objects.create(
            title="videotest",
            owner=self.user,
            video="test.mp4",
            duration=20,
            type=Type.objects.get(id=1),
        )
        self.video_quiz_url = reverse(
            "quiz:video_quiz", kwargs={"video_slug": self.video.slug}
        )

        self.connected_only_quiz = Quiz.objects.create(
            video=self.video, connected_user_only=True
        )
        self.MCQ1 = MultipleChoiceQuestion.objects.create(
            quiz=self.connected_only_quiz,
            title="MCQ1",
            choices='{"choice 1": true, "choice 2": false, "choice 3": true}',
        )
        self.SCQ1 = SingleChoiceQuestion.objects.create(
            quiz=self.connected_only_quiz,
            title="SCQ1",
            choices='{"choice 1": true, "choice 2": false, "choice 3": false}',
        )
        self.SAQ1 = ShortAnswerQuestion.objects.create(
            quiz=self.connected_only_quiz, title="SAQ1", answer="answer"
        )

    def test_maintenance(self) -> None:
        """Test Pod maintenance mode in VideoQuizViewsTest."""
        self.client.force_login(self.user)
        response = self.client.get(self.video_quiz_url)
        self.assertEqual(response.status_code, 200)

        conf = Configuration.objects.get(key="maintenance_mode")
        conf.value = "1"
        conf.save()

        response = self.client.get(self.video_quiz_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/maintenance/")

        print(" ---> test_maintenance ok")

    def test_wrong_video_slug(self) -> None:
        """Test wrong_video_slug."""
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("quiz:video_quiz", kwargs={"video_slug": "wrong_slug"})
        )
        self.assertEqual(response.status_code, 404)

        print(" ---> test_wrong_video_slug ok")

    def test_disconnected_user_for_connected_only_quiz(self) -> None:
        """Test disconnected_user_for_connected_only_quiz."""
        response = self.client.get(self.video_quiz_url)
        self.assertEqual(response.status_code, 302)
        redirect_url = f"{reverse('authentication:authentication_login')}?referrer={self.video_quiz_url}"
        self.assertRedirects(
            response, redirect_url, status_code=302, target_status_code=302
        )

        print(" ---> test_disconnected_user_for_connected_only_quiz ok")

    def test_get_request_for_video_quiz_view(self) -> None:
        """Test get_request_for_video_quiz_view."""
        self.client.force_login(self.user)
        response = self.client.get(self.video_quiz_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "quiz/video_quiz.html")

        self.assertIn("quiz", response.context)
        self.assertIsInstance(response.context["quiz"], Quiz)
        self.assertIn("form_submitted", response.context)
        self.assertIsInstance(response.context["form_submitted"], bool)
        self.assertFalse(response.context["form_submitted"])

        print(" ---> test_get_request_for_video_quiz_view ok")


class DeleteQuizViewsTest(TestCase):
    """TestCase for Esup-Pod quiz deletion views."""

    fixtures = ["initial_data.json"]

    def setUp(self) -> None:
        """Set up DeleteQuizViewsTest."""
        self.user = User.objects.create(username="test", password="azerty")
        self.user2 = User.objects.create(username="test2", password="azerty")
        self.video = Video.objects.create(
            title="videotest",
            owner=self.user,
            video="test.mp4",
            duration=20,
            type=Type.objects.get(id=1),
        )
        self.delete_quiz_url = reverse(
            "quiz:remove_quiz", kwargs={"video_slug": self.video.slug}
        )

        self.quiz = Quiz.objects.create(video=self.video)
        self.MCQ1 = MultipleChoiceQuestion.objects.create(
            quiz=self.quiz,
            title="MCQ1",
            choices='{"choice 1": true, "choice 2": false, "choice 3": true}',
        )
        self.SCQ1 = SingleChoiceQuestion.objects.create(
            quiz=self.quiz,
            title="SCQ1",
            choices='{"choice 1": true, "choice 2": false, "choice 3": false}',
        )

    def test_maintenance(self) -> None:
        """Test Pod maintenance mode in DeleteQuizViewsTest."""
        self.client.force_login(self.user)
        response = self.client.get(self.delete_quiz_url)
        self.assertEqual(response.status_code, 200)

        conf = Configuration.objects.get(key="maintenance_mode")
        conf.value = "1"
        conf.save()

        response = self.client.get(self.delete_quiz_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, "/maintenance/")

        print(" ---> test_maintenance ok")

    def test_wrong_video_slug(self) -> None:
        """Test wrong_video_slug."""
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("quiz:remove_quiz", kwargs={"video_slug": "wrong_slug"})
        )
        self.assertEqual(response.status_code, 404)

        print(" ---> test_wrong_video_slug ok")

    def test_quiz_does_not_exist(self) -> None:
        """Test quiz_does_not_exist."""
        self.client.force_login(self.user)
        video_without_quiz = Video.objects.create(
            title="videotest2",
            owner=self.user,
            video="test.mp4",
            duration=20,
            type=Type.objects.get(id=1),
        )
        response = self.client.get(
            reverse("quiz:remove_quiz", kwargs={"video_slug": video_without_quiz.slug})
        )
        self.assertEqual(response.status_code, 404)

        print(" ---> test_quiz_does_not_exist ok")

    def test_quiz_delete_view_permission_denied(self) -> None:
        """Test quiz_delete_view_permission_denied."""
        self.client.force_login(self.user2)
        response = self.client.get(self.delete_quiz_url)
        messages = [m.message for m in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 403)
        self.assertIn(_("You cannot delete the quiz for this video."), messages)
        self.assertRaises(PermissionError)

        print(" ---> test_quiz_delete_view_permission_denied ok")

    def test_get_request_for_delete_quiz_view(self) -> None:
        """Test get_request_for_delete_quiz_view."""
        self.client.force_login(self.user)
        response = self.client.get(self.delete_quiz_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "quiz/delete_quiz.html")
        self.assertIn("quiz", response.context)
        self.assertIsInstance(response.context["quiz"], Quiz)
        self.assertIn("form", response.context)
        self.assertIsInstance(response.context["form"], QuizDeleteForm)

        print(" ---> test_get_request_for_delete_quiz_view ok")

    def test_post_request_for_delete_quiz_view_valid_form(self) -> None:
        """Test post_request_for_delete_quiz_view_valid_form."""
        self.client.force_login(self.user)
        form_data = {"agree": True}
        response = self.client.post(self.delete_quiz_url, data=form_data)
        messages = [m.message for m in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            reverse(
                "video:completion:video_completion", kwargs={"slug": self.video.slug}
            ),
        )
        self.assertIn(_("The quiz has been deleted."), messages)
        self.assertFalse(Quiz.objects.filter(video=self.video).exists())

        print(" ---> test_post_request_for_delete_quiz_view_valid_form ok")

    def test_post_request_for_delete_quiz_view_invalid_form(self) -> None:
        """Test post_request_for_delete_quiz_view_invalid_form."""
        self.client.force_login(self.user)
        form_data = {"agree": False}
        response = self.client.post(self.delete_quiz_url, data=form_data)
        messages = [m.message for m in get_messages(response.wsgi_request)]

        self.assertEqual(response.status_code, 200)
        self.assertIn(_("One or more errors have been found in the form."), messages)

        print(" ---> test_post_request_for_delete_quiz_view_invalid_form ok")
