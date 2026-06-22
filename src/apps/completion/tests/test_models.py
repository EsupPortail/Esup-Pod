"""
Esup-Pod - Tests for completion models.
"""

import pytest
from src.apps.completion.models import Contributor


@pytest.mark.django_db
def test_contributor_creation():
    """Test creating a contributor and its properties."""
    contributor = Contributor.objects.create(
        first_name="John", last_name="Doe", email_address="john.doe@example.com"
    )
    assert contributor.full_name == "John Doe"
    assert contributor.get_noscript_mail() == "john.doe__AT__example.com"
