from rest_framework import serializers, viewsets
from .models import RecordingFile, Recording


class RecordingModelSerializer(
        serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Recording
        fields = ('id', 'url', 'user', 'title', 'source_file', 'type')


class RecordingFileModelSerializer(
        serializers.HyperlinkedModelSerializer):

    class Meta:
        model = RecordingFile
        fields = ('id', 'url', 'file', 'type')


class RecordingModelViewSet(viewsets.ModelViewSet):
    queryset = Recording.objects.all()
    serializer_class = RecordingModelSerializer


class RecordingFileModelViewSet(viewsets.ModelViewSet):
    queryset = RecordingFile.objects.all()
    serializer_class = RecordingFileModelSerializer
