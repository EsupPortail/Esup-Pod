from pod.filepicker.models import CustomImageModel, UserDirectory
from pod.filepicker.models import CustomFileModel
from rest_framework import serializers, viewsets

# Serializers define the API representation.


class UserDirectorySerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = UserDirectory
        fields = ('id', 'url', 'name', 'parent', 'owner')


class CustomFileModelSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = CustomFileModel
        fields = ('id', 'url', 'directory', 'name', 'file', 'created_by')


class CustomImageModelSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = CustomImageModel
        fields = ('id', 'url', 'directory', 'name', 'file', 'created_by')


# ViewSets define the view behavior.
class UserDirectorySerializerViewSet(viewsets.ModelViewSet):
    queryset = UserDirectory.objects.all()
    serializer_class = UserDirectorySerializer


class CustomFileModelSerializerViewSet(viewsets.ModelViewSet):
    queryset = CustomFileModel.objects.all()
    serializer_class = CustomFileModelSerializer


class CustomImageModelSerializerViewSet(viewsets.ModelViewSet):
    queryset = CustomImageModel.objects.all()
    serializer_class = CustomImageModelSerializer
