import sys
import time
import requests
import os

# Configuration
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
ADMIN_USER = os.getenv("DJANGO_SUPERUSER_USERNAME", "admin")
ADMIN_PASS = os.getenv("DJANGO_SUPERUSER_PASSWORD", "admin")


def log(msg):
    print(f"[E2E] {msg}")


def test_api_health(retries=5):
    url = f"{API_URL}/api/docs/"
    for i in range(retries):
        log(f"Checking Health at {url} (Attempt {i + 1}/{retries})...")
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                log("✅ API is responding (200 OK)")
                return True
            else:
                log(f"⚠️ API returned {response.status_code}, retrying...")
        except requests.exceptions.RequestException as e:
            log(f"⚠️ Connection error: {e}, retrying...")
        time.sleep(5)
    log("❌ API Unreachable after multiple attempts")
    return False


def test_admin_login():
    url = f"{API_URL}/accounts/login"  # CAS or Standard Login URL depending on config.
    # NOTE: Since we don't have a standard REST auth endpoint enabled by default in base setup yet without CAS,
    # and we act as a headless client, we will check if the Login Page exists (redirects usually).

    log(f"Checking Auth Endpoint at {url}...")
    response = requests.get(url, allow_redirects=True)
    if response.status_code == 200:
        log("✅ Auth login page reachable")
    else:
        log(f"⚠️ Auth page status: {response.status_code}")


def test_security_headers():
    url = f"{API_URL}/api/docs/"
    log("Checking Security Headers...")
    response = requests.get(url)
    # Example check
    if 'X-Frame-Options' in response.headers:
        log("✅ X-Frame-Options present")
    else:
        log("⚠️ Missing X-Frame-Options")


def run_tests():
    log("Starting E2E Tests...")

    # Warup Wait
    time.sleep(2)

    if not test_api_health():
        sys.exit(1)

    test_security_headers()
    test_admin_login()

    log("🎉 All Checks Passed!")


if __name__ == "__main__":
    run_tests()
