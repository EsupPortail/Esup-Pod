from rest_framework import serializers, viewsets
from .models import RecordingFile, Recording, Recorder, RecordingFileTreatment


class RecordingFileTreatmentModelSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = RecordingFileTreatment
        fields = ("id", "file", "file_size", "recorder", "type", "date_added")
        filterset_fields = ["date_added", "recorder", "file", "id"]


class RecordingModelSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Recording
        fields = (
            "id",
            "url",
            "user",
            "title",
            "source_file",
            "type",
            "date_added",
            "recorder",
        )


class RecorderModelSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Recorder
        fields = ("id", "name", "description", "address_ip", "recording_type", "sites")


class RecordingFileModelSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = RecordingFile
        fields = ("id", "url", "file", "recorder")


class RecordingFileTreatmentModelViewSet(viewsets.ModelViewSet):
    queryset = RecordingFileTreatment.objects.all()
    serializer_class = RecordingFileTreatmentModelSerializer
    filterset_fields = ["date_added", "recorder", "file", "id"]


class RecordingModelViewSet(viewsets.ModelViewSet):
    queryset = Recording.objects.all()
    serializer_class = RecordingModelSerializer


class RecordingFileModelViewSet(viewsets.ModelViewSet):
    queryset = RecordingFile.objects.all()
    serializer_class = RecordingFileModelSerializer


class RecorderModelViewSet(viewsets.ModelViewSet):
    queryset = Recorder.objects.all()
    serializer_class = RecorderModelSerializer
