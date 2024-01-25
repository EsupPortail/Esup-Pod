import json

import requests
from requests import Response

API_URL = "https://aristote-preprod.k8s-cloud.centralesupelec.fr/api"
API_VERSION = "v1"


class AristoteAI:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = None

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
        """Get the AI response."""
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.token}",
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
        """Get a specific AI enrichment."""
        path = f"/{API_VERSION}/enrichments/{enrichment_id}"
        return self.get_response(path)
