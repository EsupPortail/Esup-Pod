from django.contrib.auth.models import User, Group
from django.contrib.sites.models import Site
from .models import Owner
from rest_framework import serializers, viewsets

# Serializers define the API representation.


class OwnerSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Owner
        fields = ('id', 'url', 'user', 'auth_type',
                  'affiliation', 'commentaire', 'hashkey', 'userpicture')


class UserSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = User
        fields = ('id', 'url', 'username', 'first_name', 'is_staff',
                  'last_name', 'email', 'groups')


class GroupSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Group
        fields = ('url', 'name')


class SiteSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Site
        fields = ('url', 'name', 'domain')

# ViewSets define the view behavior.


class OwnerViewSet(viewsets.ModelViewSet):
    queryset = Owner.objects.all().order_by('-user')
    serializer_class = OwnerSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class SiteViewSet(viewsets.ModelViewSet):
    queryset = Site.objects.all()
    serializer_class = SiteSerializer
