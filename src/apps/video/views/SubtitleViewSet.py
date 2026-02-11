from rest_framework import viewsets, permissions, parsers
from rest_framework.exceptions import PermissionDenied
from src.apps.video.models import Subtitle
from src.apps.video.serializers import SubtitleSerializer


class IsSubtitleVideoOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission personnalisée :
    - Lecture : Autorisée pour tout le monde (ou selon la config globale).
    - Écriture/Suppression : Autorisée uniquement si l'utilisateur est le propriétaire de la vidéo liée.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.video.owner == request.user


class SubtitleViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour gérer les sous-titres (upload, listing, suppression).
    """

    queryset = Subtitle.objects.all()
    serializer_class = SubtitleSerializer
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly,
        IsSubtitleVideoOwnerOrReadOnly,
    ]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def get_queryset(self):
        """
        Permet de filtrer les sous-titres par vidéo.
        Usage: /api/subtitles/?video_id=12
        """
        queryset = super().get_queryset()
        video_id = self.request.query_params.get("video_id")
        if video_id:
            queryset = queryset.filter(video_id=video_id)
        return queryset

    def perform_create(self, serializer):
        """
        Vérification de sécurité au moment de la création.
        """
        video = serializer.validated_data.get("video")
        if (
            video
            and video.owner != self.request.user
            and not self.request.user.is_superuser
        ):
            raise PermissionDenied(
                "Vous ne pouvez pas ajouter de sous-titres à une vidéo qui ne vous appartient pas."
            )
        serializer.save()
