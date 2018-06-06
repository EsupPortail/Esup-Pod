from django.contrib.auth.models import User, Group
from .models import AuthenticationImageModel, Owner
from rest_framework import serializers, viewsets

# Serializers define the API representation.


class OwnerSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Owner
        fields = ('id', 'url', 'user', 'auth_type',
                  'affiliation', 'commentaire', 'hashkey', 'userpicture')


class AuthenticationImageModelSerializer(
        serializers.HyperlinkedModelSerializer):

    class Meta:
        model = AuthenticationImageModel
        fields = ('id', 'url', 'file')


class UserSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = User
        fields = ('id', 'url', 'username', 'first_name',
                  'last_name', 'email', 'groups')


class GroupSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Group
        fields = ('url', 'name')

# ViewSets define the view behavior.


class OwnerViewSet(viewsets.ModelViewSet):
    queryset = Owner.objects.all().order_by('-user')
    serializer_class = OwnerSerializer


class AuthenticationImageModelViewSet(viewsets.ModelViewSet):
    queryset = AuthenticationImageModel.objects.all()
    serializer_class = AuthenticationImageModelSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
