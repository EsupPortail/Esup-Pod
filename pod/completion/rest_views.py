from .models import Contributor, Document, Track, Overlay
from rest_framework import serializers, viewsets

# Serializers define the API representation.


class ContributorSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Contributor
        fields = (
            "id",
            "url",
            "video",
            "name",
            "email_address",
            "role",
            "weblink",
        )


class DocumentSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Document
        fields = ("id", "url", "video", "document")


class TrackSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Track
        fields = ("id", "url", "video", "kind", "lang", "src")


class OverlaySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Overlay
        fields = (
            "id",
            "url",
            "video",
            "title",
            "time_start",
            "time_end",
            "content",
            "position",
            "background",
        )


#############################################################################
# ViewSets define the view behavior.
#############################################################################


class ContributorViewSet(viewsets.ModelViewSet):
    queryset = Contributor.objects.all()
    serializer_class = ContributorSerializer
    filterset_fields = [
        "video",
        "role",
    ]


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    filterset_fields = [
        "video",
    ]


class TrackViewSet(viewsets.ModelViewSet):
    queryset = Track.objects.all()
    serializer_class = TrackSerializer
    filterset_fields = [
        "video",
    ]


class OverlayViewSet(viewsets.ModelViewSet):
    queryset = Overlay.objects.all()
    serializer_class = OverlaySerializer
    filterset_fields = [
        "video",
    ]
