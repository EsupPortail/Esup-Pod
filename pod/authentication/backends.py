from shibboleth.backends import ShibbolethRemoteUserBackend
from django.contrib.sites.shortcuts import get_current_site

from django.conf import settings
from pod.authentication.populatedCASbackend import get_ldap_conn, get_entry, populate_user_from_entry

POPULATE_USER = getattr(settings, 'POPULATE_USER', None)
USER_LDAP_MAPPING_ATTRIBUTES = getattr(settings, 'USER_LDAP_MAPPING_ATTRIBUTES',{})

class ShibbBackend(ShibbolethRemoteUserBackend):
    @staticmethod
    def update_user_params(user, params):
        super(ShibbBackend,
              ShibbBackend).update_user_params(user, params)

        if POPULATE_USER == 'LDAP':
                list_value = []
                for val in USER_LDAP_MAPPING_ATTRIBUTES.values():
                        list_value.append(str(val))
                conn = get_ldap_conn()
                if conn is not None:
                        entry = get_entry(conn, user.username.replace('@u-bordeaux.fr',''), list_value)
                        if entry is not None:
                                populate_user_from_entry(user, user.owner, entry)

        user.owner.auth_type = "Shibboleth"
        if get_current_site(None) not in user.owner.sites.all():
            user.owner.sites.add(get_current_site(None))
        user.owner.save()
