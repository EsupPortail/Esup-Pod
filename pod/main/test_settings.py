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
from bs4 import BeautifulSoup
import requests

USE_OPENCAST_STUDIO = True


TEST_SETTINGS = True
TEMPLATES[0]["DIRS"].append(
    os.path.join(settings_base_dir, "custom", "static", "opencast")
)
USE_DOCKER = True
path = "pod/custom/settings_local.py"
ES_URL = ["http://127.0.0.1:9200/"]
ES_VERSION = 6
if os.path.exists(path):
    _temp = __import__("pod.custom", globals(), locals(), ["settings_local"])
    USE_DOCKER = getattr(_temp.settings_local, "USE_DOCKER", True)
    ES_URL = getattr(_temp.settings_local, "ES_URL", ["http://127.0.0.1:9200/"])
    ES_VERSION = getattr(_temp.settings_local, "ES_VERSION", 6)

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
USE_PLAYLIST = True
USE_STATS_VIEW = True
ACCOMMODATION_YEARS = {"faculty": 1}
USE_OBSOLESCENCE = True
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
RESTRICT_EDIT_VIDEO_ACCESS_TO_STAFF_ONLY = False
EXISTING_BROADCASTER_IMPLEMENTATIONS = ["Wowza", "Test"]
AFFILIATION_EVENT = ["employee"]

USE_MEETING = True


def get_shared_secret():
    api_mate_url = "https://bigbluebutton.org/api-mate/"
    response = requests.get(api_mate_url)
    soup = BeautifulSoup(response.text, features="html.parser")
    input_val = soup.body.find("input", attrs={"id": "input-custom-server-salt"})
    return input_val.get("value")


BBB_API_URL = "http://test-install.blindsidenetworks.com/bigbluebutton/api/"
BBB_SECRET_KEY = get_shared_secret()
MEETING_DISABLE_RECORD = False

USE_IMPORT_VIDEO = True

# xAPI settings
USE_XAPI = True
USE_XAPI_VIDEO = True
XAPI_ANONYMIZE_ACTOR = False
XAPI_LRS_URL = ""
XAPI_LRS_LOGIN = ""
XAPI_LRS_PWD = ""

# Uniquement lors d'environnement conteneurisé
if USE_DOCKER:
    MIGRATION_MODULES = {"flatpages": "pod.db_migrations"}
    MIGRATION_DIRECTORY = os.path.join(settings_base_dir, "db_migrations")
    if not os.path.exists(MIGRATION_DIRECTORY):
        os.mkdir(MIGRATION_DIRECTORY)
        file = os.path.join(MIGRATION_DIRECTORY, "__init__.py")
        open(file, "a").close()

# DEBUG
USE_DEBUG_TOOLBAR = False
