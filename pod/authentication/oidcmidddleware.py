
from authlib.integrations.django_client import OAuth
from django.conf import settings

OIDC_NAME = getattr(
  settings, 'OIDC_NAME', 'openid_connect')
OIDC_CONF_URL = getattr(
  settings, 'OIDC_CONF_URL', '')
OIDC_SCOPE = getattr(
  settings, 'OIDC_SCOPE', 'openid email profile')

oauth = OAuth()
oauth.register(
  name=OIDC_NAME,
  server_metadata_url=OIDC_CONF_URL,
  client_kwargs={
    'scope':OIDC_SCOPE
  }
)
