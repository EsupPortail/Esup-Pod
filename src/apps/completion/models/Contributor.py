"""
Esup-Pod - Contributor model.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
import base64


class Contributor(models.Model):
    """
    Global directory of contributors.
    Fusions the V4 concept of Contributor and Speaker.
    """

    first_name = models.CharField(max_length=200, verbose_name=_("First name"))
    last_name = models.CharField(max_length=200, verbose_name=_("Last name"))
    email_address = models.EmailField(
        null=True, blank=True, default="", verbose_name=_("Email address")
    )
    weblink = models.URLField(
        max_length=200, null=True, blank=True, verbose_name=_("Web link")
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Meta options for Contributor."""

        verbose_name = _("Contributor")
        verbose_name_plural = _("Contributors")
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_base_mail(self):
        """Returns base64 encoded email for anti-spam protection (like in V4)."""
        if self.email_address:
            return base64.b64encode(self.email_address.encode("utf-8")).decode("utf-8")
        return ""

    def get_noscript_mail(self):
        """Returns email with @ replaced for non-JS clients."""
        if self.email_address:
            return self.email_address.replace("@", "__AT__")
        return ""
