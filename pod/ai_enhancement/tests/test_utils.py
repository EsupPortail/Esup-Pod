from unittest.mock import patch

from django.test import TestCase
from requests import Response

from pod.ai_enhancement.utils import AristoteAI


class AristoteAITestCase(TestCase):
    """TestCase for Esup-Pod AI Enhancement utilities."""

    fixtures = ["initial_data.json"]

    def setUp(self):
        self.client_id = "client_id"
        self.client_secret = "client_secret"

    @patch("requests.post")
    def test_connect_to_api_success(self, mock_post):
        mock_response = Response()
        mock_response.status_code = 200
        mock_response.json = lambda: {"access_token": "mocked_token"}
        mock_post.return_value = mock_response

        aristote_ai = AristoteAI(self.client_id, self.client_secret)
        result = aristote_ai.connect_to_api()
        self.assertEqual(result, {"access_token": "mocked_token"})
        self.assertEqual(aristote_ai.token, "mocked_token")
        print(" --->  test_connect_to_api_success ok")

    @patch("requests.post")
    def test_connect_to_api_failure(self, mock_post):
        mock_response = Response()
        mock_response.status_code = 401
        mock_post.return_value = mock_response

        aristote_ai = AristoteAI(self.client_id, self.client_secret)
        result = aristote_ai.connect_to_api()
        self.assertEqual(result, mock_response)
        self.assertIsNone(aristote_ai.token)
        print(" --->  test_connect_to_api_failure ok")

    @patch("requests.get")
    def test_get_ai_enrichments_success(self, mock_get):
        mock_response = Response()
        mock_response.status_code = 200
        mock_response.json = lambda: {"content": "mocked_content"}
        mock_get.return_value = mock_response

        aristote_ai = AristoteAI(self.client_id, self.client_secret)
        aristote_ai.token = "mocked_token"
        result = aristote_ai.get_ai_enrichments()
        self.assertEqual(result, {"content": "mocked_content"})
        print(" --->  test_get_ai_enrichments_success ok")

    @patch("requests.get")
    def test_get_ai_enrichments_failure(self, mock_get):
        mock_response = Response()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        aristote_ai = AristoteAI(self.client_id, self.client_secret)
        aristote_ai.token = "mocked_token"
        result = aristote_ai.get_ai_enrichments()
        self.assertEqual(result, mock_response)
        print(" --->  test_get_ai_enrichments_failure ok")

    @patch("requests.get")
    def test_get_specific_ai_enrichment_success(self, mock_get):
        content = {
            "id": "mocked_id",
            "status": "mocked_status",
            "failureCause": None,
            "media": {
                "originalFileName": "mocked_originalFileName",
                "mineType": "mocked_mineType",
            },
            "notificationStatus": None,
            "disciplines": [
                "mocked_discipline_01",
                "mocked_discipline_02",
                "mocked_discipline_03",
                "mocked_discipline_04",
                "mocked_discipline_05",
            ],
            "mediaTypes": ["mocked_mediaType_01", "mocked_mediaType_02"],
            "notifiedAt": None,
            "aiEvaluation": "mocked_aiEvaluation",
            "endUserIdentifier": "mocked_endUserIdentifier",
            "initialVersionId": "mocked_initialVersionId",
        }
        mock_response = Response()
        mock_response.status_code = 200
        mock_response.json = lambda: content
        mock_get.return_value = mock_response

        aristote_ai = AristoteAI(self.client_id, self.client_secret)
        aristote_ai.token = "mocked_token"
        result = aristote_ai.get_specific_ai_enrichment("mocked_id")
        self.assertEqual(result, content)
        print(" --->  test_get_specific_ai_enrichment_success ok")

    @patch("requests.get")
    def test_get_specific_ai_enrichment_failure(self, mock_get):
        mock_response = Response()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        aristote_ai = AristoteAI(self.client_id, self.client_secret)
        aristote_ai.token = "mocked_token"
        result = aristote_ai.get_specific_ai_enrichment("mocked_id")
        self.assertEqual(result, mock_response)
        print(" --->  test_get_specific_ai_enrichment_failure ok")

    @patch("requests.post")
    def test_create_enrichment_from_url_success(self, mock_post):
        mock_response = Response()
        mock_response.status_code = 200
        mock_response.json = lambda: {
            "status": "OK",
            "id": "mocked_id",
        }
        mock_post.return_value = mock_response

        aristote_ai = AristoteAI(self.client_id, self.client_secret)
        aristote_ai.token = "mocked_token"
        result = aristote_ai.create_enrichment_from_url(
            "mocked_url",
            ["mocked_media_type_1", "mocked_media_type_2"],
            "mocked_end_user_identifier",
            "mocked_notification_webhook_url")
        self.assertEqual(result, mock_response.json())
        print(" --->  test_create_enrichment_from_url_success ok")

    @patch("requests.post")
    def test_create_enrichment_from_url_failure(self, mock_post):
        mock_response = Response()
        mock_response.status_code = 401
        mock_post.return_value = mock_response

        aristote_ai = AristoteAI(self.client_id, self.client_secret)
        aristote_ai.token = "mocked_token"
        result = aristote_ai.create_enrichment_from_url(
            "mocked_url",
            ["mocked_media_type_1", "mocked_media_type_2"],
            "mocked_end_user_identifier",
            "mocked_notification_webhook_url")
        self.assertEqual(result, mock_response)
        print(" --->  test_create_enrichment_from_url_failure ok")

    @patch("requests.get")
    def test_get_latest_enrichment_version_success(self, mock_get):
        mock_response = Response()
        mock_response.status_code = 200
        mock_response.json = lambda: {
            "createdAt": "2024-01-26T14:40:05+01:00",
            "updatedAt": "2024-01-26T14:40:05+01:00",
            "id": "018d45ff-bfe7-772f-b671-723ac7de674e",
            "enrichmentVersionMetadata": {
                "title": "Worker enrichment",
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
        mock_get.return_value = mock_response

        aristote_ai = AristoteAI(self.client_id, self.client_secret)
        aristote_ai.token = "mocked_token"
        result = aristote_ai.get_latest_enrichment_version("mocked_id")
        self.assertEqual(result, mock_response.json())
        print(" --->  test_get_latest_enrichment_version_success ok")

    @patch("requests.get")
    def test_get_latest_enrichment_version_failure(self, mock_get):
        mock_response = Response()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        aristote_ai = AristoteAI(self.client_id, self.client_secret)
        aristote_ai.token = "mocked_token"
        result = aristote_ai.get_latest_enrichment_version("mocked_id")
        self.assertEqual(result, mock_response)
        print(" --->  test_get_latest_enrichment_version_failure ok")

    @patch("requests.get")
    def test_get_enrichment_versions_success(self, mock_get):
        mock_response = Response()
        mock_response.status_code = 200
        mock_response.json = lambda: {
            "content": [],
            "totalElements": 0,
            "currentPage": 1,
            "isLastPage": True,
        }
        mock_get.return_value = mock_response

        aristote_ai = AristoteAI(self.client_id, self.client_secret)
        aristote_ai.token = "mocked_token"
        result = aristote_ai.get_enrichment_versions("mocked_id")
        self.assertEqual(result, mock_response.json())
        print(" --->  test_get_latest_enrichment_version_success ok")

    @patch("requests.get")
    def test_get_enrichment_versions_failure(self, mock_get):
        mock_response = Response()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        aristote_ai = AristoteAI(self.client_id, self.client_secret)
        aristote_ai.token = "mocked_token"
        result = aristote_ai.get_enrichment_versions("mocked_id")
        self.assertEqual(result, mock_response)
        print(" --->  test_get_latest_enrichment_version_failure ok")
