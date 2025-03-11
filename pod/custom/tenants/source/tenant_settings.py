"""Settings for an Esup-Pod tenant."""
# Cette ligne va importer les settings déjà présents dans votre application,
# vous pourrez les surchager par site
from pod.settings import *

DEBUG = False

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Ici il faut mettre l'id unique du site qui correspond à l'id présent
# dans votre espace d'administration sur le site en question
SITE_ID = __ID_SITE__

# index pour elasticsearch,
# il est important de le modifier pour que chaque instance ai son moteur de recherche
ES_INDEX = 'pod2__NAME__'

ALLOWED_HOSTS = ['pod.univ.fr', '__DOMAIN_NAME__']

DEFAULT_FROM_EMAIL = 'no-reply@__DOMAIN_NAME__'  # to complete
SERVER_EMAIL = 'no-reply@__DOMAIN_NAME__'  # to complete
HELP_MAIL = 'no-reply@__DOMAIN_NAME__'  # to complete
CONTACT_US_EMAIL = ['contact@__DOMAIN_NAME__']  # to complete

TEMPLATE_VISIBLE_SETTINGS = {
    'TITLE_SITE': '__NAME__.Video',
    'TITLE_ETB': '__NAME__',
    'LOGO_SITE': 'img/logoPod.svg',
    'LOGO_COMPACT_SITE': 'img/logoPod.svg',
    'LOGO_ETB': '__NAME__/custom/images/__NAME__.png',
    'LOGO_PLAYER': 'img/pod_favicon.svg',
    'FOOTER_TEXT': (
        '__NAME__ ',
        ' '
    ),
    'LINK_PLAYER': '#',
    'CSS_OVERRIDE': '__NAME__/custom/override.css',
    # 'PRE_HEADER_TEMPLATE': 'custom/preheader.html',
    # 'POST_FOOTER_TEMPLATE': 'custom/footer.html',
    # 'TRACKING_TEMPLATE': 'custom/tracking.html',
}
DEFAULT_DC_COVERAGE = TEMPLATE_VISIBLE_SETTINGS["TITLE_ETB"] + " - Paris - France"
DEFAULT_DC_RIGHTS = "BY-NC-SA"

CELERY_BROKER_URL = CELERY_BROKER_URL + "-__NAME__"  # Define a broker


# !!!!!!!! A LAISSER EN DERNIER !!!!!!!!!!!!!
the_update_settings = update_settings(locals())
for variable in the_update_settings:
    locals()[variable] = the_update_settings[variable]
