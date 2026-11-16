"""
Esup-Pod - Serializer for the Chapter model.
"""

from django.utils.translation import gettext as _
from rest_framework import serializers

from src.apps.video.models import Chapter


class ChapterSerializer(serializers.ModelSerializer):
    """
    Esup-Pod - Serializes Chapter instances for API input and output.

    Validation rules (ported from Pod v4):
    - ``time_start`` must be between 0 and ``video.duration - 1``;
    - two chapters of the same video cannot start at the same time.

    The ``video`` field is only used at creation: it is ignored on update.
    """

    class Meta:
        """Metadata for the ChapterSerializer."""

        model = Chapter
        fields = ["id", "video", "title", "time_start"]
        read_only_fields = ["id"]
        # The uniqueness rule (same video and same start time) is checked in
        # validate() with a clearer message, so the default validator is dropped.
        validators = []

    def validate(self, attrs):
        """Check the start time against the video duration and other chapters."""
        instance = self.instance
        video = instance.video if instance else attrs.get("video")
        time_start = attrs.get("time_start", instance.time_start if instance else 0)

        if video is None:
            return attrs

        duration = video.duration or 0
        if duration <= 0:
            raise serializers.ValidationError(
                {"time_start": _("The video duration is not available yet.")}
            )
        if not 0 <= time_start < duration:
            raise serializers.ValidationError(
                {
                    "time_start": _(
                        "Please enter a start time between 0 and {max_time}."
                    ).format(max_time=duration - 1)
                }
            )

        clashing = Chapter.objects.filter(video=video, time_start=time_start)
        if instance:
            clashing = clashing.exclude(pk=instance.pk)
        other = clashing.first()
        if other:
            raise serializers.ValidationError(
                {
                    "time_start": _(
                        "A chapter already starts at this time: {title}."
                    ).format(title=other.title)
                }
            )
        return attrs

    def update(self, instance, validated_data):
        """Update a chapter without allowing it to be moved to another video."""
        validated_data.pop("video", None)
        return super().update(instance, validated_data)
