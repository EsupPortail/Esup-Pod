from .models import Enrichment
from rest_framework import serializers, viewsets

# Serializers define the API representation.


class EnrichmentSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Enrichment
        fields = (
            "id",
            "url",
            "video",
            "title",
            "stop_video",
            "start",
            "end",
            "type",
            "image",
            "document",
            "richtext",
            "weblink",
            "embed",
        )


#############################################################################
# ViewSets define the view behavior.
#############################################################################


class EnrichmentViewSet(viewsets.ModelViewSet):
    queryset = Enrichment.objects.all().order_by("video", "start")
    serializer_class = EnrichmentSerializer
