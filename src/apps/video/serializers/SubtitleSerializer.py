from rest_framework import serializers
from src.apps.video.models import Subtitle


class SubtitleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subtitle
        fields = ['id', 'language', 'file', 'is_default']
