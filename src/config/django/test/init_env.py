"""
Esup-Pod - Test environment initialization.

Sets up environment variables required for running tests.
Enables all authentication providers (CAS, LDAP, Shibboleth, OIDC) to ensure
comprehensive coverage of authentication flows during testing.
"""

import os

os.environ["USE_CAS"] = "True"
os.environ["USE_LDAP"] = "True"
os.environ["USE_SHIB"] = "True"
os.environ["USE_OIDC"] = "True"
