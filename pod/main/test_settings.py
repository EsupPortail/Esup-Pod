"""Esup-Pod "test mode" settings."""

# test_settings.py
# from ..settings import *
from ..settings import BASE_DIR as settings_base_dir
from ..settings import USE_TZ, REST_FRAMEWORK, LOG_DIRECTORY, LOGGING
from ..settings import LOCALE_PATHS, STATICFILES_DIRS, DEFAULT_AUTO_FIELD
from ..settings import AUTH_PASSWORD_VALIDATORS, USE_I18N
from ..settings import ROOT_URLCONF, WSGI_APPLICATION, TEMPLATES
from ..settings import INSTALLED_APPS, MIDDLEWARE, AUTHENTICATION_BACKENDS
from ..settings import SERIALIZATION_MODULES, TAGULOUS_NAME_MAX_LENGTH

import os
from bs4 import BeautifulSoup
import requests

USE_OPENCAST_STUDIO = True


TEST_SETTINGS = True
TEMPLATES[0]["DIRS"].append(
    os.path.join(settings_base_dir, "custom", "static", "opencast")
)
USE_DOCKER = True
ES_URL = ["http://elasticsearch.localhost:9200/"]
ES_VERSION = 8
ES_INDEX = "pod"
path = "pod/custom/settings_local.py"
if os.path.exists(path):
    _temp = __import__("pod.custom", globals(), locals(), ["settings_local"])
    USE_DOCKER = getattr(_temp.settings_local, "USE_DOCKER", USE_DOCKER)
    ES_URL = getattr(_temp.settings_local, "ES_URL", ES_URL)
    ES_VERSION = getattr(_temp.settings_local, "ES_VERSION", ES_VERSION)

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
            "timeout": 40.0,  # in seconds
            # see also https://docs.python.org/3.10/library/sqlite3.html#sqlite3.connect
        },
    }
}

LANGUAGES = (("fr", "Français"), ("en", "English"))
LANGUAGE_CODE = "en"
THIRD_PARTY_APPS = ["enrichment", "live"]
USE_CUT = True
USE_DRESSING = True
USE_FAVORITES = True
USE_PODFILE = True
USE_PLAYLIST = True
USE_PROMOTED_PLAYLIST = True
RESTRICT_PROMOTED_PLAYLIST_ACCESS_TO_STAFF_ONLY = False
USE_STATS_VIEW = True
USE_QUIZ = True
ACCOMMODATION_YEARS = {"faculty": 1}
USE_OBSOLESCENCE = True
ACTIVE_VIDEO_COMMENT = True
USER_VIDEO_CATEGORY = True
POD_ARCHIVE_AFFILIATION = ["faculty"]
WARN_DEADLINES = [60, 30, 7]
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
USE_SPEAKER = True


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

# Webinar options
USE_MEETING_WEBINAR = True
MEETING_WEBINAR_AFFILIATION = ["faculty", "employee", "staff"]

# Uniquement lors d'environnement conteneurisé
if USE_DOCKER:
    MIGRATION_MODULES = {"flatpages": "pod.db_migrations"}
    MIGRATION_DIRECTORY = os.path.join(settings_base_dir, "db_migrations")
    if not os.path.exists(MIGRATION_DIRECTORY):
        os.mkdir(MIGRATION_DIRECTORY)
        file = os.path.join(MIGRATION_DIRECTORY, "__init__.py")
        open(file, "a").close()

# AI Enhancement settings
USE_AI_ENHANCEMENT = True
AI_ENHANCEMENT_CLIENT_ID = "mocked_id"
AI_ENHANCEMENT_CLIENT_SECRET = "mock_secret"
AI_ENHANCEMENT_API_URL = ""
AI_ENHANCEMENT_API_VERSION = ""

# DEBUG
USE_DEBUG_TOOLBAR = False
