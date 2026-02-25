import logging
from typing import Any, Dict
import requests

from src.apps.encoding.conf import encoding_settings

logger = logging.getLogger(__name__)


class RunnerClient:
    """Client for the Esup-Runner Manager API."""

    def __init__(self, url: str, token: str):
        self.url = url.rstrip("/")
        self.token = token
        self.headers = {"X-API-Token": self.token}

    def execute_task(
        self,
        video_id: str,
        source_url: str,
        notify_url: str = "",
        parameters: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Executes a task on the runner manager.
        """
        endpoint = f"{self.url}/task/execute"

        payload = {
            "etab_name": "Pod",
            "app_name": "Pod",
            "app_version": "5.0.0",
            "task_type": "encoding",
            "source_url": source_url,
            "notify_url": notify_url,
            "parameters": parameters or {},
        }

        try:
            response = requests.post(
                endpoint, json=payload, headers=self.headers, timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(
                "Failed to execute task on runner manager: %s",
                e,
                exc_info=True,
            )
            if hasattr(e, "response") and e.response is not None:
                logger.error(
                    "Runner manager response body: %s",
                    e.response.text,
                )
            raise ConnectionError("Runner manager API error: %s" % e)


def get_runner_client() -> RunnerClient:
    """Factory to get the configured runner client."""
    from config.env import env
    manager_url = env("ENCODING_MANAGER_URL", default="")
    manager_token = env("ENCODING_MANAGER_TOKEN", default="")
    return RunnerClient(url=manager_url, token=manager_token)
