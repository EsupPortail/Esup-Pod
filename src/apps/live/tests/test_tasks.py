"""
Esup-Pod - Module providing tests for the live app's background tasks.
"""

import pytest
from src.apps.live.tasks import cleanup_heartbeats_task


@pytest.mark.django_db
def test_cleanup_heartbeats_task():
    """Test that the cleanup_heartbeats_task executes without errors."""
    # Simple test to hit the lines in cleanup_heartbeats_task
    cleanup_heartbeats_task()
