"""
Esup-Pod - Module providing tests for the live app's management commands.
"""

import pytest
from django.core.management import call_command


@pytest.mark.django_db
def test_live_viewcounter_command():
    """Test that the live_viewcounter command executes without errors."""
    # Just run the command to hit the lines
    call_command("live_viewcounter")


@pytest.mark.django_db
def test_check_live_start_stop_command():
    """Test that the check_live_start_stop command executes without errors."""
    # Just run the command to hit the lines
    call_command("check_live_start_stop")
