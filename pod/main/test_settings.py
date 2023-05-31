"""Esup-Pod "test mode" settings."""
# test_settings.py
# from ..settings import *
from ..settings import BASE_DIR as settings_base_dir
from ..settings import USE_TZ, REST_FRAMEWORK, LOG_DIRECTORY, LOGGING
from ..settings import LOCALE_PATHS, STATICFILES_DIRS, DEFAULT_AUTO_FIELD
from ..settings import AUTH_PASSWORD_VALIDATORS, USE_I18N, USE_L10N
from ..settings import ROOT_URLCONF, WSGI_APPLICATION, TEMPLATES
from ..settings import INSTALLED_APPS, MIDDLEWARE, AUTHENTICATION_BACKENDS
import os

USE_OPENCAST_STUDIO = True


TEST_SETTINGS = True
TEMPLATES[0]["DIRS"].append(
    os.path.join(settings_base_dir, "custom", "static", "opencast")
)

for application in INSTALLED_APPS:
    if application.startswith("pod"):
        path = application.replace(".", os.path.sep) + "/settings.py"
        if os.path.exists(path):
            _temp = __import__(application, globals(), locals(), ["settings"])
            for variable in dir(_temp.settings):
                if variable == variable.upper():
                    locals()[variable] = getattr(_temp.settings, variable)


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "db-test.sqlite",
        "OPTIONS": {
            "timeout": 20,
        },
    }
}
LANGUAGES = (("fr", "Français"), ("en", "English"))
LANGUAGE_CODE = "en"
THIRD_PARTY_APPS = ["enrichment", "live"]
USE_PODFILE = True
USE_FAVORITES = True
USE_STATS_VIEW = True
ACCOMMODATION_YEARS = {"faculty": 1}
USE_OBSOLESCENCE = True
USER_PLAYLIST = True
SHOW_EVENTS_ON_HOMEPAGE = True
ACTIVE_VIDEO_COMMENT = True
USER_VIDEO_CATEGORY = True
POD_ARCHIVE_AFFILIATION = ["faculty"]
WARN_DEADLINES = [60, 30, 7]
USE_BBB = True
ORGANIZE_BY_THEME = True
SHIBBOLETH_STAFF_ALLOWED_DOMAINS = ()
SHIBBOLETH_ATTRIBUTE_MAP = {
    "REMOTE_USER": (True, "username"),
    "Shibboleth-givenName": (True, "first_name"),
    "Shibboleth-sn": (False, "last_name"),
    "Shibboleth-mail": (False, "email"),
    "Shibboleth-primary-affiliation": (False, "affiliation"),
    "Shibboleth-unscoped-affiliation": (False, "affiliations"),
}
REMOTE_USER_HEADER = "REMOTE_USER"
EXISTING_BROADCASTER_IMPLEMENTATIONS = ["Wowza", "Test"]
AFFILIATION_EVENT = ["employee"]

USE_MEETING = True
# found on https://bigbluebutton.org/api-mate/
BBB_API_URL = "http://test-install.blindsidenetworks.com/bigbluebutton/api/"
BBB_SECRET_KEY = "8cd8ef52e8e101574e400365b55e11a6"
MEETING_DISABLE_RECORD = False

# xAPI settings
USE_XAPI = True
USE_XAPI_VIDEO = True
XAPI_ANONYMIZE_ACTOR = False
XAPI_LRS_URL = ""
XAPI_LRS_LOGIN = ""
XAPI_LRS_PWD = ""
