from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User

from .apps import FAVORITE_PLAYLIST_NAME
from .models import Playlist


@receiver(post_save, sender=User)
def create_favorite_playlist(sender, instance, created, **kwargs):
    """
    Function to create the `Favorites` playlist when a user is created.

    Args:
        sender (:class:`django.contrib.auth.models.User`): The User class that sends the signal.
        instance (:class:`django.contrib.auth.models.User`): The instance of user that has been created
        created (bool): Indicates if the user was created or not.
    """
    if created:
        Playlist.objects.create(
            name=FAVORITE_PLAYLIST_NAME,
            description=_("Your favorites videos."),
            visibility="private",
            autoplay=True,
            owner=instance,
            editable=False
        )
