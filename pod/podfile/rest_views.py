"""Esup-Pod REST views."""

from .models import UserFolder
from .models import CustomImageModel, CustomFileModel
from rest_framework import serializers, viewsets

# Serializers define the API representation.


class UserFolderSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = UserFolder
        fields = ("id", "url", "name", "owner")


class CustomFileModelSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = CustomFileModel
        fields = ("id", "url", "folder", "name", "file", "created_by")


class CustomImageModelSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = CustomImageModel
        fields = ("id", "url", "folder", "name", "file", "created_by")


# ViewSets define the view behavior.
class UserFolderSerializerViewSet(viewsets.ModelViewSet):
    queryset = UserFolder.objects.all()
    serializer_class = UserFolderSerializer


class CustomFileModelSerializerViewSet(viewsets.ModelViewSet):
    queryset = CustomFileModel.objects.all()
    serializer_class = CustomFileModelSerializer


class CustomImageModelSerializerViewSet(viewsets.ModelViewSet):
    queryset = CustomImageModel.objects.all()
    serializer_class = CustomImageModelSerializer
