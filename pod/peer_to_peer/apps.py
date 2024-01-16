from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PeerToPeerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pod.peer_to_peer'
    verbose_name = _("Peer to peer")
