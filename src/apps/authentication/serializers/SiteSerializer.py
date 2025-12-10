from rest_framework import serializers
from django.contrib.sites.models import Site

class SiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Site
        fields = ("id", "name", "domain")