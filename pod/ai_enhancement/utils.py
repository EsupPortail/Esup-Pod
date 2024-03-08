import json

from django.conf import settings

import requests
from requests import Response

from pod.ai_enhancement.models import AIEnhancement
from pod.main.utils import extract_json_from_str
from pod.video.models import Discipline, Video

API_URL = getattr(settings, "API_URL", "")
API_VERSION = getattr(settings, "API_VERSION", "")


class AristoteAI:
    """Aristote AI Enhancement utilities."""

    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = None

    def get_token(self):
        """Get the token."""
        if self.token is None:
            self.connect_to_api()
        return self.token

    def connect_to_api(self) -> Response or None:
        """Connect to the API."""
        path = "/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        try:
            response = requests.post(
                API_URL + path,
                data=json.dumps(data),
                headers=headers,
            )
            if response.status_code == 200:
                self.token = response.json()["access_token"]
                return response.json()
            else:
                print(f"Error: {response.status_code}")
            return response
        except requests.exceptions.RequestException as e:
            print(f"Request Exception: {e}")
            return None

    def get_response(self, path: str) -> dict or None:
        """
        Get the AI response.

        Args:
            path (str): The path to the API endpoint.
        """
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.get_token()}",
        }
        try:
            response = requests.get(
                API_URL + path,
                headers=headers,
            )
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error: {response.status_code}")
            return response
        except requests.exceptions.RequestException as e:
            print(f"Request Exception: {e}")
            return None

    def get_ai_enhancements(self) -> dict or None:
        """Get the AI enhancements."""
        path = f"/{API_VERSION}/enhancements"
        return self.get_response(path)

    def get_specific_ai_enhancement(self, enhancement_id: str) -> dict or None:
        """
        Get a specific AI enhancement.

        Args:
            enhancement_id (str): The enhancement id.
        """
        path = f"/{API_VERSION}/enhancements/{enhancement_id}"
        return self.get_response(path)

    def create_enhancement_from_url(
            self,
            url: str,
            media_types: list,
            end_user_identifier: str,
            notification_webhook_url: str
    ) -> dict or None:
        """Create an enhancement from a file."""
        if Discipline.objects.count() > 0:
            path = f"/{API_VERSION}/enhancements/url"
            data = {
                "url": url,
                "notificationWebhookUrl": notification_webhook_url,
                "enhancementParameters": {
                    "mediaTypes": media_types,
                    "disciplines": list(
                        Discipline.objects.all().values_list("title", flat=True)
                    ),
                    # "aiEvaluation": "true"                    # TODO: change this
                },
                "enduserIdentifier": end_user_identifier,
            }
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.get_token()}",
            }
            try:
                response = requests.post(
                    API_URL + path,
                    data=json.dumps(data),
                    headers=headers,
                )
                if response.status_code == 200:
                    return extract_json_from_str(response.content.decode("utf-8")) if response.content else None
                else:
                    print(f"Error: {response.status_code}")
                return None
            except requests.exceptions.RequestException as e:
                print(f"Request Exception: {e}")
                return None
        else:
            raise ValueError("No discipline in the database.")

    def get_latest_enhancement_version(self, enhancement_id: str) -> dict or None:
        """Get the latest enhancement version."""
        path = f"/{API_VERSION}/enhancements/{enhancement_id}/versions/latest"
        return self.get_response(path)

    def get_enhancement_versions(self, enhancement_id: str, with_transcript: bool = True) -> dict or None:
        """Get the enhancement versions."""
        path = f"/{API_VERSION}/enhancements/{enhancement_id}/versions?withTranscript={with_transcript}"
        return self.get_response(path)

    def get_specific_enhancement_version(self, enhancement_id: str, version_id: str) -> dict or None:
        """Get a specific version."""
        path = f"/{API_VERSION}/enhancements/{enhancement_id}/versions/{version_id}"
        return self.get_response(path)


def enhancement_is_already_asked(video: Video) -> bool:
    """Check if the enhancement is already asked."""
    return AIEnhancement.objects.filter(video=video).exists()


def enhancement_is_ready(video: Video) -> bool:
    """Check if the enhancement is ready."""
    return AIEnhancement.objects.filter(video=video, is_ready=True).exists()
