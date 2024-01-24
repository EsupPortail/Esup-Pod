import json
import requests

API_URL = "https://aristote-preprod.k8s-cloud.centralesupelec.fr/api"
API_VERSION = "v1"


class AristoteAI:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = None

    def connect_to_api(self) -> object:
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

    def get_ai_enrichments(self) -> object:
        """Get the AI enrichments."""
        path = f"/{API_VERSION}/enrichments"
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


# TODO To remove after tests
aristote_ai = AristoteAI("pod_integration", "a3.dlYTV4dkhh109:M1")
print(aristote_ai.connect_to_api())
print(aristote_ai.token)
print(aristote_ai.get_ai_enrichments())
