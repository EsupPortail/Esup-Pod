# test_settings.py
# from ..settings import *
import os

_temp = __import__("pod", globals(), locals(), ['settings'])
for variable in (dir(_temp.settings)):
    if variable == variable.upper():
        locals()[variable] = getattr(_temp.settings, variable)

for application in INSTALLED_APPS:
    if application.startswith('pod'):
        path = application.replace('.', os.path.sep) + '/settings.py'
        if os.path.exists(path):
            _temp = __import__(application, globals(), locals(), ['settings'])
            for variable in (dir(_temp.settings)):
                if variable == variable.upper():
                    locals()[variable] = getattr(_temp.settings, variable)

TEST_SETTINGS = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite',
    }
}
LANGUAGE_CODE = 'en'
THIRD_PARTY_APPS = ["enrichment", "live"]
USE_PODFILE = True
USE_STATS_VIEW = True
