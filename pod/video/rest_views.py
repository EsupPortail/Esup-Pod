from pod.video.models import Channel, Theme
from rest_framework import serializers, viewsets

# Serializers define the API representation.


class ChannelSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Channel
        fields = ('id', 'url', 'title', 'description',
                  'color', 'style', 'owners', 'users', 'visible', 'themes') #themes ?, headband


class ThemeSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Theme
        fields = (
            'url', 'parentId', 'title', 'description', 'channel')

# ViewSets define the view behavior.


class ChannelViewSet(viewsets.ModelViewSet):
    queryset = Channel.objects.all()
    serializer_class = ChannelSerializer


class ThemeViewSet(viewsets.ModelViewSet):
    queryset = Theme.objects.all()
    serializer_class = ThemeSerializer
