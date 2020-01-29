# test_settings.py

from ..settings import *

MEDIA_ROOT=os.path.join(BASE_DIR, 'media'),

DATABASES={
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite',
    }
}
LANGUAGE_CODE='en'

THIRD_PARTY_APPS = ["enrichment", "interactive", "live"]
USE_PODFILE = True
