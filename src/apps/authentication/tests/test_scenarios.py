import sys
from importlib import reload
from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import clear_url_caches, resolve
from django_cas_ng import views as cas_views
from django.contrib.auth import views as auth_views


def reload_urlconf():
    clear_url_caches()
    if settings.ROOT_URLCONF in sys.modules:
        reload(sys.modules[settings.ROOT_URLCONF])


class AuthenticationScenariosTests(TestCase):

    def tearDown(self):
        # Reset to default state after each test to avoid side effects
        clear_url_caches()
        reload_urlconf()

    @override_settings(
        USE_CAS=True,
        USE_LOCAL_AUTH=False,
        AUTHENTICATION_BACKENDS=['django_cas_ng.backends.CASBackend'],
        CAS_SERVER_URL='https://cas.example.com'
    )
    def test_university_mode_cas_only(self):
        """
        Scenario: University / Production Mode
        - CAS is Enabled
        - Local Auth is Disabled

        Expectation:
        - /accounts/login resolves to CAS login view
        """
        reload_urlconf()

        # 1. Verify URL resolution
        resolver_match = resolve('/accounts/login')
        self.assertEqual(resolver_match.func.view_class, cas_views.LoginView)

        resolver_match_logout = resolve('/accounts/logout')
        self.assertEqual(resolver_match_logout.func.view_class, cas_views.LogoutView)

    @override_settings(
        USE_CAS=False,
        USE_LOCAL_AUTH=True,
        AUTHENTICATION_BACKENDS=['django.contrib.auth.backends.ModelBackend']
    )
    def test_local_mode_default(self):
        """
        Scenario: Local Development Mode
        - CAS is Disabled
        - Local Auth is Enabled

        Expectation:
        - /accounts/login resolves to Django standard LoginView
        """
        reload_urlconf()

        # 1. Verify URL resolution
        resolver_match = resolve('/accounts/login')
        self.assertEqual(resolver_match.func.view_class, auth_views.LoginView)

        resolver_match_logout = resolve('/accounts/logout')
        self.assertEqual(resolver_match_logout.func.view_class, auth_views.LogoutView)
