from rest_framework.response import Response
from rest_framework import viewsets, permissions, parsers, filters
from django.db.models import Q
from src.apps.video.models import Video
from src.apps.video.serializers import VideoSerializer
from src.apps.video.permissions import IsOwnerOrCoOwnerOrReadOnly
from django.http import FileResponse, Http404
from rest_framework.decorators import action
import os
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth.hashers import check_password


class VideoViewSet(viewsets.ModelViewSet):
    serializer_class = VideoSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrCoOwnerOrReadOnly]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]
    lookup_field = "slug"
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title", "description", "owner__username"]
    ordering_fields = ["created_at", "title"]
    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user
        qs = Video.objects.all()
        if not user.is_authenticated:
            return qs.filter(status=Video.Status.PUBLISHED)
        if user.is_superuser:
            return qs
        return qs.filter(
            Q(status=Video.Status.PUBLISHED)
            | Q(status=Video.Status.RESTRICTED)
            | Q(owner=user)
            | Q(co_owners=user)
        ).distinct()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user, status=Video.Status.ENCODING)

    @action(detail=True, methods=["get"])
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
        file = open(path, "rb")
        response = FileResponse(file)
        response["Content-Type"] = "video/mp4"
        return response

    @action(detail=True, methods=['post'])
    def register_view(self, request, slug=None):
        video = self.get_object()
        video.view_count += 1
        video.save(update_fields=['view_count'])
        return Response({'status': 'viewed', 'count': video.view_count})

    @action(detail=True, methods=['post'], permission_classes=[permissions.AllowAny])
    def unlock(self, request, slug=None):
        """
        Permet de récupérer l'URL d'une vidéo protégée par mot de passe.
        Payload: { "password": "str" }
        """
        video = self.get_object()
        if video.status == Video.Status.RESTRICTED and not request.user.is_authenticated:
            raise PermissionDenied("Vous devez être connecté pour accéder à cette vidéo.")
        input_password = request.data.get('password')
        if video.password and check_password(input_password, video.password):
            request = self.context.get('request')
            url = request.build_absolute_uri(video.video_file.url) if video.video_file else None
            return Response({'video_url': url})
        return Response({'error': 'Mot de passe incorrect'}, status=403)
