from rest_framework import serializers, viewsets
from .models import Recording, Recorder, Job

class JobModelSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Job
        fields = ('mediapath', 'file_size', 'date_added', 'email_sent', 'date_email_sent')

class RecordingModelSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Recording
        fields = ('id', 'title', 'date_added', 'mediapath', 'type', 'recorder', 'comment')

class RecorderModelSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Recorder
        fields = ('id', 'name', 'description', 'address_ip', 'salt', 'user', 'type', 'directory')
        lookup_field = 'name'

class JobModelViewSet(viewsets.ModelViewSet):
    queryset = Job.objects.all()
    serializer_class = JobModelSerializer

class RecordingModelViewSet(viewsets.ModelViewSet):
    queryset = Recording.objects.all()
    serializer_class = RecordingModelSerializer

class RecorderModelViewSet(viewsets.ModelViewSet):
    queryset = Recorder.objects.all().order_by('id')
    serializer_class = RecorderModelSerializer
    lookup_field = 'name'