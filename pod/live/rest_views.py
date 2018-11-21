from .models import Building, Broadcaster
from rest_framework import serializers, viewsets

# Serializers define the API representation.


class BuildingSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Building
        fields = ('id', 'url', 'name', 'headband', 'gmapurl')


class BroadcasterSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Broadcaster
        fields = ('id', 'url', 'name',
                  'building', 'description', 'poster',
                  'url', 'status')

#############################################################################
# ViewSets define the view behavior.
#############################################################################


class BuildingViewSet(viewsets.ModelViewSet):
    queryset = Building.objects.all().order_by('name')
    serializer_class = BuildingSerializer


class BroadcasterViewSet(viewsets.ModelViewSet):
    queryset = Broadcaster.objects.all().order_by('building', 'name')
    serializer_class = BroadcasterSerializer
