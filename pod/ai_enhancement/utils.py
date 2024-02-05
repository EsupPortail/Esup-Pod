import json

import requests
from requests import Response

from pod.video.models import Discipline

API_URL = "https://aristote-preprod.k8s-cloud.centralesupelec.fr/api"
API_VERSION = "v1"


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

    def get_response(self, path: str) -> Response or None:
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

    def get_ai_enrichments(self) -> Response or None:
        """Get the AI enrichments."""
        path = f"/{API_VERSION}/enrichments"
        return self.get_response(path)

    def get_specific_ai_enrichment(self, enrichment_id: str) -> Response or None:
        """
        Get a specific AI enrichment.

        Args:
            enrichment_id (str): The enrichment id.
        """
        path = f"/{API_VERSION}/enrichments/{enrichment_id}"
        return self.get_response(path)

    def create_enrichment_from_url(
            self,
            url: str,
            media_types: list,
            end_user_identifier: str,
            notification_webhook_url: str
    ) -> Response or None:
        """Create an enrichment from a file."""
        path = f"/{API_VERSION}/enrichments/url"
        data = {
            "url": url,
            "notificationWebhookUrl": notification_webhook_url,
            "enrichmentParameters": {
                "mediaTypes": media_types,
                "disciplines": list(
                    Discipline.objects.all().values_list("title", flat=True)
                ),
                "aiEvaluation": "true"      # TODO: change this
            },
            "enduserIdentifier": end_user_identifier,
        }
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.get_token()}",
        }
        try:
            response = requests.post(
                API_URL + path,
                data=json.dumps(data),
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

    def get_latest_enrichment_version(self, enrichment_id: str) -> Response or None:
        """Get the latest enrichment version."""
        path = f"/{API_VERSION}/enrichments/{enrichment_id}/versions/latest"
        return self.get_response(path)

    def get_enrichment_versions(self, enrichment_id: str, with_transcript: bool = True) -> Response or None:
        """Get the enrichment versions."""
        path = f"/{API_VERSION}/enrichments/{enrichment_id}/versions?withTranscript={with_transcript}"
        return self.get_response(path)

    def get_specific_enrichment_version(self, enrichment_id: str, version_id: str) -> Response or None:
        """Get a specific version."""
        path = f"/{API_VERSION}/enrichments/{enrichment_id}/versions/{version_id}"
        return self.get_response(path)
