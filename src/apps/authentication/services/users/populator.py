"""
Esup-Pod - User and Owner data populator from external sources.
"""

from typing import Any, Dict, List, Optional
import logging
from ...conf import auth_settings
from django.contrib.sites.models import Site
from django.core.exceptions import ObjectDoesNotExist
from ...models import AccessGroup, Owner
from ..ldap_client import get_ldap_conn, get_ldap_entry

logger = logging.getLogger(__name__)


class UserPopulator:
    """
    Handles the population of User and Owner models from external sources (CAS, LDAP).
    """

    def __init__(self, user: Any):
        """Initializes the populator and ensures an Owner exists for the user."""
        self.user = user
        # Ensure owner exists
        if not hasattr(self.user, "owner"):
            Owner.objects.create(user=self.user)
        self.owner = self.user.owner

    def run(self, source: str, attributes: Optional[Dict[str, Any]] = None) -> None:
        """
        Main entry point to populate user data.
        :param source: 'CAS', 'LDAP', 'Shibboleth', or 'OIDC'
        :param attributes: Dictionary of attributes (from CAS, Shibboleth headers, or OIDC claims)
        """
        self.owner.auth_type = source
        self._delete_synchronized_access_groups()

        if source == "CAS" and attributes:
            self._populate_from_cas(attributes)
        elif source == "LDAP":
            self._populate_from_ldap()
        elif source == "Shibboleth" and attributes:
            self._populate_from_shibboleth(attributes)
        elif source == "OIDC" and attributes:
            self._populate_from_oidc(attributes)

        self.owner.save()
        self.user.save()

    def _delete_synchronized_access_groups(self) -> None:
        """Remove groups that are marked for auto-sync."""
        groups_to_sync = self.owner.accessgroups.filter(auto_sync=True)
        if groups_to_sync.exists():
            self.owner.accessgroups.remove(*groups_to_sync)

    def _populate_from_cas(self, attributes: Dict[str, Any]) -> None:
        """Map CAS attributes to User/Owner."""
        self.owner.affiliation = attributes.get(
            "primaryAffiliation", auth_settings.default_affiliation
        )

        # Handle affiliations list for group creation/staff status
        affiliations = attributes.get("affiliation", [])
        if isinstance(affiliations, str):
            affiliations = [affiliations]

        self._process_affiliations(affiliations)

        # Handle explicit groups
        groups = attributes.get("groups", [])
        if isinstance(groups, str):
            groups = [groups]
        self._assign_access_groups(groups)

    def _populate_from_shibboleth(self, attributes: Dict[str, Any]) -> None:
        """Map Shibboleth attributes to User/Owner."""

        if "first_name" in attributes:
            self.user.first_name = attributes["first_name"]
        if "last_name" in attributes:
            self.user.last_name = attributes["last_name"]
        if "email" in attributes:
            self.user.email = attributes["email"]

        self.owner.affiliation = attributes.get(
            "affiliation", auth_settings.default_affiliation
        )

        affiliations = attributes.get("affiliations", [])
        if isinstance(affiliations, str):
            if ";" in affiliations:
                affiliations = affiliations.split(";")
            else:
                affiliations = [affiliations]

        self._process_affiliations(affiliations)

    def _populate_from_oidc(self, attributes: Dict[str, Any]) -> None:
        """Map OIDC claims to User/Owner."""

        given_name_claim = auth_settings.oidc_claim_given_name
        family_name_claim = auth_settings.oidc_claim_family_name

        self.user.first_name = attributes.get(given_name_claim, self.user.first_name)
        self.user.last_name = attributes.get(family_name_claim, self.user.last_name)
        self.user.email = attributes.get("email", self.user.email)

        self.owner.affiliation = auth_settings.oidc_default_affiliation

        # OIDC default access groups
        oidc_groups = auth_settings.oidc_default_access_group_code_names
        self._assign_access_groups(oidc_groups)

        # Is user staff?
        if self.owner.affiliation in auth_settings.affiliation_staff:
            self.user.is_staff = True

    def _populate_from_ldap(self) -> None:
        """Fetch and map LDAP attributes to User/Owner."""
        if not self._is_ldap_configured():
            return

        conn = get_ldap_conn()
        if not conn:
            return

        entry = get_ldap_entry(conn, self.user.username)
        if entry:
            self._apply_ldap_entry(entry)

    def _apply_ldap_entry(self, entry: Any) -> None:
        """Maps LDAP attributes to the user and owner models."""
        self.user.email = self._get_ldap_value(entry, "mail", "")
        self.user.first_name = self._get_ldap_value(entry, "first_name", "")
        self.user.last_name = self._get_ldap_value(entry, "last_name", "")
        self.user.save()

        self.owner.affiliation = self._get_ldap_value(
            entry, "primaryAffiliation", auth_settings.default_affiliation
        )
        self.owner.establishment = self._get_ldap_value(entry, "establishment", "")
        self.owner.save()

        affiliations = self._get_ldap_value(entry, "affiliations", [])
        if isinstance(affiliations, str):
            affiliations = [affiliations]
        self._process_affiliations(affiliations)

        # Groups from LDAP
        ldap_group_attr = auth_settings.ldap_mapping_attributes.get("groups")
        groups_element = []
        if ldap_group_attr and entry[ldap_group_attr]:
            groups_element = entry[ldap_group_attr].values

        self._assign_access_groups(groups_element)

    def _process_affiliations(self, affiliations: List[str]) -> None:
        """Process list of affiliations to set staff status and create AccessGroups."""

        create_group_from_aff = auth_settings.create_group_from_affiliation
        current_site = Site.objects.get_current()

        for affiliation in affiliations:
            if affiliation in auth_settings.affiliation_staff:
                self.user.is_staff = True

            if create_group_from_aff:
                accessgroup, created = AccessGroup.objects.get_or_create(
                    code_name=affiliation
                )
                if created:
                    accessgroup.display_name = affiliation
                    accessgroup.auto_sync = True
                    accessgroup.save()

                accessgroup.sites.add(current_site)
                self.owner.accessgroups.add(accessgroup)

    def _assign_access_groups(self, groups: List[str]) -> None:
        """Assign AccessGroups based on group codes."""

        create_group_from_groups = auth_settings.create_group_from_groups
        current_site = Site.objects.get_current()

        for group_code in groups:
            # We assume GROUP_STAFF is same as AFFILIATION_STAFF
            if group_code in auth_settings.affiliation_staff:
                self.user.is_staff = True

            if create_group_from_groups:
                accessgroup, created = AccessGroup.objects.get_or_create(
                    code_name=group_code
                )
                if created:
                    accessgroup.display_name = group_code
                    accessgroup.auto_sync = True
                    accessgroup.save()
                accessgroup.sites.add(current_site)
                self.owner.accessgroups.add(accessgroup)
            else:
                try:
                    accessgroup = AccessGroup.objects.get(code_name=group_code)
                    self.owner.accessgroups.add(accessgroup)
                except ObjectDoesNotExist:
                    logger.debug(
                        "AccessGroup with code_name %r not found in database, skipping.",
                        group_code,
                    )

    def _get_ldap_value(self, entry: Any, attribute: str, default: Any) -> Any:
        """Safely retrieves a value from an LDAP entry using configured mapping."""
        mapping = auth_settings.ldap_mapping_attributes.get(attribute)
        if mapping and entry[mapping]:
            if attribute == "last_name" and isinstance(entry[mapping].value, list):
                return entry[mapping].value[0]
            elif attribute == "affiliations":
                return entry[mapping].values
            else:
                return entry[mapping].value
        return default

    def _is_ldap_configured(self) -> bool:
        """Checks if LDAP settings are present in the configuration."""

        ldap_config = auth_settings.ldap_server
        return bool(ldap_config.get("url"))
