"""
Esup-Pod - Django group serializer.
"""

from django.contrib.auth.models import Group
from rest_framework import serializers


class GroupSerializer(serializers.ModelSerializer):
    """
    Serializer for standard Django groups.
    """

    class Meta:
        """Group serializer metadata."""

        model = Group
        fields = ("id", "name")
