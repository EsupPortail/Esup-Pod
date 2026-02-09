from rest_framework import viewsets, permissions, parsers, filters
from django.db.models import Q
from src.apps.video.models import Video
from src.apps.video.serializers import VideoSerializer
from src.apps.video.permissions import IsOwnerOrReadOnly
from django.http import FileResponse, Http404
from rest_framework.decorators import action
import os


class VideoViewSet(viewsets.ModelViewSet):
    serializer_class = VideoSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]
    lookup_field = 'slug'
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'owner__username']
    ordering_fields = ['created_at', 'title']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        qs = Video.objects.all()
        if not user.is_authenticated:
            return qs.filter(status=Video.Status.PUBLISHED)
        if user.is_superuser:
            return qs
        return qs.filter(
            Q(status=Video.Status.PUBLISHED) | Q(status=Video.Status.RESTRICTED) | Q(owner=user)
        ).distinct()

    def perform_create(self, serializer):
        serializer.save(
            owner=self.request.user,
            status=Video.Status.ENCODING
        )


@action(detail=True, methods=['get'])
def stream(self, request, slug=None):
    """
    Endpoint spécifique pour la lecture vidéo.
    URL: /api/videos/<slug>/stream/
    """
    video = self.get_object()
    if not video.video_file:
        raise Http404("Video file not found")
    path = video.video_file.path
    if not os.path.exists(path):
        raise Http404("Video file not found on disk")
    file = open(path, 'rb')
    response = FileResponse(file)
    response['Content-Type'] = 'video/mp4'
    return response
