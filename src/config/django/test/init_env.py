"""
Test environment initialization.

Sets up environment variables required for running tests.
Enables all authentication providers (CAS, LDAP, Shibboleth, OIDC) to ensure
comprehensive coverage of authentication flows during testing.
"""

import os

os.environ["POD_AUTH_USE_CAS"] = "True"
os.environ["POD_AUTH_USE_LDAP"] = "True"
os.environ["POD_AUTH_USE_SHIB"] = "True"
os.environ["POD_AUTH_USE_OIDC"] = "True"
