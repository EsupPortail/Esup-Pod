"""Esup-Pod shared utilities for Python tests."""


def response_error(response):
    """Summarize a Django test response without dumping an HTML error page."""
    if response.exc_info:
        return f"{response.exc_info[0].__name__}: {response.exc_info[1]}"
    return f"HTTP {response.status_code}"
