"""
Esup-Pod - Site serializer.
"""

from django.contrib.sites.models import Site
from rest_framework import serializers


class SiteSerializer(serializers.ModelSerializer):
    """
    Serializer for the Django Site model.
    """

    class Meta:
        """Meta."""

        model = Site
        fields = ("id", "name", "domain")
