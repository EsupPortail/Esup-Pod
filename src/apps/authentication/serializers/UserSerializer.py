from rest_framework import serializers
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema_field

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model, enriched with Owner profile data.
    """
    affiliation = serializers.SerializerMethodField(method_name='get_affiliation')
    establishment = serializers.SerializerMethodField(method_name='get_establishment')
    userpicture = serializers.SerializerMethodField(method_name='get_userpicture')

    class Meta:
        model = User
        fields = [
            'id', 
            'username', 
            'email', 
            'first_name', 
            'last_name', 
            'is_staff', 
            'affiliation', 
            'establishment',
            'userpicture'
        ]

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_affiliation(self, obj) -> str | None:
        """Returns the user's affiliation from the Owner profile."""
        if hasattr(obj, 'owner'):
            return obj.owner.affiliation
        return None

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_establishment(self, obj) -> str | None:
        """Returns the user's establishment from the Owner profile."""
        if hasattr(obj, 'owner'):
            return obj.owner.establishment
        return None

    def get_userpicture(self, obj) -> str | None:
        if hasattr(obj, 'owner') and obj.owner.userpicture:
            return obj.owner.userpicture.image.url 
        return None