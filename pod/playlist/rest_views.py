from rest_framework import serializers, viewsets

from pod.video.rest_views import VideoSerializer

from .models import Playlist, PlaylistContent


class PlaylistContentSerializer(serializers.ModelSerializer):
    video = VideoSerializer()

    class Meta:
        model = PlaylistContent
        fields = ("video",)


class PlaylistSerializer(serializers.HyperlinkedModelSerializer):
    videos = PlaylistContentSerializer(
        many=True, source="playlistcontent_set", read_only=True
    )

    class Meta:
        model = Playlist
        fields = (
            "id",
            "url",
            "name",
            "visibility",
            "description",
            "autoplay",
            "editable",
            "slug",
            "date_created",
            "date_updated",
            "owner",
            "additional_owners",
            "videos",
        )
        read_only_fields = ("editable",)


class PlaylistViewSet(viewsets.ModelViewSet):
    queryset = Playlist.objects.all()
    serializer_class = PlaylistSerializer
    filter_fields = (
        "owner",
        "visibility",
        "autoplay",
        "editable",
    )
