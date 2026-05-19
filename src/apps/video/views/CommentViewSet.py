"""
Esup-Pod - Comment views.
"""

from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter
from src.apps.video.models import Video, Comment, Vote
from src.apps.video.serializers import CommentSerializer


class CommentViewSet(viewsets.GenericViewSet):
    """
    ViewSet for video comments.
    Adapted from Pod V4 logic into the DRF-optimized hierarchical structure of V5.
    Provides endpoints for listing, adding, deleting, and voting on comments.
    """

    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @extend_schema(
        operation_id="comment_list",
        parameters=[
            OpenApiParameter("only", str, enum=["parents"]),
        ],
    )
    def list_comments(self, request, video_slug: str):
        """
        Retrieves comments for a specific video.
        GET /comment/<video_slug>/
        If ?only=parents is provided, only first-level comments are returned.
        Otherwise, all top-level comments are returned with their children embedded.
        """
        only_parents = request.query_params.get("only") == "parents"
        user_id = request.user.id if request.user.is_authenticated else None
        queryset = self.get_serializer_class().get_optimized_queryset(video_slug, user_id)
        queryset = queryset.filter(parent__isnull=True)
        serializer = self.get_serializer(
            queryset,
            many=True,
            context={"request": request, "only_parents": only_parents},
        )
        return Response(serializer.data)

    @extend_schema()
    def detail_comment(self, request, video_slug: str, comment_id: int):
        """
        Retrieves a specific comment and its nested children.
        GET /comment/<comment_id>/<video_slug>/
        """
        user_id = request.user.id if request.user.is_authenticated else None
        comment = get_object_or_404(
            self.get_serializer_class().get_optimized_queryset(video_slug, user_id),
            id=comment_id,
        )
        serializer = self.get_serializer(comment)
        return Response(serializer.data)

    @extend_schema(operation_id="comment_add", request=CommentSerializer)
    def add_comment(self, request, video_slug: str, comment_id: int = None):
        """
        Adds a new comment or a reply to a video.
        POST /comment/add/<video_slug>/
        POST /comment/add/<video_slug>/<comment_id>/
        """
        video = get_object_or_404(Video, slug=video_slug)
        content = request.data.get("content")
        if not content:
            return Response(
                {"error": "Comment content cannot be empty."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        parent = None
        direct_parent = None
        if comment_id:
            direct_parent = get_object_or_404(Comment, id=comment_id, video=video)
            parent = direct_parent.parent if direct_parent.parent else direct_parent
        comment = Comment.objects.create(
            author=request.user,
            content=content,
            video=video,
            parent=parent,
            direct_parent=direct_parent,
        )
        return Response(
            {
                "id": comment.id,
                "author_name": f"{comment.author.first_name} {comment.author.last_name}".strip()
                or comment.author.username,
                "added": comment.added,
            },
            status=status.HTTP_201_CREATED,
        )

    @extend_schema()
    def delete_comment(self, request, video_slug: str, comment_id: int):
        """
        Deletes a comment. Permission check: Author, Video Owner, or Superuser.
        POST /comment/del/<video_slug>/<comment_id>/
        """
        comment = get_object_or_404(Comment, id=comment_id, video__slug=video_slug)
        can_delete = (
            request.user == comment.author
            or request.user == comment.video.owner
            or request.user.is_superuser
        )
        if not can_delete:
            return Response(
                {"deleted": False, "error": "Insufficient permissions."},
                status=status.HTTP_403_FORBIDDEN,
            )
        comment.delete()
        return Response({"deleted": True})

    @extend_schema()
    def get_user_votes(self, request, video_slug: str):
        """
        Returns a list of IDs for comments the user has voted on for a specific video.
        GET /comment/vote/<video_slug>/
        """
        if not request.user.is_authenticated:
            return Response([])
        voted_ids = Vote.objects.filter(
            user=request.user, comment__video__slug=video_slug
        ).values_list("comment_id", flat=True)
        return Response(list(voted_ids))

    @extend_schema()
    def toggle_vote(self, request, video_slug: str, comment_id: int):
        """
        Toggles (adds/removes) a vote on a comment by the current user.
        POST /comment/vote/<video_slug>/<comment_id>/
        """
        if not request.user.is_authenticated:
            return Response(
                {"error": "Authentication required to vote."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        comment = get_object_or_404(Comment, id=comment_id, video__slug=video_slug)
        vote, created = Vote.objects.get_or_create(user=request.user, comment=comment)
        if not created:
            vote.delete()
            status_msg = "unvoted"
        else:
            status_msg = "voted"
        return Response(
            {"status": status_msg, "nbr_vote": comment.votes.count()},
            status=status.HTTP_200_OK,
        )
