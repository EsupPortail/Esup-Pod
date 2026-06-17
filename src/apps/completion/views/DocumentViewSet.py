"""
Esup-Pod - Document viewset.
"""

from rest_framework import viewsets, permissions, filters, parsers, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.http import FileResponse
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend

from src.apps.completion.models import Document
from src.apps.completion.serializers import DocumentSerializer
from src.apps.completion.permissions import CanManageDocument


class DocumentViewSet(viewsets.ModelViewSet):
    """
    API view set for the Document model.
    """

    queryset = Document.objects.all().select_related("video")
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageDocument]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ["video", "is_private"]
    ordering_fields = ["created_at", "title"]
    ordering = ["-created_at"]

    def perform_create(self, serializer):
        """Handle document creation with permission checks."""
        video = serializer.validated_data.get("video")
        user = self.request.user
        if video and not (
            user == video.owner
            or user.is_superuser
            or user in video.co_owners.all()
            or user.has_perm("completion.add_document_anywhere")
        ):
            raise PermissionDenied(
                _("You do not have permission to add a document to this video.")
            )
        serializer.save()

    def get_queryset(self):
        """
        Filter private documents: only owners, co-owners, and staff can see them.
        """
        user = self.request.user
        qs = super().get_queryset()

        if user.is_superuser:
            return qs

        if user.is_authenticated:
            # Can see public documents, AND documents of videos they own/co-own
            return qs.filter(
                Q(is_private=False) | Q(video__owner=user) | Q(video__co_owners=user)
            ).distinct()

        return qs.filter(is_private=False)

    @action(
        detail=True, methods=["get"], permission_classes=[permissions.IsAuthenticated]
    )
    def download(self, request, pk=None):
        """
        Secure download endpoint for the document.
        Checks permissions before serving the file.
        """
        document = self.get_object()

        # Check privacy
        if document.is_private:
            user = request.user
            if not (
                user.is_superuser
                or user == document.video.owner
                or user in document.video.co_owners.all()
            ):
                return Response(
                    {
                        "detail": _(
                            "You do not have permission to access this private document."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        if not document.file:
            return Response(
                {"detail": _("No file attached.")}, status=status.HTTP_404_NOT_FOUND
            )

        response = FileResponse(document.file)
        response["Content-Disposition"] = (
            f'attachment; filename="{document.file.name.split("/")[-1]}"'
        )
        return response
