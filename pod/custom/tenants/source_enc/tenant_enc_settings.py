"""Settings for an Esup-Pod encoding tenant."""

# Cette ligne va importer les settings déjà présents dans votre application,
# vous pourrez les surchager par site
from pod.settings import *

DEBUG = False

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

CELERY_TO_ENCODE = True  # Active encode
CELERY_BROKER_URL = CELERY_BROKER_URL + "-__NAME__"  # Define a broker

# !!!!!!!!!!!!! A LAISSER EN DERNIER !!!!!!!!!!!!!
the_update_settings = update_settings(locals())
for variable in the_update_settings:
    locals()[variable] = the_update_settings[variable]
