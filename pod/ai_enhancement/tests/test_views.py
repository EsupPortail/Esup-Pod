import json
from unittest.mock import patch

from django.contrib.auth.models import User
from django.http import JsonResponse
from django.test import RequestFactory, TestCase
from django.urls import reverse

from pod.ai_enhancement.models import AIEnrichment
from pod.ai_enhancement.views import enrich_video_json, toggle_webhook
from pod.video.models import Video, Type


class EnrichVideoJsonViewTest(TestCase):
    """Test the enrich_video_json view."""

    fixtures = ["initial_data.json"]

    def setUp(self):
        """Set up the test."""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username="testuser")
        self.video = Video.objects.create(
            slug="test-video",
            owner=self.user,
            video="test_video.mp4",
            title="Test video",
            description="This is a test video.",
            type=Type.objects.get(id=1),
        )
        self.enrichment = AIEnrichment.objects.create(video=self.video, ai_enrichment_id_in_aristote="123")

    @patch("pod.ai_enhancement.views.AristoteAI")
    def test_enrich_video_json__success(self, mock_aristote_ai):
        """Test the enrich_video_json view when successful."""
        json_data = {
            "createdAt": "2024-01-26T14:40:05+01:00",
            "updatedAt": "2024-01-26T14:40:05+01:00",
            "id": "018d45ff-bfe7-772f-b671-723ac7de674e",
            "enrichmentVersionMetadata": {
                "title": "Random title",
                "description": "This is an example of an enrichment version",
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
        mock_aristote_instance.get_latest_enrichment_version.return_value = json_data
        url = reverse("ai_enhancement:enrich_video_json", args=[self.video.slug])
        request = self.factory.get(url)
        response = enrich_video_json(request, self.video.slug)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response, JsonResponse)
        mock_aristote_instance.get_latest_enrichment_version.assert_called_once_with(
            self.enrichment.ai_enrichment_id_in_aristote,
        )
        expected_json = json
        self.assertJSONEqual(str(response.content, encoding="utf-8"), expected_json)
        print(" --->  test_enrich_video_json__success ok")


class ReceiveWebhookViewTest(TestCase):
    """Test the receive_webhook view."""

    fixtures = ["initial_data.json"]

    def setUp(self):
        """Set up the test."""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username="test_user")
        self.video = Video.objects.create(
            slug="test-video",
            owner=self.user,
            video="test_video.mp4",
            title="Test video",
            description="This is a test video.",
            type=Type.objects.get(id=1),
        )
        self.enrichment = AIEnrichment.objects.create(
            video=self.video,
            ai_enrichment_id_in_aristote="123"
        )

    def test_toggle_webhook__success(self):
        """Test the receive_webhook view when successful."""
        url = reverse("ai_enhancement:webhook")
        request_data = {
            "id": "123",
            "status": "SUCCESS",
            "initialVersionId": "018e08b5-9ea0-73a7-bcd7-34764e3b0775",
            "failureCause": None,
        }
        request = self.factory.post(url, data=request_data, content_type="application/json")
        response = toggle_webhook(request)
        self.enrichment.refresh_from_db()
        self.assertTrue(self.enrichment.is_ready)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response, JsonResponse)
        self.assertEqual(json.loads(response.content.decode()), {"status": "OK"})
        print(" --->  test_toggle_webhook__success ok")

    def test_toggle_webhook__bad_method(self):
        """Test the receive_webhook view when using a bad method."""
        url = reverse("ai_enhancement:webhook")
        request = self.factory.get(url)
        response = toggle_webhook(request)
        self.enrichment.refresh_from_db()
        self.assertFalse(self.enrichment.is_ready)
        self.assertEqual(response.status_code, 405)
        self.assertIsInstance(response, JsonResponse)
        self.assertEqual(json.loads(response.content.decode()), {"error": "Only POST requests are allowed."})
        print(" --->  test_toggle_webhook__bad_method ok")

    def test_toggle_webhook__enrichment_not_found(self):
        """Test the receive_webhook view when the enrichment is not found."""
        url = reverse("ai_enhancement:webhook")
        request_data = {
            "id": "456",
            "status": "SUCCESS",
            "initialVersionId": "018e08b5-9ea0-73a7-bcd7-34764e3b0775",
            "failureCause": None,
        }
        request = self.factory.post(url, data=request_data, content_type="application/json")
        response = toggle_webhook(request)
        self.enrichment.refresh_from_db()
        self.assertFalse(self.enrichment.is_ready)
        self.assertEqual(response.status_code, 404)
        self.assertIsInstance(response, JsonResponse)
        self.assertEqual(json.loads(response.content.decode()), {"error": "Enrichment not found."})
        print(" --->  test_toggle_webhook__enrichment_not_found ok")

    def test_toggle_webhook__no_id_in_request(self):
        """Test the receive_webhook view when there is no id in the request."""
        url = reverse("ai_enhancement:webhook")
        request_data = {
            "status": "SUCCESS",
            "initialVersionId": "018e08b5-9ea0-73a7-bcd7-34764e3b0775",
            "failureCause": None,
        }
        request = self.factory.post(url, data=request_data, content_type="application/json")
        response = toggle_webhook(request)
        self.enrichment.refresh_from_db()
        self.assertFalse(self.enrichment.is_ready)
        self.assertEqual(response.status_code, 400)
        self.assertIsInstance(response, JsonResponse)
        self.assertEqual(json.loads(response.content.decode()), {"error": "No id in the request."})
        print(" --->  test_toggle_webhook__no_id_in_request ok")
