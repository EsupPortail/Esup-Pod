from django.conf import settings as django_settings

USE_PEER_TO_PEER = getattr(django_settings, "USE_PEER_TO_PEER", True)

def context_settings(request):
    """Return all context settings for playlist app"""
    new_settings = {}
    new_settings["USE_PEER_TO_PEER"] = USE_PEER_TO_PEER
    return new_settings