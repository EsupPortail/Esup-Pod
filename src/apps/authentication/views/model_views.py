"""
Esup-Pod - Model viewsets for the authentication app.

This module provides standard ViewSets for User, Group, Site, Owner,
and AccessGroup models.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.sites.models import Site
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiResponse,
)
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
from ..permissions import IsSuperUser
from ..services import AccessGroupService
from django_filters.rest_framework import DjangoFilterBackend
from ..filters import UserFilterSet, AccessGroupFilterSet

User = get_user_model()


class UserMeView(APIView):
    """
    **Current User Profile**
    Returns the profile information of the currently authenticated user.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Retrieve authenticated user profile",
        responses={200: UserSerializer},
    )
    def get(self, request):
        """Returns the profile information, including username, email, full name, affiliation, and establishment of the currently authenticated user."""
        serializer = UserSerializer(request.user)
        data = serializer.data
        if hasattr(request.user, "owner"):
            data["affiliation"] = request.user.owner.affiliation
            data["establishment"] = request.user.owner.establishment

        return Response(data, status=status.HTTP_200_OK)


@extend_schema_view(
    list=extend_schema(
        summary="List user owner profiles",
        description="Retrieve a list of user profiles (Owner models) containing additional metadata such as affiliation, establishment, and profile picture. Restricted to superusers.",
    ),
    retrieve=extend_schema(
        summary="Retrieve owner profile details",
        description="Retrieve details of a specific Owner profile. Restricted to superusers.",
    ),
    create=extend_schema(
        summary="Create an owner profile",
        description="Add a new Owner profile. Restricted to superusers.",
    ),
    update=extend_schema(
        summary="Update an owner profile",
        description="Fully update an existing Owner profile. Restricted to superusers.",
    ),
    partial_update=extend_schema(
        summary="Partially update an owner profile",
        description="Partially update an existing Owner profile. Restricted to superusers.",
    ),
    destroy=extend_schema(
        summary="Delete an owner profile",
        description="Delete an Owner profile. Restricted to superusers.",
    ),
)
class OwnerViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Owner profiles.
    Includes actions to manage access groups for a user.
    """

    queryset = Owner.objects.all().order_by("-user")
    serializer_class = OwnerSerializer
    permission_classes = [IsSuperUser]

    @extend_schema(
        summary="Assign access groups to user",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "The unique username of the user.",
                    },
                    "groups": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of access group code names to assign.",
                    },
                },
                "required": ["username", "groups"],
            }
        },
        responses={
            200: OwnerWithGroupsSerializer,
            400: OpenApiResponse(description="Missing username or groups."),
            404: OpenApiResponse(description="User not found."),
        },
    )
    @action(detail=False, methods=["post"], url_path="set-user-accessgroup")
    def set_user_accessgroup(self, request):
        """
        Assigns access groups to a user based on their username. Restricted to superusers.
        Equivalent of accessgroups_set_user_accessgroup.
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

    @extend_schema(
        summary="Remove access groups from user",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "The unique username of the user.",
                    },
                    "groups": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of access group code names to remove.",
                    },
                },
                "required": ["username", "groups"],
            }
        },
        responses={
            200: OwnerWithGroupsSerializer,
            400: OpenApiResponse(description="Missing username or groups."),
            404: OpenApiResponse(description="User not found."),
        },
    )
    @action(detail=False, methods=["post"], url_path="remove-user-accessgroup")
    def remove_user_accessgroup(self, request):
        """
        Removes access groups from a user based on their username. Restricted to superusers.
        Equivalent of accessgroups_remove_user_accessgroup.
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

    @extend_schema(
        summary="Update profile picture",
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "picture": {
                        "type": "string",
                        "format": "binary",
                        "description": "Image file to upload.",
                    }
                },
            }
        },
        responses={
            200: OpenApiResponse(
                description="Profile picture updated successfully.",
                response={
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "example": "success"},
                        "message": {
                            "type": "string",
                            "example": "Profile picture updated.",
                        },
                        "userpicture": {"type": "string", "format": "uri"},
                    },
                },
            ),
            204: OpenApiResponse(description="Profile picture deleted successfully."),
            400: OpenApiResponse(description="No picture file provided."),
            403: OpenApiResponse(
                description="Forbidden - cannot modify another user's picture."
            ),
        },
    )
    @action(
        detail=True,
        methods=["post", "patch", "delete"],
        url_path="picture",
        permission_classes=[IsAuthenticated],
    )
    def update_picture(self, request, pk=None):
        """
        Uploads and assigns an image as the user's profile picture, or deletes it if a DELETE request is made.
        """
        owner = self.get_object()

        if not request.user.is_superuser and owner.user != request.user:
            return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

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


@extend_schema_view(
    list=extend_schema(
        summary="List users",
        description="Retrieve a list of standard Django Users. Regular users can only see their own profile, whereas superusers can see all users. Supports multi-value filtering (e.g., `?username=A&username=B` or `?email=A&email=B`).",
    ),
    retrieve=extend_schema(
        summary="Retrieve user details",
        description="Retrieve details of a specific user by their ID. Regular users can only retrieve their own user record.",
    ),
    create=extend_schema(summary="Create a user", description="Register a new user."),
    update=extend_schema(
        summary="Update a user",
        description="Fully update a user profile. Regular users can only update their own profile.",
    ),
    partial_update=extend_schema(
        summary="Partially update a user",
        description="Partially update a user profile. Regular users can only update their own profile.",
    ),
    destroy=extend_schema(
        summary="Delete a user", description="Permanently delete a user account."
    ),
)
class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing standard Django Users.
    """

    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserSerializer
    filterset_class = UserFilterSet
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ["username", "first_name", "last_name", "email"]

    def get_queryset(self):
        """Restrict users from seeing profiles other than their own unless they are superusers."""
        if not self.request.user.is_superuser:
            return User.objects.filter(pk=self.request.user.pk)
        return super().get_queryset()


