import logging
from typing import Optional, Dict, Any, List
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django_cas_ng.utils import get_cas_client
from ldap3 import Server, Connection, ALL
from .models import Owner, AccessGroup, AFFILIATION_STAFF

UserModel = get_user_model()
logger = logging.getLogger(__name__)

def verify_cas_ticket(ticket: str, service_url: str) -> Optional[User]:
    """
    Verifies the CAS service ticket and retrieves or creates the corresponding Django user.
    Also synchronizes user profile data via CAS attributes.
    """
    client = get_cas_client(service_url=service_url)
    username, attributes, _ = client.verify_ticket(ticket)

    if not username:
        logger.warning("CAS ticket validation failed")
        return None

    if attributes:
        logger.debug(f"CAS Attributes: {attributes}")

    if getattr(settings, 'CAS_FORCE_CHANGE_USERNAME_CASE', 'lower') == 'lower':
        username = username.lower()

    user, created = UserModel.objects.get_or_create(username=username)
    
    if created:
        user.set_unusable_password()
        user.save()
        
    if hasattr(user, 'owner'):
        user.owner.auth_type = "CAS"
        user.owner.save()

    sync_user_data(user, attributes)

    return user

def sync_user_data(user: User, cas_attributes: Optional[Dict[str, Any]]) -> None:
    """
    Synchronizes user attributes from CAS and LDAP sources and updates staff status.
    """
    owner, _ = Owner.objects.get_or_create(user=user)
    owner.auth_type = "CAS"

    if cas_attributes:
        if 'mail' in cas_attributes:
            user.email = cas_attributes['mail']
        if 'givenName' in cas_attributes:
            user.first_name = cas_attributes['givenName']
        if 'sn' in cas_attributes:
            user.last_name = cas_attributes['sn']
        
        affil = cas_attributes.get('primaryAffiliation') or cas_attributes.get('eduPersonPrimaryAffiliation')
        if affil:
            owner.affiliation = affil

    ldap_config = getattr(settings, "LDAP_SERVER", None)
    if ldap_config and ldap_config.get("url"):
        try:
            sync_from_ldap(user, owner)
        except Exception as e:
            logger.error(f"LDAP sync error: {e}")

    if owner.affiliation in AFFILIATION_STAFF:
        user.is_staff = True
    else:
        if not user.is_superuser:
            user.is_staff = False 

    user.save()
    owner.save()

def sync_from_ldap(user: User, owner: Owner) -> None:
    """
    Connects to the configured LDAP server to fetch and map additional user details.
    """
    ldap_settings = settings.LDAP_SERVER
    server = Server(ldap_settings['url'], get_info=ALL)
    
    conn = Connection(
        server, 
        getattr(settings, "AUTH_LDAP_BIND_DN", ""), 
        getattr(settings, "AUTH_LDAP_BIND_PASSWORD", ""), 
        auto_bind=True
    )

    search_base = getattr(settings, "AUTH_LDAP_USER_SEARCH_BASE", "ou=people,dc=univ,dc=fr")
    search_filter = f"(uid={user.username})"
    attributes = ['mail', 'sn', 'givenName', 'eduPersonPrimaryAffiliation', 'eduPersonAffiliation']

    conn.search(search_base, search_filter, attributes=attributes)
    
    if len(conn.entries) > 0:
        entry = conn.entries[0]
        
        if entry.mail: user.email = str(entry.mail)
        if entry.givenName: user.first_name = str(entry.givenName)
        if entry.sn: user.last_name = str(entry.sn)
        
        if entry.eduPersonPrimaryAffiliation:
            owner.affiliation = str(entry.eduPersonPrimaryAffiliation)
        
        if entry.eduPersonAffiliation:
            affiliations = [str(a) for a in entry.eduPersonAffiliation] if isinstance(entry.eduPersonAffiliation, list) else [str(entry.eduPersonAffiliation)]
            update_access_groups(owner, affiliations)

def update_access_groups(owner: Owner, affiliations_list: List[str]) -> None:
    """
    Updates the owner's access groups based on the provided affiliation list.
    Only modifies groups marked for auto-synchronization.
    """
    current_auto_groups = owner.accessgroups.filter(auto_sync=True)
    owner.accessgroups.remove(*current_auto_groups)
    
    for aff in affiliations_list:
        group, created = AccessGroup.objects.get_or_create(code_name=str(aff))
        if created:
            group.name = str(aff)
            group.display_name = str(aff)
            group.auto_sync = True
            group.save()
        
        owner.accessgroups.add(group)