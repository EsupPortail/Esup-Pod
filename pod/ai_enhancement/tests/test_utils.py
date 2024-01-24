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

    @patch("requests.post")
    def test_connect_to_api_failure(self, mock_post):
        mock_response = Response()
        mock_response.status_code = 401
        mock_post.return_value = mock_response

        aristote_ai = AristoteAI(self.client_id, self.client_secret)
        result = aristote_ai.connect_to_api()
        self.assertEqual(result, mock_response)
        self.assertIsNone(aristote_ai.token)
