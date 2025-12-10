from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

class OIDCTokenObtainSerializer(serializers.Serializer):
    """
    Sérialiseur pour l'échange de code OIDC.
    Le frontend renvoie le 'code' reçu après redirection.
    """
    code = serializers.CharField(required=True)
    redirect_uri = serializers.CharField(required=True, help_text="L'URI de redirection utilisée lors de la demande initiale.")

class ShibbolethTokenObtainSerializer(serializers.Serializer):
    """
    Sérialiseur vide car Shibboleth utilise les headers HTTP.
    Sert principalement à la documentation API (Swagger).
    """
    pass