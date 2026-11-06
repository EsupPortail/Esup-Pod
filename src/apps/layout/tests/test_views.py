"""
Esup-Pod - Layout tests.
"""

import pytest
from rest_framework.test import APIClient
from django.urls import reverse
from src.apps.layout.models import BlockConfig


@pytest.fixture
def api_client():
    """Return an API client."""
    return APIClient()


@pytest.fixture
def block_config(db):
    """Create a test BlockConfig."""
    return BlockConfig.objects.create(
        frontend_id="test-carousel",
        admin_name="Test Carousel",
        is_active=True,
        display_title="Test Block",
        item_limit=5,
    )


@pytest.mark.django_db
def test_list_blocks(api_client, block_config):
    """Test retrieving the list of blocks."""
    url = reverse("blockconfig-list")
    response = api_client.get(url)
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    results = data["results"]
    assert len(results) == 1
    assert results[0]["frontend_id"] == "test-carousel"
    assert results[0]["display_title"] == "Test Block"
    assert results[0]["item_limit"] == 5


@pytest.mark.django_db
def test_retrieve_block(api_client, block_config):
    """Test retrieving a single block by frontend_id."""
    url = reverse("blockconfig-detail", args=[block_config.frontend_id])
    response = api_client.get(url)
    assert response.status_code == 200
    data = response.json()
    assert data["frontend_id"] == "test-carousel"
    assert data["display_title"] == "Test Block"


@pytest.mark.django_db
def test_layout_settings_flag(api_client, block_config, settings):
    """Test that blocks are not returned if USE_LAYOUT_BLOCKS is False."""
    settings.USE_LAYOUT_BLOCKS = False

    url = reverse("blockconfig-list")
    response = api_client.get(url)
    assert response.status_code == 200
    assert response.json()["count"] == 0
