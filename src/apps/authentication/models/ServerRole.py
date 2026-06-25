"""
Esup-Pod - ServerRole model for the authentication app.

Provides custom role-based access control (RBAC) to manage specific
permissions (e.g., video deletion) per establishment or globally.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class ServerRole(models.Model):
    """
    Custom role for Pod application.
    Allows administrators to define roles with specific capabilities.
    """

    SCOPE_GLOBAL = "GLOBAL"
    SCOPE_ESTABLISHMENT = "ESTABLISHMENT"
    SCOPE_CHOICES = [
        (SCOPE_GLOBAL, _("Global (All establishments)")),
        (
            SCOPE_ESTABLISHMENT,
            _("Establishment specific (Restricted to user’s establishment)"),
        ),
    ]

    name = models.CharField(_("Role Name"), max_length=100, unique=True)
    description = models.TextField(_("Description"), blank=True)
    scope = models.CharField(
        _("Scope"),
        max_length=20,
        choices=SCOPE_CHOICES,
        default=SCOPE_ESTABLISHMENT,
        help_text=_("Defines the boundaries where this role’s permissions apply."),
    )

    # --- Permissions ---
    can_delete_video = models.BooleanField(
        _("Can delete videos"),
        default=False,
        help_text=_("Allows the user to delete videos within the role’s scope."),
    )
    can_edit_video = models.BooleanField(
        _("Can edit videos"),
        default=False,
        help_text=_("Allows the user to edit any video within the role’s scope."),
    )
    can_import_video = models.BooleanField(
        _("Can import external videos"),
        default=False,
        help_text=_("Allows the user to import videos from external sources."),
    )

    class Meta:
        """ServerRole model metadata."""

        verbose_name = _("Server Role")
        verbose_name_plural = _("Server Roles")
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.get_scope_display()})"
