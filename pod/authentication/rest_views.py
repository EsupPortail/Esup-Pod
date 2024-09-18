from django.contrib.auth.models import User, Group
from django.contrib.sites.models import Site
from .models import Owner, AccessGroup
from rest_framework import serializers, viewsets
from rest_framework.decorators import api_view
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse

# Serializers define the API representation.


class OwnerSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Owner
        fields = (
            "id",
            "url",
            "user",
            "auth_type",
            "affiliation",
            "commentaire",
            "hashkey",
            "userpicture",
            "sites",
        )


class OwnerWithGroupsSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Owner
        fields = (
            "id",
            "url",
            "user",
            "auth_type",
            "affiliation",
            "commentaire",
            "hashkey",
            "userpicture",
            "accessgroup_set",
        )


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "url",
            "username",
            "first_name",
            "is_staff",
            "last_name",
            "email",
            "groups",
        )
        filterset_fields = ["id", "username", "email"]


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ("url", "name")


class SiteSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Site
        fields = ("url", "name", "domain")


class AccessGroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = AccessGroup
        fields = ("display_name", "code_name", "sites", "users", "sites")


# ViewSets define the view behavior.


class OwnerViewSet(viewsets.ModelViewSet):
    queryset = Owner.objects.all().order_by("-user")
    serializer_class = OwnerSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserSerializer
    filterset_fields = ["id", "username", "email"]


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class SiteViewSet(viewsets.ModelViewSet):
    queryset = Site.objects.all()
    serializer_class = SiteSerializer


class AccessGroupViewSet(viewsets.ModelViewSet):
    queryset = AccessGroup.objects.all()
    serializer_class = AccessGroupSerializer


@api_view(["POST"])
def accessgroups_set_users_by_name(request):
    if ("users" in request.data) and ("code_name" in request.data):
        code_name = request.data["code_name"]
        users = request.data["users"]
        accessgroup = get_object_or_404(AccessGroup, code_name=code_name)
        for user in users:
            try:
                owner = Owner.objects.get(user__username=user)
                accessgroup.users.add(owner)
            except ObjectDoesNotExist:
                pass
        return Response(
            AccessGroupSerializer(instance=accessgroup, context={"request": request}).data
        )
    else:
        return HttpResponse(status=500)


@api_view(["POST"])
def accessgroups_remove_users_by_name(request):
    if ("users" in request.data) and ("code_name" in request.data):
        code_name = request.data["code_name"]
        users = request.data["users"]
        accessgroup = get_object_or_404(AccessGroup, code_name=code_name)
        for user in users:
            try:
                owner = Owner.objects.get(user__username=user)
                if owner in accessgroup.users.all():
                    accessgroup.users.remove(owner)
            except ObjectDoesNotExist:
                pass
        return Response(
            AccessGroupSerializer(instance=accessgroup, context={"request": request}).data
        )
    else:
        return HttpResponse(status=500)


@api_view(["POST"])
def accessgroups_set_user_accessgroup(request):
    if ("username" in request.data) and ("groups" in request.data):
        username = request.data["username"]
        groups = request.data["groups"]
        owner = get_object_or_404(Owner, user__username=username)
        for group in groups:
            try:
                accessgroup = AccessGroup.objects.get(code_name=group)
                owner.accessgroup_set.add(accessgroup)
            except ObjectDoesNotExist:
                pass
        return Response(
            OwnerWithGroupsSerializer(instance=owner, context={"request": request}).data
        )
    else:
        return HttpResponse(status=500)


@api_view(["POST"])
def accessgroups_remove_user_accessgroup(request):
    if ("username" in request.data) and ("groups" in request.data):
        username = request.data["username"]
        groups = request.data["groups"]
        owner = get_object_or_404(Owner, user__username=username)
        for group in groups:
            try:
                accessgroup = AccessGroup.objects.get(code_name=group)
                if accessgroup in owner.accessgroup_set.all():
                    owner.accessgroup_set.remove(accessgroup)
            except ObjectDoesNotExist:
                pass
        return Response(
            OwnerWithGroupsSerializer(instance=owner, context={"request": request}).data
        )
    else:
        return HttpResponse(status=500)
