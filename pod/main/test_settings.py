# test_settings.py
# from ..settings import *
import os
from ..settings import INSTALLED_APPS, MIDDLEWARE, AUTHENTICATION_BACKENDS
from ..settings import ROOT_URLCONF, WSGI_APPLICATION, TEMPLATES
from ..settings import AUTH_PASSWORD_VALIDATORS, USE_I18N, USE_L10N
from ..settings import LOCALE_PATHS
from ..settings import USE_TZ, REST_FRAMEWORK, LOG_DIRECTORY, LOGGING

TEST_SETTINGS = True

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
        "NAME": "db.sqlite",
    }
}
LANGUAGES = (("fr", "Français"), ("en", "English"), ("nl", "Netherlands"))
LANGUAGE_CODE = "en"
THIRD_PARTY_APPS = ["enrichment", "live"]
USE_PODFILE = True
USE_STATS_VIEW = True
ACCOMMODATION_YEARS = {"faculty": 1}
USE_OBSOLESCENCE = True
ACTIVE_VIDEO_COMMENT = True
USER_VIDEO_CATEGORY = True
POD_ARCHIVE_AFFILIATION = ["faculty"]
WARN_DEADLINES = [60, 30, 7]
USE_BBB = True
USE_VIDEO_RECORD = True
ORGANIZE_BY_THEME = True
