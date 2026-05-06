"""
Esup-Pod - Model viewsets for the authentication app.

This module provides standard ViewSets for User, Group, Site, Owner,
and AccessGroup models.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.sites.models import Site
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models.AccessGroup import AccessGroup
from ..models.Owner import Owner
from ..serializers.AccessGroupSerializer import AccessGroupSerializer
from ..serializers.GroupSerializer import GroupSerializer
from ..serializers.OwnerSerializer import OwnerSerializer, OwnerWithGroupsSerializer
from ..serializers.SiteSerializer import SiteSerializer
from ..serializers.UserSerializer import UserSerializer
from ..services import AccessGroupService

User = get_user_model()


class UserMeView(APIView):
    """
    **Current User Profile**
    Returns the profile information of the currently authenticated user.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(responses=UserSerializer)
    def get(self, request):
        """Returns the profile of the current authenticated user."""
        serializer = UserSerializer(request.user)
        data = serializer.data
        if hasattr(request.user, "owner"):
            data["affiliation"] = request.user.owner.affiliation
            data["establishment"] = request.user.owner.establishment

        return Response(data, status=status.HTTP_200_OK)


class OwnerViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Owner profiles.
    Includes actions to manage access groups for a user.
    """

    queryset = Owner.objects.all().order_by("-user")
    serializer_class = OwnerSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["post"], url_path="set-user-accessgroup")
    def set_user_accessgroup(self, request):
        """
        Equivalent of accessgroups_set_user_accessgroup.
        Assigns AccessGroups to a user via their username.
        """
        username = request.data.get("username")
        groups = request.data.get("groups")

        if not username or groups is None:
            return Response(
                {"error": "Missing username or groups"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            owner = AccessGroupService.set_user_accessgroup(username, groups)
            serializer = OwnerWithGroupsSerializer(
                instance=owner, context={"request": request}
            )
            return Response(serializer.data)
        except Owner.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=["post"], url_path="remove-user-accessgroup")
    def remove_user_accessgroup(self, request):
        """
        Equivalent of accessgroups_remove_user_accessgroup.
        Removes AccessGroups from a user via their username.
        """
        username = request.data.get("username")
        groups = request.data.get("groups")

        if not username or groups is None:
            return Response(
                {"error": "Missing username or groups"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            owner = AccessGroupService.remove_user_accessgroup(username, groups)
            serializer = OwnerWithGroupsSerializer(
                instance=owner, context={"request": request}
            )
            return Response(serializer.data)
        except Owner.DoesNotExist:
            return Response(
                {"error": _("User not found")}, status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=["post", "patch", "delete"], url_path="picture")
    def update_picture(self, request, pk=None):
        """
        Uploads and assigns an image as the user's profile picture, or deletes it.
        """
        owner = self.get_object()

        if request.method == "DELETE":
            if owner.userpicture:
                owner.userpicture.delete(save=False)
                owner.userpicture = None
                owner.save(update_fields=["userpicture"])
            return Response(
                {"status": "success", "message": _("Profile picture deleted.")},
                status=status.HTTP_204_NO_CONTENT,
            )

        file = request.FILES.get("picture")

        if not file:
            return Response(
                {"error": _("No picture file provided in the request.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if owner.userpicture:
            owner.userpicture.delete(save=False)

        owner.userpicture = file
        owner.save()

        return Response(
            {
                "status": "success",
                "message": _("Profile picture updated."),
                "userpicture": request.build_absolute_uri(owner.userpicture.url),
            },
            status=status.HTTP_200_OK,
        )


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing standard Django Users.
    """

    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserSerializer
    filterset_fields = ["id", "username", "email"]
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ["username", "first_name", "last_name", "email"]


class GroupViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Django Groups (Permissions).
    """

    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated]


class SiteViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Sites.
    """

    queryset = Site.objects.all()
    serializer_class = SiteSerializer
    permission_classes = [IsAuthenticated]


class AccessGroupViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Access Groups.
    Includes actions to add/remove users by code name.
    """

    queryset = AccessGroup.objects.all()
    serializer_class = AccessGroupSerializer
    filterset_fields = ["id", "display_name", "code_name"]
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["post"], url_path="set-users-by-name")
    def set_users_by_name(self, request):
        """
        Equivalent of accessgroups_set_users_by_name.
        Adds a list of users (by username) to an AccessGroup (by code_name).
        """
        code_name = request.data.get("code_name")
        users = request.data.get("users")

        if not code_name or users is None:
            return Response(
                {"error": "Missing code_name or users"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            accessgroup = AccessGroupService.set_users_by_name(code_name, users)
            return Response(
                AccessGroupSerializer(
                    instance=accessgroup, context={"request": request}
                ).data
            )
        except AccessGroup.DoesNotExist:
            return Response(
                {"error": "AccessGroup not found"}, status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=["post"], url_path="remove-users-by-name")
    def remove_users_by_name(self, request):
        """
        Equivalent of accessgroups_remove_users_by_name.
        Removes a list of users (by username) from an AccessGroup (by code_name).
        """
        code_name = request.data.get("code_name")
        users = request.data.get("users")
        if not code_name or users is None:
            return Response(
                {"error": "Missing code_name or users"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            accessgroup = AccessGroupService.remove_users_by_name(code_name, users)
            return Response(
                AccessGroupSerializer(
                    instance=accessgroup, context={"request": request}
                ).data
            )
        except AccessGroup.DoesNotExist:
            return Response(
                {"error": "AccessGroup not found"}, status=status.HTTP_404_NOT_FOUND
            )
