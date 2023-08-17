from django.contrib.sites.models import Site
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

from pod.authentication.models import Owner

from .apps import FAVORITE_PLAYLIST_NAME
from .models import Playlist


@receiver(m2m_changed, sender=Owner.sites.through)
def update_favorite_playlist(sender, instance, action, reverse, model, pk_set, **kwargs):
    if action == 'post_add':
        for site_id in pk_set:
            site = Site.objects.get(id=site_id)
            if not Playlist.objects.filter(name=FAVORITE_PLAYLIST_NAME, owner=instance.user, site=site).exists():
                Playlist.objects.create(
                    name=FAVORITE_PLAYLIST_NAME,
                    description=_("Your favorites videos."),
                    visibility="private",
                    autoplay=True,
                    owner=instance.user,
                    editable=False,
                    site=site,
                )
