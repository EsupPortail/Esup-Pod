"""
End-to-End (E2E) Test Scenario Script.

This script performs a series of automated checks to validate the availability
and basic security configuration of the deployed application. It is used
in the CI/CD pipeline to ensure the service is up and running correctly
after deployment.

Checks included:
1. API Health: Verifies that the API documentation endpoint is reachable.
2. Security Headers: Checks for the presence of essential security headers.
3. Admin Access: Confirms that the authentication login page is accessible.
"""

import sys

import time
import os
import requests



API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
ADMIN_USER = os.getenv("DJANGO_SUPERUSER_USERNAME", "admin")
ADMIN_PASS = os.getenv("DJANGO_SUPERUSER_PASSWORD", "admin")

DEFAULT_TIMEOUT = 10
RETRY_DELAY = 5


def log(message: str) -> None:
    """Print formatted E2E log message."""
    print(f"[E2E] {message}")


def test_api_health(retries: int = 5) -> bool:
    """
    Check if the API documentation endpoint is reachable.
    Retries several times before failing.
    """
    url = f"{API_URL}/api/docs/"

    for attempt in range(1, retries + 1):
        log(f"Checking API health at {url} (attempt {attempt}/{retries})")

        try:
            response = requests.get(url, timeout=DEFAULT_TIMEOUT)

            if response.status_code == 200:
                log("API is responding (200 OK)")
                return True

            log(f"Unexpected status code: {response.status_code}")

        except requests.RequestException as exc:
            log(f"Connection error: {exc}")

        time.sleep(RETRY_DELAY)

    log("API unreachable after multiple attempts")
    return False


def test_admin_login() -> None:
    """
    Check if the authentication endpoint is reachable.
    This does not authenticate, only verifies that the login page exists.
    """
    url = f"{API_URL}/accounts/login"
    log(f"Checking auth endpoint at {url}")

    response = requests.get(url, allow_redirects=True, timeout=DEFAULT_TIMEOUT)

    if response.status_code == 200:
        log("Auth login page reachable")
    else:
        log(f"Auth page returned status {response.status_code}")


def test_security_headers() -> None:
    """
    Check presence of basic security headers.
    """
    url = f"{API_URL}/api/docs/"
    log("Checking security headers")

    response = requests.get(url, timeout=DEFAULT_TIMEOUT)

    if "X-Frame-Options" in response.headers:
        log("X-Frame-Options header is present")
    else:
        log("Missing X-Frame-Options header")


def run_tests() -> None:
    """Run all E2E checks."""
    log("Starting E2E tests")

    # Warmup delay
    time.sleep(2)

    if not test_api_health():
        sys.exit(1)

    test_security_headers()
    test_admin_login()

    log("All checks completed")


if __name__ == "__main__":
    run_tests()
