from rest_framework import serializers, viewsets

from .models import Playlist
from .models import PlaylistElement


# Serializers define the API representation.


class PlaylistSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Playlist
        fields = ("id", "title", "slug", "owner", "description", "visible")


class PlaylistElementSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = PlaylistElement
        fields = (
            "id",
            "playlist",
            "video",
            "position",
        )


#############################################################################
# ViewSets define the view behavior.
#############################################################################


class PlaylistViewSet(viewsets.ModelViewSet):
    queryset = Playlist.objects.all()
    serializer_class = PlaylistSerializer


class PlaylistElementViewSet(viewsets.ModelViewSet):
    queryset = PlaylistElement.objects.all()
    serializer_class = PlaylistElementSerializer
