"""Test the util functions and classes for ai_enhancement module."""

from unittest.mock import patch

from django.test import TestCase
from requests import Response

from pod.ai_enhancement.utils import AristoteAI
from pod.main.utils import extract_json_from_str
from pod.video.models import Discipline


class AristoteAITestCase(TestCase):
    """TestCase for Esup-Pod AI Enhancement utilities."""

    fixtures = ["initial_data.json"]

    def setUp(self):
        """Set up the tests."""
        self.client_id = "client_id"
        self.client_secret = "client_secret"
        for i in range(1, 6):
            Discipline.objects.create(title=f"mocked_discipline_0{i}")

    @patch("requests.post")
    def test_connect_to_api__success(self, mock_post):
        """Test the connect_to_api method when the request is successful."""
        mock_response = Response()
        mock_response.status_code = 200
        mock_response.json = lambda: {"access_token": "mocked_token"}
        mock_post.return_value = mock_response

        aristote_ai = AristoteAI(self.client_id, self.client_secret)
        result = aristote_ai.connect_to_api()
        self.assertEqual(result, {"access_token": "mocked_token"})
        self.assertEqual(aristote_ai.token, "mocked_token")
        print(" --->  test_connect_to_api__success ok")

    @patch("requests.post")
    def test_connect_to_api__failure(self, mock_post):
        """Test the connect_to_api method when the request fails."""
        mock_response = Response()
        mock_response.status_code = 401
        mock_post.return_value = mock_response

        aristote_ai = AristoteAI(self.client_id, self.client_secret)
        result = aristote_ai.connect_to_api()
        self.assertEqual(result, mock_response)
        self.assertIsNone(aristote_ai.token)
        print(" --->  test_connect_to_api__failure ok")

    @patch("requests.get")
    def test_get_ai_enhancements__success(self, mock_get):
        """Test the get_ai_enhancements method when the request is successful."""
        mock_response = Response()
        mock_response.status_code = 200
        mock_response.json = lambda: {"content": "mocked_content"}
        mock_get.return_value = mock_response

        aristote_ai = AristoteAI(self.client_id, self.client_secret)
        aristote_ai.token = "mocked_token"
        result = aristote_ai.get_ai_enhancements()
        self.assertEqual(result, {"content": "mocked_content"})
        print(" --->  test_get_ai_enhancements__success ok")

    @patch("requests.get")
    def test_get_ai_enhancements__failure(self, mock_get):
        """Test the get_ai_enhancements method when the request fails."""
        mock_response = Response()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        aristote_ai = AristoteAI(self.client_id, self.client_secret)
        aristote_ai.token = "mocked_token"
        result = aristote_ai.get_ai_enhancements()
        self.assertEqual(result, mock_response)
        print(" --->  test_get_ai_enhancements__failure ok")

    @patch("requests.get")
    def test_get_specific_ai_enhancement__success(self, mock_get):
        """Test the get_specific_ai_enhancement method when the request is successful."""
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
        result = aristote_ai.get_specific_ai_enhancement("mocked_id")
        self.assertEqual(result, content)
        print(" --->  test_get_specific_ai_enhancement__success ok")

    @patch("requests.get")
    def test_get_specific_ai_enhancement__failure(self, mock_get):
        """Test the get_specific_ai_enhancement method when the request fails."""
        mock_response = Response()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        aristote_ai = AristoteAI(self.client_id, self.client_secret)
        aristote_ai.token = "mocked_token"
        result = aristote_ai.get_specific_ai_enhancement("mocked_id")
        self.assertEqual(result, mock_response)
        print(" --->  test_get_specific_ai_enhancement__failure ok")

    @patch("requests.post")
    def test_create_enhancement_from_url__success(self, mock_post):
        """Test the create_enhancement_from_url method when the request is successful."""
        mock_response = Response()
        mock_response.status_code = 200
        mock_response.json = lambda: {
            "status": "OK",
            "id": "mocked_id",
        }
        mock_post.return_value = mock_response

        aristote_ai = AristoteAI(self.client_id, self.client_secret)
        aristote_ai.token = "mocked_token"
        result = aristote_ai.create_enhancement_from_url(
            "mocked_url",
            ["mocked_media_type_1", "mocked_media_type_2"],
            "mocked_end_user_identifier",
            "mocked_notification_webhook_url",
        )
        self.assertIsNone(result)
        print(" --->  test_create_enhancement_from_url__success ok")

    @patch("requests.post")
    def test_create_enhancement_from_url__failure(self, mock_post):
        """Test the create_enhancement_from_url method when the request fails."""
        mock_response = Response()
        mock_response.status_code = 401
        mock_post.return_value = mock_response

        aristote_ai = AristoteAI(self.client_id, self.client_secret)
        aristote_ai.token = "mocked_token"
        result = aristote_ai.create_enhancement_from_url(
            "mocked_url",
            ["mocked_media_type_1", "mocked_media_type_2"],
            "mocked_end_user_identifier",
            "mocked_notification_webhook_url",
        )
        self.assertIsNone(result)
        print(" --->  test_create_enhancement_from_url__failure ok")

    @patch("requests.get")
    def test_get_latest_enhancement_version__success(self, mock_get):
        """Test the get_latest_enhancement_version method when the request is successful."""
        mock_response = Response()
        mock_response.status_code = 200
        mock_response.json = lambda: {
            "createdAt": "2024-01-26T14:40:05+01:00",
            "updatedAt": "2024-01-26T14:40:05+01:00",
            "id": "018d45ff-bfe7-772f-b671-723ac7de674e",
            "enhancementVersionMetadata": {
                "title": "Worker enhancement",
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
        mock_get.return_value = mock_response

        aristote_ai = AristoteAI(self.client_id, self.client_secret)
        aristote_ai.token = "mocked_token"
        result = aristote_ai.get_latest_enhancement_version("mocked_id")
        self.assertEqual(result, mock_response.json())
        print(" --->  test_get_latest_enhancement_version__success ok")

    @patch("requests.get")
    def test_get_latest_enhancement_version__failure(self, mock_get):
        """Test the get_latest_enhancement_version method when the request fails."""
        mock_response = Response()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        aristote_ai = AristoteAI(self.client_id, self.client_secret)
        aristote_ai.token = "mocked_token"
        result = aristote_ai.get_latest_enhancement_version("mocked_id")
        self.assertEqual(result, mock_response)
        print(" --->  test_get_latest_enhancement_version__failure ok")

    @patch("requests.get")
    def test_get_enhancement_versions__success(self, mock_get):
        """Test the get_enhancement_versions method when the request is successful."""
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
        result = aristote_ai.get_enhancement_versions("mocked_id")
        self.assertEqual(result, mock_response.json())
        print(" --->  test_get_latest_enhancement_version__success ok")

    @patch("requests.get")
    def test_get_enhancement_versions__failure(self, mock_get):
        """Test the get_enhancement_versions method when the request fails."""
        mock_response = Response()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        aristote_ai = AristoteAI(self.client_id, self.client_secret)
        aristote_ai.token = "mocked_token"
        result = aristote_ai.get_enhancement_versions("mocked_id")
        self.assertEqual(result, mock_response)
        print(" --->  test_get_latest_enhancement_version__failure ok")

    @patch("requests.get")
    def test_get_specific_enhancement_version__success(self, mock_get):
        """Test the get_specific_enhancement_version method when the request is successful."""
        mock_response = Response()
        mock_response.status_code = 200
        mock_response.json = lambda: {
            "createdAt": "2024-01-26T14:40:05+01:00",
            "updatedAt": "2024-01-26T14:40:05+01:00",
            "id": "mocked_id",
            "enhancementVersionMetadata": {
                "title": "Worker enhancement",
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
            "lastEvaluationDate": "mocked_last_evaluation_date",
        }
        mock_get.return_value = mock_response

        aristote_ai = AristoteAI(self.client_id, self.client_secret)
        aristote_ai.token = "mocked_token"
        result = aristote_ai.get_specific_enhancement_version(
            "mocked_enhancement_id",
            "mocked_version_id",
        )
        self.assertEqual(result, mock_response.json())
        print(" --->  get_specific_enhancement_version__success ok")

    @patch("requests.get")
    def test_get_specific_enhancement_version__failure(self, mock_get):
        """Test the get_specific_enhancement_version method when the request fails."""
        mock_response = Response()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        aristote_ai = AristoteAI(self.client_id, self.client_secret)
        aristote_ai.token = "mocked_token"
        result = aristote_ai.get_specific_enhancement_version(
            "mocked_enhancement_id", "mocked_version_id"
        )
        self.assertEqual(result, mock_response)
        print(" --->  test_get_specific_enhancement_version__failure ok")

    def test_extract_json_from_str__valid_json(self):
        """Test the extract_json_from_str function with a valid JSON string."""
        content_to_extract = 'This is some text {"key": "value"} and more text.'
        result = extract_json_from_str(content_to_extract)
        self.assertEqual(result, {"key": "value"})
        print(" --->  test_extract_json_from_str__valid_json ok")

    def test_extract_json_from_str__invalid_json(self):
        """Test the extract_json_from_str function with an invalid JSON string."""
        content_to_extract = 'This is some text {"key": "value" and more text.'
        result = extract_json_from_str(content_to_extract)
        expected_result = {
            "error": "JSONDecodeError: The string is not a valid JSON string."
        }
        self.assertEqual(result, expected_result)
        print(" --->  test_extract_json_from_str__invalid_json ok")

    def test_extract_json_from_str__no_json(self):
        """Test the extract_json_from_str function with a string without JSON content."""
        content_to_extract = "This is some text without JSON content."
        result = extract_json_from_str(content_to_extract)
        expected_result = {
            "error": "JSONDecodeError: The string is not a valid JSON string."
        }
        self.assertEqual(result, expected_result)
        print(" --->  test_extract_json_from_str__no_json ok")

    def test_get_token(self):
        """Test the get_token method."""
        aristote = AristoteAI(self.client_id, self.client_secret)
        aristote.connect_to_api = lambda: setattr(aristote, "token", "mocked_token")
        token = aristote.get_token()
        self.assertEqual(token, "mocked_token")
        print(" --->  test_get_token__success ok")
