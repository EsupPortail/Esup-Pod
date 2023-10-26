from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User, Permission, Group
from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.sites.models import Site

import hashlib
import logging
import traceback

logger = logging.getLogger(__name__)

if getattr(settings, "USE_PODFILE", False):
    from pod.podfile.models import CustomImageModel
else:
    from pod.main.models import CustomImageModel

HIDE_USERNAME = getattr(settings, "HIDE_USERNAME", False)

AUTH_TYPE = getattr(
    settings,
    "AUTH_TYPE",
    (
        ("local", _("local")),
        ("CAS", "CAS"),
        ("OIDC", "OIDC"),
        ("Shibboleth", "Shibboleth"),
    ),
)
AFFILIATION = getattr(
    settings,
    "AFFILIATION",
    (
        ("student", _("student")),
        ("faculty", _("faculty")),
        ("staff", _("staff")),
        ("employee", _("employee")),
        ("member", _("member")),
        ("affiliate", _("affiliate")),
        ("alum", _("alum")),
        ("library-walk-in", _("library-walk-in")),
        ("researcher", _("researcher")),
        ("retired", _("retired")),
        ("emeritus", _("emeritus")),
        ("teacher", _("teacher")),
        ("registered-reader", _("registered-reader")),
    ),
)
DEFAULT_AFFILIATION = AFFILIATION[0][0]
AFFILIATION_STAFF = getattr(
    settings, "AFFILIATION_STAFF", ("faculty", "employee", "staff")
)
ESTABLISHMENTS = getattr(
    settings,
    "ESTABLISHMENTS",
    (
        ("Etab_1", "Etab_1"),
        ("Etab_2", "Etab_2"),
    ),
)
SECRET_KEY = getattr(settings, "SECRET_KEY", "")
FILES_DIR = getattr(settings, "FILES_DIR", "files")


def get_name(self) -> str:
    """
    Returns the user's full name, including the username if not hidden.

    Returns:
        str: The user's full name and username if not hidden.
    """
    if HIDE_USERNAME or not self.is_authenticated:
        return self.get_full_name().strip()
    return f"{self.get_full_name()} ({self.get_username()})".strip()


User.add_to_class("__str__", get_name)


class Owner(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    auth_type = models.CharField(
        max_length=20, choices=AUTH_TYPE, default=AUTH_TYPE[0][0]
    )
    affiliation = models.CharField(
        max_length=50, choices=AFFILIATION, default=DEFAULT_AFFILIATION
    )
    commentaire = models.TextField(_("Comment"), blank=True, default="")
    hashkey = models.CharField(max_length=64, unique=True, blank=True, default="")
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
    accessgroups = models.ManyToManyField("authentication.AccessGroup", blank=True)
    sites = models.ManyToManyField(Site)
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

    def __str__(self):
        if HIDE_USERNAME:
            return "%s %s" % (self.user.first_name, self.user.last_name)
        return "%s %s (%s)" % (
            self.user.first_name,
            self.user.last_name,
            self.user.username,
        )

    def save(self, *args, **kwargs):
        self.hashkey = hashlib.sha256(
            (SECRET_KEY + self.user.username).encode("utf-8")
        ).hexdigest()
        super(Owner, self).save(*args, **kwargs)

    def is_manager(self):
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
    def email(self):
        return self.user.email


@receiver(post_save, sender=Owner)
def default_site_owner(sender, instance, created, **kwargs):
    if len(instance.sites.all()) == 0:
        instance.sites.add(Site.objects.get_current())


@receiver(post_save, sender=User)
def create_owner_profile(sender, instance, created, **kwargs):
    if created:
        try:
            Owner.objects.create(user=instance)
        except Exception as e:
            msg = "\n Create owner profile ***** Error:%r" % e
            msg += "\n%s" % traceback.format_exc()
            logger.error(msg)
            print(msg)


class GroupSite(models.Model):
    group = models.OneToOneField(Group, on_delete=models.CASCADE)
    sites = models.ManyToManyField(Site)

    class Meta:
        verbose_name = _("Group site")
        verbose_name_plural = _("Groups site")
        ordering = ["group"]


@receiver(post_save, sender=GroupSite)
def default_site_groupsite(sender, instance, created, **kwargs):
    if len(instance.sites.all()) == 0:
        instance.sites.add(Site.objects.get_current())


@receiver(post_save, sender=Group)
def create_groupsite_profile(sender, instance, created, **kwargs):
    if created:
        try:
            GroupSite.objects.create(group=instance)
        except Exception as e:
            msg = "\n Create groupsite profile ***** Error:%r" % e
            msg += "\n%s" % traceback.format_exc()
            logger.error(msg)
            print(msg)


class AccessGroup(models.Model):
    display_name = models.CharField(max_length=128, blank=True, default="")
    code_name = models.CharField(max_length=250, unique=True)
    sites = models.ManyToManyField(Site)
    auto_sync = models.BooleanField(
        _("Auto synchronize"),
        default=False,
        help_text=_("Check if the access group must be synchronized on user connexion."),
    )
    users = models.ManyToManyField(
        Owner,
        blank=True,
        through="Owner_accessgroups",
    )

    def __str__(self):
        return "%s" % (self.display_name)

    class Meta:
        verbose_name = _("Access Groups")
        verbose_name_plural = _("Access Groups")
        ordering = ["display_name"]
