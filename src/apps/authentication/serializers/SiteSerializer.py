from django.contrib.sites.models import Site
from rest_framework import serializers


class SiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Site
        fields = ("id", "name", "domain")
