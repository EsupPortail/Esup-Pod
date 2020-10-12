from rest_framework import serializers, viewsets
from .models import Meeting
from .models import User as BBBUser


class MeetingModelSerializer(
        serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Meeting
        fields = ('id',)


class MeetingModelViewSet(viewsets.ModelViewSet):
    queryset = Meeting.objects.all()
    serializer_class = MeetingModelSerializer


class BBBUserModelSerializer(
        serializers.HyperlinkedModelSerializer):

    class Meta:
        model = BBBUser
        fields = ('id',)


class BBBUserModelViewSet(viewsets.ModelViewSet):
    queryset = BBBUser.objects.all()
    serializer_class = BBBUserModelSerializer