@extend_schema_view(
    list=extend_schema(
        summary="List user permission groups",
        description="Retrieve a list of standard Django groups. Restricted to superusers.",
    ),
    retrieve=extend_schema(
        summary="Retrieve permission group",
        description="Retrieve details of a specific group by ID. Restricted to superusers.",
    ),
    create=extend_schema(
        summary="Create a permission group",
        description="Create a new Django group. Restricted to superusers.",
    ),
    update=extend_schema(
        summary="Update a permission group",
        description="Fully update a Django group. Restricted to superusers.",
    ),
    partial_update=extend_schema(
        summary="Partially update a permission group",
        description="Partially update a Django group. Restricted to superusers.",
    ),
    destroy=extend_schema(
        summary="Delete a permission group",
        description="Delete a Django group. Restricted to superusers.",
    ),
)
class GroupViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Django Groups (Permissions).
    """

    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [IsSuperUser]


@extend_schema_view(
    list=extend_schema(
        summary="List multi-site domains",
        description="Retrieve a list of all sites/domains configured in this multi-tenant installation. Restricted to superusers.",
    ),
    retrieve=extend_schema(
        summary="Retrieve site domain details",
        description="Retrieve details of a specific site domain by ID. Restricted to superusers.",
    ),
    create=extend_schema(
        summary="Create a site domain",
        description="Add a new site/domain. Restricted to superusers.",
    ),
    update=extend_schema(
        summary="Update a site domain",
        description="Fully update a site domain. Restricted to superusers.",
    ),
    partial_update=extend_schema(
        summary="Partially update a site domain",
        description="Partially update a site domain. Restricted to superusers.",
    ),
    destroy=extend_schema(
        summary="Delete a site domain",
        description="Delete a site domain. Restricted to superusers.",
    ),
)
class SiteViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Sites.
    """

    queryset = Site.objects.all()
    serializer_class = SiteSerializer
    permission_classes = [IsSuperUser]


@extend_schema_view(
    list=extend_schema(
        summary="List access groups",
        description="Retrieve a list of all LDAP or local access groups configured for the system. Restricted to superusers. Supports multi-value filtering (e.g., `?code_name=A&code_name=B`).",
    ),
    retrieve=extend_schema(
        summary="Retrieve access group",
        description="Retrieve detailed information about a specific access group. Restricted to superusers.",
    ),
    create=extend_schema(
        summary="Create an access group",
        description="Create a new access group. Restricted to superusers.",
    ),
    update=extend_schema(
        summary="Update an access group",
        description="Fully update an access group. Restricted to superusers.",
    ),
    partial_update=extend_schema(
        summary="Partially update an access group",
        description="Partially update an access group. Restricted to superusers.",
    ),
    destroy=extend_schema(
        summary="Delete an access group",
        description="Delete an access group. Restricted to superusers.",
    ),
)
class AccessGroupViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Access Groups.
    Includes actions to add/remove users by code name.
    """

    queryset = AccessGroup.objects.all()
    serializer_class = AccessGroupSerializer
    filterset_class = AccessGroupFilterSet
    permission_classes = [IsSuperUser]
    filter_backends = [DjangoFilterBackend]

    @extend_schema(
        summary="Set users of an access group",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "code_name": {
                        "type": "string",
                        "description": "The unique code name of the access group.",
                    },
                    "users": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Array of usernames to assign as sole members of this access group.",
                    },
                },
                "required": ["code_name", "users"],
            }
        },
        responses={
            200: AccessGroupSerializer,
            400: OpenApiResponse(description="Missing code_name or users."),
            404: OpenApiResponse(description="AccessGroup not found."),
        },
    )
    @action(detail=False, methods=["post"], url_path="set-users-by-name")
    def set_users_by_name(self, request):
        """
        Replaces/assigns the list of users belonging to an access group by their usernames. Restricted to superusers.
        Equivalent of accessgroups_set_users_by_name.
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

    @extend_schema(
        summary="Remove users from an access group",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "code_name": {
                        "type": "string",
                        "description": "The unique code name of the access group.",
                    },
                    "users": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Array of usernames to remove from the access group.",
                    },
                },
                "required": ["code_name", "users"],
            }
        },
        responses={
            200: AccessGroupSerializer,
            400: OpenApiResponse(description="Missing code_name or users."),
            404: OpenApiResponse(description="AccessGroup not found."),
        },
    )
    @action(detail=False, methods=["post"], url_path="remove-users-by-name")
    def remove_users_by_name(self, request):
        """
        Removes a list of users (by their usernames) from an access group (by its code_name). Restricted to superusers.
        Equivalent of accessgroups_remove_users_by_name.
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
