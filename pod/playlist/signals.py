from os import name
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Playlist
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User


@receiver(post_save, sender=User)
def create_favorite_playlist(sender, instance, created, **kwargs):
    if created:
        Playlist.objects.create(
            name="Favorites",
            description=_("Your favorites videos."),
            visibility="private",
            autoplay=True,
            owner=instance
        )
