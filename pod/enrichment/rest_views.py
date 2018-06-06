from .models import Enrichment, EnrichmentImage, EnrichmentFile
from rest_framework import serializers, viewsets

# Serializers define the API representation.


class EnrichmentImageSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = EnrichmentImage
        fields = ('id', 'url', 'file')


class EnrichmentFileSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = EnrichmentFile
        fields = ('id', 'url', 'file')


class EnrichmentSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Enrichment
        fields = ('id', 'url', 'video', 'title', 'stop_video', 'start',
                  'end', 'type', 'image', 'document', 'richtext', 'weblink',
                  'embed')

#############################################################################
# ViewSets define the view behavior.
#############################################################################


class EnrichmentViewSet(viewsets.ModelViewSet):
    queryset = Enrichment.objects.all().order_by('video', 'start')
    serializer_class = EnrichmentSerializer


class EnrichmentFileViewSet(viewsets.ModelViewSet):
    queryset = EnrichmentFile.objects.all()
    serializer_class = EnrichmentFileSerializer


class EnrichmentImageViewSet(viewsets.ModelViewSet):
    queryset = EnrichmentImage.objects.all()
    serializer_class = EnrichmentImageSerializer
