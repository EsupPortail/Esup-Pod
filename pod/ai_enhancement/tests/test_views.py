"""Tests the views for ai_enhancement module."""

import json
from unittest.mock import patch

from django.contrib.auth.models import User
from django.http import JsonResponse
from django.test import RequestFactory, TestCase
from django.urls import reverse

from pod.ai_enhancement.models import AIEnhancement
from pod.ai_enhancement.views import toggle_webhook
from pod.main.models import Configuration
from pod.video.models import Video, Type


class EnrichVideoJsonViewTest(TestCase):
    """Test the enhance_video_json view."""

    fixtures = ["initial_data.json"]

    def setUp(self):
        """Set up the test."""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username="testuser")
        self.user.is_staff = True
        self.user.save()
        self.video = Video.objects.create(
            slug="test-video",
            owner=self.user,
            video="test_video.mp4",
            title="Test video",
            description="This is a test video.",
            type=Type.objects.get(id=1),
        )
        self.enhancement = AIEnhancement.objects.create(
            video=self.video, ai_enhancement_id_in_aristote="123"
        )
        self.client.force_login(self.user)

    @patch("pod.ai_enhancement.views.AristoteAI")
    def test_enhance_video_json__success(self, mock_aristote_ai):
        """Test the enhance_video_json view when successful."""
        json_data = {
            "createdAt": "2024-01-26T14:40:05+01:00",
            "updatedAt": "2024-01-26T14:40:05+01:00",
            "id": "018d45ff-bfe7-772f-b671-723ac7de674e",
            "enhancementVersionMetadata": {
                "title": "Random title",
                "description": "This is an example of an enhancement version",
                "topics": [
                    "Random topic 1",
                    "Random topic 2",
                ],
                "discipline": "mocked_discipline",
                "mediaType": "mocked_mediaType",
            },
            "transcript": {
                "originalFilename": "transcript.json",
                "language": "fr",
                "text": "mocked_text",
                "sentences": [],
            },
            "multipleChoiceQuestions": [],
            "initialVersion": True,
        }
        mock_aristote_instance = mock_aristote_ai.return_value
        mock_aristote_instance.get_latest_enhancement_version.return_value = json_data
        url = reverse("ai_enhancement:enhance_video_json", args=[self.video.slug])
        # request = self.factory.get(url)
        response = self.client.get(url)
        # response = enhance_video_json(request, self.video.slug)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response, JsonResponse)
        mock_aristote_instance.get_latest_enhancement_version.assert_called_once_with(
            self.enhancement.ai_enhancement_id_in_aristote,
        )
        expected_json = json_data
        self.assertJSONEqual(str(response.content, encoding="utf-8"), expected_json)
        print(" --->  test_enhance_video_json__success ok")


