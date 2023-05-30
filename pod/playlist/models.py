from django.db import models
from django.utils.translation import ugettext as _


class Playlist(models.Model):
    VISIBILITY_CHOICES = [
        ("public", _("Public")),
        ("protected", _("Protected")),
        ("private", _("Private")),
    ]
    name = models.CharField(
        verbose_name=_("Name"),
        max_length=250,
        help_text=_("Please choose a name between 1 and 250 characters."),
    )
    description = models.TextField(
        verbose_name=_("Description"),
        blank=True,
        default="",
        help_text=_("Please choose a description. This description is empty by default."),
    )
    password = models.TextField(verbose_name=_("Password"))
    visibility = models.CharField(
        verbose_name=_("Visibility"),
        choices=VISIBILITY_CHOICES,
        help_text=_("Please chosse an visibility among 'public', 'protected', 'private'."),
    )
    autoplay = models.BooleanField(
        verbose_name=_("Autoplay"),
        default=True,
        help_text=_("Please choose if this playlist is an autoplay playlist or not."),
    )
    slug = models.SlugField(
        _("slug"),
        unique=True,
        max_length=105,
        help_text=_(
            'Used to access this instance, the "slug" is a short'
            + " label containing only letters, numbers, underscore"
            + " or dash top."
        ),
        editable=False,
    )

class PlaylistContent(models.Model):
    ...
