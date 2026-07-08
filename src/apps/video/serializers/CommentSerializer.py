"""
Esup-Pod - Comment serializer.
"""

from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from django.db.models import Count, Case, When, Value, BooleanField, F
from django.db.models.functions import Concat
from src.apps.video.models import Comment


class CommentSerializer(serializers.ModelSerializer):
    """
    Serializer for the Comment model.
    Optimized for lists, including children and vote counts.
    """

    author_name = serializers.CharField(read_only=True)
    author_username = serializers.CharField(source="author.username", read_only=True)
    author_picture = serializers.SerializerMethodField()
    nbr_vote = serializers.IntegerField(read_only=True)
    is_owner = serializers.BooleanField(read_only=True)
    children = serializers.SerializerMethodField()

    class Meta:
        """Comment serializer metadata."""

        model = Comment
        fields = [
            "id",
            "parent",
            "direct_parent",
            "author",
            "author_name",
            "author_username",
            "author_picture",
            "content",
            "video",
            "added",
            "nbr_vote",
            "is_owner",
            "children",
        ]
        read_only_fields = [
            "author",
            "author_name",
            "author_username",
            "author_picture",
            "added",
            "nbr_vote",
            "is_owner",
            "children",
        ]

    @extend_schema_field(serializers.ListSerializer(child=serializers.DictField()))
    def get_children(self, obj):
        """
        Retrieves children if the current context specifies it.
        Uses the optimized model method.
        """
        request = self.context.get("request")
        if self.context.get("only_parents"):
            return []
        user_id = request.user.id if request and request.user.is_authenticated else None
        if obj.parent_id is None:
            return obj.get_json_children(user_id)
        return []

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_author_picture(self, obj):
        """
        Retrieves the profile picture URL of the comment's author.
        """
        if (
            obj.author
            and hasattr(obj.author, "owner")
            and obj.author.owner
            and obj.author.owner.userpicture
        ):
            try:
                return obj.author.owner.userpicture.url
            except ValueError:
                pass
        return None

    @classmethod
    def get_optimized_queryset(cls, video_slug, user_id=None):
        """
        Helper to get an optimized queryset with all necessary annotations.
        """
        return (
            Comment.objects.filter(video__slug=video_slug)
            .annotate(nbr_vote=Count("votes", distinct=True))
            .annotate(
                author_name=Concat("author__last_name", Value(" "), "author__first_name")
            )
            .annotate(author_username=F("author__username"))
            .annotate(
                is_owner=Case(
                    When(author__id=user_id, then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField(),
                )
            )
            .select_related("author", "author__owner", "video")
        )
