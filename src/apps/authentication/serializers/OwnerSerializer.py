from rest_framework import serializers
from django.contrib.auth import get_user_model
from ..models.Owner import Owner

User = get_user_model()

class OwnerSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    
    class Meta:
        model = Owner
        fields = (
            "id",
            "user",
            "auth_type",
            "affiliation",
            "commentaire",
            "hashkey",
            "userpicture",
            "sites",
        )

class OwnerWithGroupsSerializer(serializers.ModelSerializer):
    """
    Serializer spécifique incluant les groupes d'accès (AccessGroups).
    Utilisé notamment lors de la modification des permissions d'un utilisateur.
    """
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Owner
        fields = (
            "id",
            "user",
            "auth_type",
            "affiliation",
            "commentaire",
            "hashkey",
            "userpicture",
            "accessgroups",
        )