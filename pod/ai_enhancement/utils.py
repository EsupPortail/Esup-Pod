import json
from typing import Mapping

import requests


class AIEnhancement:
    """Class to connect to the AI Enhancement API."""

    def __init__(self, api_url):
        """
        Initialize the class.

        Args:
            api_url (str): The API URL.
        """
        self.api_url = api_url

    def connect_to_api(self, data: Mapping[str, str], headers: Mapping[str, str], path: str) -> object:
        """
        Connect to the API.

        Args:
            data (:class:`typing.Mapping[str, str]`): The data.
            headers (:class:`typing.Mapping[str, str]`): The headers.
            path (str): The path.

        Returns:
            object: The response.
        """
        try:
            response = requests.post(
                self.api_url + path,
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


class AristoteAI(AIEnhancement):
    def __init__(self, client_id, client_secret):
        super().__init__("https://aristote-preprod.k8s-cloud.centralesupelec.fr/api")
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = None

    def connect_to_api(self, **kwargs) -> object:
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
        return super().connect_to_api(data, headers, path)


aristote_ai = AristoteAI("pod_integration", "a3.dlYTV4dkhh109:M1")
print(aristote_ai.connect_to_api())
