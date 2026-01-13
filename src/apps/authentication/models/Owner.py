import logging
import hashlib

from django.dispatch import receiver
from django.db import models
from django.contrib.auth.models import User, Permission
from django.contrib.sites.models import Site
from django.db.models.signals import post_save
from django.utils.translation import gettext_lazy as _

from src.apps.utils.models.CustomImageModel import CustomImageModel
from .utils import (
    AUTH_TYPE,
    AFFILIATION,
    DEFAULT_AFFILIATION,
    ESTABLISHMENTS,
    HIDE_USERNAME,
    SECRET_KEY,
)

logger = logging.getLogger(__name__)


class Owner(models.Model):
    """
    Extends the default Django User model to add specific attributes
    for the POD application (affiliation, establishment, auth type, etc.).
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="owner")
    auth_type = models.CharField(
        _("Authentication Type"),
        max_length=20,
        choices=AUTH_TYPE,
        default=AUTH_TYPE[0][0],
    )
    affiliation = models.CharField(
        _("Affiliation"),
        max_length=50,
        choices=AFFILIATION,
        default=DEFAULT_AFFILIATION,
    )
    commentaire = models.TextField(_("Comment"), blank=True, default="")
    hashkey = models.CharField(
        max_length=64,
        unique=True,
        blank=True,
        default="",
        help_text=_("Unique hash generated from username and secret key."),
    )
    userpicture = models.ForeignKey(
        CustomImageModel,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        verbose_name=_("Picture"),
    )
    establishment = models.CharField(
        _("Establishment"),
        max_length=10,
        blank=True,
        choices=ESTABLISHMENTS,
        default=ESTABLISHMENTS[0][0],
    )

    accessgroups = models.ManyToManyField(
        "authentication.AccessGroup",
        blank=True,
        related_name="users",
        verbose_name=_("Access Groups"),
    )
    sites = models.ManyToManyField(Site, related_name="owners")
    accepts_notifications = models.BooleanField(
        verbose_name=_("Accept notifications"),
        default=None,
        null=True,
        help_text=_("Receive push notifications on your devices."),
    )

    class Meta:
        verbose_name = _("Owner")
        verbose_name_plural = _("Owners")
        ordering = ["user"]

    def __str__(self) -> str:
        if HIDE_USERNAME:
            return f"{self.user.first_name} {self.user.last_name}"
        return f"{self.user.first_name} {self.user.last_name} ({self.user.username})"

    def save(self, *args, **kwargs) -> None:
        """
        Overridden save method to ensure hashkey generation.
        """
        if self.user and self.user.username and not self.hashkey:
            self.hashkey = hashlib.sha256(
                (SECRET_KEY + self.user.username).encode("utf-8")
            ).hexdigest()
        super().save(*args, **kwargs)

    def is_manager(self) -> bool:
        """
        Check if the user has management permissions on the current site.
        """
        if not self.user.groups.exists():
            return False
        group_ids = (
            self.user.groups.all()
            .filter(groupsite__sites=Site.objects.get_current())
            .values_list("id", flat=True)
        )

        return (
            self.user.is_staff
            and Permission.objects.filter(group__id__in=group_ids).count() > 0
        )

    @property
    def email(self) -> str:
        return self.user.email


@receiver(post_save, sender=Owner)
def default_site_owner(sender, instance: Owner, created: bool, **kwargs) -> None:
    """Assigns the current site to the owner upon creation/update if none exists."""
    if instance.pk and instance.sites.count() == 0:
        instance.sites.add(Site.objects.get_current())


@receiver(post_save, sender=User)
def create_owner_profile(sender, instance: User, created: bool, **kwargs) -> None:
    """Automatically creates an Owner profile when a Django User is created."""
    if created:
        try:
            Owner.objects.get_or_create(user=instance)
        except Exception as e:
            logger.error(
                f"Error creating owner profile for user {instance.username}: {e}",
                exc_info=True,
            )