class ReceiveWebhookViewTest(TestCase):
    """Test the receive_webhook view."""

    fixtures = ["initial_data.json"]

    def setUp(self):
        """Set up the test."""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username="test_user")
        self.user.is_staff = True
        self.user.save()
        self.video = Video.objects.create(
            slug="test-video",
            owner=self.user,
            video="test_video.mp4",
            title="Test video",
            description="This is a test video.",
            type=Type.objects.get(id=1),
        )
        self.enhancement = AIEnhancement.objects.create(
            video=self.video, ai_enhancement_id_in_aristote="123"
        )
        self.client.force_login(self.user)

    def test_toggle_webhook__success(self):
        """Test the receive_webhook view when successful."""
        url = reverse("ai_enhancement:webhook")
        request_data = {
            "id": "123",
            "status": "SUCCESS",
            "initialVersionId": "018e08b5-9ea0-73a7-bcd7-34764e3b0775",
            "failureCause": None,
        }
        request = self.factory.post(
            url, data=request_data, content_type="application/json"
        )
        response = toggle_webhook(request)
        self.enhancement.refresh_from_db()
        self.assertTrue(self.enhancement.is_ready)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response, JsonResponse)
        self.assertEqual(json.loads(response.content.decode()), {"status": "OK"})
        print(" --->  test_toggle_webhook__success ok")

    def test_toggle_webhook__bad_method(self):
        """Test the receive_webhook view when using a bad method."""
        url = reverse("ai_enhancement:webhook")
        request = self.factory.get(url)
        response = toggle_webhook(request)
        self.enhancement.refresh_from_db()
        self.assertFalse(self.enhancement.is_ready)
        self.assertEqual(response.status_code, 405)
        self.assertIsInstance(response, JsonResponse)
        self.assertEqual(
            json.loads(response.content.decode()),
            {"error": "Only POST requests are allowed."},
        )
        print(" --->  test_toggle_webhook__bad_method ok")

    def test_toggle_webhook__enhancement_not_found(self):
        """Test the receive_webhook view when the enhancement is not found."""
        url = reverse("ai_enhancement:webhook")
        request_data = {
            "id": "456",
            "status": "SUCCESS",
            "initialVersionId": "018e08b5-9ea0-73a7-bcd7-34764e3b0775",
            "failureCause": None,
        }
        request = self.factory.post(
            url, data=request_data, content_type="application/json"
        )
        response = toggle_webhook(request)
        self.enhancement.refresh_from_db()
        self.assertFalse(self.enhancement.is_ready)
        self.assertEqual(response.status_code, 404)
        self.assertIsInstance(response, JsonResponse)
        self.assertEqual(
            json.loads(response.content.decode()), {"error": "Enhancement not found."}
        )
        print(" --->  test_toggle_webhook__enhancement_not_found ok")

    def test_toggle_webhook__no_id_in_request(self):
        """Test the receive_webhook view when there is no id in the request."""
        url = reverse("ai_enhancement:webhook")
        request_data = {
            "status": "SUCCESS",
            "initialVersionId": "018e08b5-9ea0-73a7-bcd7-34764e3b0775",
            "failureCause": None,
        }
        request = self.factory.post(
            url, data=request_data, content_type="application/json"
        )
        response = toggle_webhook(request)
        self.enhancement.refresh_from_db()
        self.assertFalse(self.enhancement.is_ready)
        self.assertEqual(response.status_code, 400)
        self.assertIsInstance(response, JsonResponse)
        self.assertEqual(
            json.loads(response.content.decode()), {"error": "No id in the request."}
        )
        print(" --->  test_toggle_webhook__no_id_in_request ok")

    def test_toggle_webhook__bad_content_type(self):
        """Test the receive_webhook view when using a bad content type."""
        url = reverse("ai_enhancement:webhook")
        request_data = {
            "status": "SUCCESS",
            "initialVersionId": "018e08b5-9ea0-73a7-bcd7-34764e3b0775",
            "failureCause": None,
        }
        request = self.factory.post(url, data=request_data, content_type="image/png")
        response = toggle_webhook(request)
        self.enhancement.refresh_from_db()
        self.assertFalse(self.enhancement.is_ready)
        self.assertEqual(response.status_code, 415)
        self.assertIsInstance(response, JsonResponse)
        self.assertEqual(
            json.loads(response.content.decode()),
            {"error": "Only application/json content type is allowed."},
        )
        print(" --->  test_toggle_webhook__bad_content_type ok")

    def test_toggle_webhook__enrichment_not_achieved(self):
        """Test the receive_webhook view when the enrichment has not been achieved."""
        url = reverse("ai_enhancement:webhook")
        request_data = {
            "id": "123",
            "status": "FAILURE",
            "initialVersionId": "018e08b5-9ea0-73a7-bcd7-34764e3b0775",
            "failureCause": "mocked_failure_cause",
        }
        request = self.factory.post(
            url, data=request_data, content_type="application/json"
        )
        response = toggle_webhook(request)
        self.enhancement.refresh_from_db()
        self.assertFalse(self.enhancement.is_ready)
        self.assertEqual(response.status_code, 500)
        self.assertIsInstance(response, JsonResponse)
        self.assertEqual(
            json.loads(response.content.decode()),
            {"status": "Enhancement has not yet been successfully achieved."},
        )
        print(" --->  test_toggle_webhook__enrichment_not_achieved ok")


class EnhanceVideoViewTest(TestCase):
    """Test the enhance_video view."""

    fixtures = ["initial_data.json"]

    def setUp(self):
        """Set up the test."""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username="test_user")
        self.user.is_staff = True
        self.user.save()
        self.video = Video.objects.create(
            slug="test-video",
            owner=self.user,
            video="test_video.mp4",
            title="Test video",
            description="This is a test video.",
            type=Type.objects.get(id=1),
        )
        self.client.force_login(self.user)

    def test_enhance_video__success(self):
        """Test the enhance_video view when success."""
        url = reverse("ai_enhancement:enhance_video", args=[self.video.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "base.html")
        self.assertTemplateUsed(response, "navbar.html")
        self.assertTemplateUsed(response, "navbar_collapse.html")
        self.assertTemplateUsed(response, "footer.html")
        self.assertTemplateUsed(response, "create_enhancement.html")
        print(" --->  test_enhance_video__success ok")

    def test_enhance_video__video_not_exists(self):
        """Test the enhance_video view when the video not exists."""
        url = reverse("ai_enhancement:enhance_video", args=["fake-slug"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        print(" --->  test_enhance_video__video_not_exists ok")

    def test_enhance_video__in_maintenance(self):
        """Test the enhance_video view when in maintenance."""
        maintenance_mode_conf = Configuration.objects.get(key="maintenance_mode")
        maintenance_mode_conf.value = "1"
        maintenance_mode_conf.save()
        print(
            "MAINTENANCE MODE: ",
            (
                True
                if Configuration.objects.get(key="maintenance_mode").value == "1"
                else False
            ),
        )
        url = reverse("ai_enhancement:enhance_video", args=[self.video.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        print(" --->  test_enhance_video__in_maintenance ok")
