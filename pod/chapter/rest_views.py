from pod.chapter.models import Chapter
from rest_framework import serializers, viewsets

# Serializers define the API representation.


class ChapterSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Chapter
        fields = ("id", "url", "video", "title", "time_start")


#############################################################################
# ViewSets define the view behavior.
#############################################################################


class ChapterViewSet(viewsets.ModelViewSet):
    queryset = Chapter.objects.all().order_by("video", "time_start")
    serializer_class = ChapterSerializer
