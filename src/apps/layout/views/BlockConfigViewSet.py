"""
Esup-Pod - BlockConfig ViewSet.
"""

from rest_framework import viewsets, permissions
from drf_spectacular.utils import extend_schema, extend_schema_view
from src.apps.layout.models import BlockConfig
from src.apps.layout.serializers import BlockConfigSerializer
from src.apps.layout.conf import layout_settings


@extend_schema_view(
    list=extend_schema(
        tags=["Layout Blocks"],
        summary="List all block configurations",
        description=(
            "Retrieve the list of all block configurations defined by the administration. "
            "The frontend should call this endpoint upon initialization to configure its layout components."
        ),
        responses={200: BlockConfigSerializer(many=True)},
    ),
    retrieve=extend_schema(
        tags=["Layout Blocks"],
        summary="Retrieve a specific block configuration",
        description="Retrieve the personalization settings for a specific block using its `frontend_id`.",
        responses={200: BlockConfigSerializer},
    ),
)
class BlockConfigViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet to read and expose the layout configuration blocks.

    These blocks are typically managed in the Django admin and consumed by the frontend
    to dynamically build the UI components (like the homepage layout).
    """

    permission_classes = [permissions.AllowAny]
    serializer_class = BlockConfigSerializer
    lookup_field = "frontend_id"

    def get_queryset(self):
        """
        Return block configurations if enabled in settings, otherwise return an empty queryset.

        Returns:
            QuerySet[BlockConfig]: Filtered queryset of BlockConfig instances ordered by frontend_id.
        """
        if not layout_settings.use_layout_blocks:
            return BlockConfig.objects.none()
        return BlockConfig.objects.all().order_by("frontend_id")
