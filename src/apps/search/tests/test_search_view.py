"""Esup-Pod - Tests for search view."""

import pytest
from rest_framework.test import APIClient
from django.urls import reverse


@pytest.mark.django_db
def test_search_view_disabled(settings):
    """Verify search endpoint returns empty when disabled."""
    settings.SEARCH_ENGINE = "disabled"
    client = APIClient()
    response = client.get(reverse("search-list"))
    assert response.status_code == 200
    assert response.data["count"] == 0
    assert response.data["results"] == []


@pytest.mark.django_db
def test_search_view_database_fallback(settings):
    """Verify search endpoint works with database fallback."""
    settings.SEARCH_ENGINE = "database"
    client = APIClient()
    response = client.get(reverse("search-list"), {"q": "test"})
    assert response.status_code == 200
    assert "count" in response.data
    assert "results" in response.data
