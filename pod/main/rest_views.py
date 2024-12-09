from rest_framework import serializers, viewsets
from .models import CustomImageModel

# from .models import CustomFileModel


class CustomImageModelSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = CustomImageModel
        fields = ("id", "url", "file")


"""
class CustomFileModelSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = CustomFileModel
        fields = ("id", "url", "file")
"""


class CustomImageModelViewSet(viewsets.ModelViewSet):
    queryset = CustomImageModel.objects.all()
    serializer_class = CustomImageModelSerializer


"""
class CustomFileModelViewSet(viewsets.ModelViewSet):
    queryset = CustomFileModel.objects.all()
    serializer_class = CustomFileModelSerializer
"""
