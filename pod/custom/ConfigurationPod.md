# Configuration de la plateforme Esup-Pod

## 1/ Information

La plateforme Esup-Pod se base sur le framework Django écrit en Python. Elle supporte les versions 3.7 3.8 et 3.9 de Python

**Django Version : 3.2 LTS** 

> La documentation complète du framework : https://docs.djangoproject.com/fr/3.2/ (ou https://docs.djangoproject.com/en/3.2/)<br>
> L’Ensemble des variables de configuration du framework est accessible à cette adresse : https://docs.djangoproject.com/fr/3.2/ref/settings/

Voici les configurations des applications tierces utilisées par Esup-Pod : 

- ModelTransalation (0.18.7): L'application modeltranslation est utilisée pour traduire le contenu dynamique des modèles Django existants
    https://django-modeltranslation.readthedocs.io/en/latest/installation.html#configuration
- ckeditor (6.3.0): application permettant d'ajouter un éditeur CKEditor dans certains champs
    https://django-ckeditor.readthedocs.io/en/latest/#installation
- sorl.thumbnail (12.9.0): utilisée pour la génération des vignettes des vidéos 
    https://sorl-thumbnail.readthedocs.io/en/latest/reference/settings.html
- tagging (0.5.0): gestion des mots-clés associés à une vidéo // voir pour référencer une nouvelle application
    https://django-tagging.readthedocs.io/en/develop/#settings
- CAS (1.5.2): système d'authentification SSO_CAS
    https://github.com/kstateome/django-cas
- captcha (0.5.17): gestion du captcha du formulaire de contact 
    https://django-simple-captcha.readthedocs.io/en/latest/usage.html
- rest_framework (3.14.0): mise en place de l'API rest pour l'application
    https://www.django-rest-framework.org/
- django_select2 (latest): recherche et completion dans les formulaire
    https://django-select2.readthedocs.io/en/latest/
- shibboleth (latest): système d'authentification Shibboleth
    https://github.com/Brown-University-Library/django-shibboleth-remoteuser
- chunked_upload (2.0.0): // voir pour mettre à jour si nécessaire
    https://github.com/juliomalegria/django-chunked-upload
- mozilla_django_oidc (3.0.0): système d'authentification OpenID Connect
    https://mozilla-django-oidc.readthedocs.io/en/stable/installation.html
- honeypot (1.0.3): utilisé pour le formulaire de contact de Pod - ajoute un champ caché pour diminuer le spam
    https://github.com/jamesturk/django-honeypot/

## 2/ Configuration Générale de la plateforme Esup_Pod

- SITE_ID = 1

> _Valeur par défaut : 1_<br>
> L’identifiant (nombre entier) du site actuel. Peut être utilisé pour mettre en place une instance multi-tenant et ainsi gérer dans une même base de données du contenu pour plusieurs sites.<br>
> __ref : https://docs.djangoproject.com/fr/3.2/ref/settings/#site-id__


- SECRET_KEY = "A_CHANGER"

> _Valeur par défaut : 'A_CHANGER'_<br>
> La clé secrète d’une installation Django.<br>
> Elle est utilisée dans le contexte de la signature cryptographique, et doit être définie à une valeur unique et non prédictible.<br>
> Vous pouvez utiliser ce site pour en générer une : https://djecrety.ir/<br>
> __ref: https://docs.djangoproject.com/fr/3.2/ref/settings/#secret-key__


- DEBUG = True

> _Valeur par défaut : True_<br>
> Une valeur booléenne qui active ou désactive le mode de débogage.<br>
> Ne déployez jamais de site en production avec le réglage DEBUG activé.<br>
> __ref: https://docs.djangoproject.com/fr/3.2/ref/settings/#debug__

- SECURE_SSL_REDIRECT = not DEBUG
- SESSION_COOKIE_SECURE =  not DEBUG
- CSRF_COOKIE_SECURE =  not DEBUG

> _Valeur par défaut :  not DEBUG_<br>
> Ces 3 variables servent à sécuriser la plateforme en passant l'ensemble des requetes en https. Idem pour les cookies de session et de cross-sites qui seront également sécurisés<br>
> Il faut les passer à False en cas d'usage du runserver (phase de développement / debugage)<br>
> __ref: https://docs.djangoproject.com/fr/3.2/ref/settings/#secure-ssl-redirect__

- ALLOWED_HOSTS = ['localhost']

> _Valeur par défaut :  ['localhost']_<br>
> Une liste de chaînes représentant des noms de domaine/d’hôte que ce site Django peut servir.<br>
> C’est une mesure de sécurité pour empêcher les attaques d’en-tête Host HTTP, qui sont possibles même avec bien des configurations de serveur Web apparemment sécurisées.<br>
> __ref: https://docs.djangoproject.com/fr/3.2/ref/settings/#allowed-hosts__

**Cookie de session**
> __ref: https://docs.djangoproject.com/fr/3.2/ref/settings/#session-cookie-age__

- SESSION_COOKIE_AGE = 14400

> _Valeur par défaut :  14400 (secondes, soit 4 heures)_<br>
> L’âge des cookies de sessions, en secondes.

- SESSION_EXPIRE_AT_BROWSER_CLOSE = True

> _Valeur par défaut :  True_<br>
> Indique s’il faut que la session expire lorsque l’utilisateur ferme son navigateur.


- ADMINS = (('Name', 'adminmail@univ.fr'),)

> _Valeur par défaut :  (('Name', 'adminmail@univ.fr'),)_<br>
> Une liste de toutes les personnes qui reçoivent les notifications d’erreurs dans le code.<br>
> Lorsque DEBUG=False et qu’une vue lève une exception, Django envoie un courriel à ces personnes contenant les informations complètes de l’exception.<br>
> Chaque élément de la liste doit être un tuple au format  « (nom complet, adresse électronique) ».<br>
> Exemple : [('John', 'john@example.com'), ('Mary', 'mary@example.com')]<br>
> Dans Pod, les "admins" sont également destinataires des courriels de contact, d'encodage ou de flux rss si la variable CONTACT_US_EMAIL n'est pas renseignée.<br>
> __ref: https://docs.djangoproject.com/fr/3.2/ref/settings/#admins__


- MANAGERS = ADMINS

> Dans Pod, les "managers" sont destinataires des courriels de fin d'encodage (et ainsi des vidéos déposées sur la plateforme).<br>
> Le premier managers renseigné est également contact des flus rss.<br>
> Ils sont aussi destinataires des courriels de contact si la variable CONTACT_US_EMAIL n'est pas renseignée.<br>
> __ref: https://docs.djangoproject.com/fr/3.2/ref/settings/#managers__


- TIME_ZONE = "UTC"

> _Valeur par défaut :  "UTC"_<br>
> Une chaîne représentant le fuseau horaire pour cette installation.<br>
> __ref: https://docs.djangoproject.com/fr/3.2/ref/settings/#std:setting-TIME_ZONE__


### 2.1/ Courriel


- CONTACT_US_EMAIL = ""

> Liste des adresses destinataires des courriels de contact


- EMAIL_HOST = "smtp.univ.fr"

> nom du serveur smtp 
> _ref: https://docs.djangoproject.com/fr/3.2/ref/settings/#email-host_


- EMAIL_PORT = 25

> port d'écoute du serveur smtp


- EMAIL_SUBJECT_PREFIX = "[Pod] "

> Préfixe par défaut pour l'objet des courriels


- SERVER_EMAIL = "noreply@univ.fr"

> Expediteur par défaut pour les envois automatique (erreur de code etc.)


- DEFAULT_FROM_EMAIL = "noreply@univ.fr"

> Expediteur par défaut pour les envois de courriel (contact, encodage etc.)

- CUSTOM_CONTACT_US = False

> Si 'True', les e-mails de contacts seront adressés, selon le sujet,
> soit au propriétaire de la vidéo soit au(x) manageur(s) des vidéos Pod.
> (voir USER_CONTACT_EMAIL_CASE et USE_ESTABLISHMENT_FIELD)

- USER_CONTACT_EMAIL_CASE = []

> Une liste contenant les sujets de contact dont l'utilisateur
> sera seul destinataire plutôt que le(s) manageur(s).
> Si la liste est vide, les mails de contact seront envoyés au(x) manageur(s).
> Valeurs possibles :
>  'info', 'contribute', 'request_password',
>  'inapropriate_content', 'bug', 'other'

- USE_ESTABLISHMENT_FIELD = False

> Si valeur vaut 'True', rajoute un attribut 'establishment'
> à l'utilisateur Pod, ce qui permet de gérer plus d'un établissement.
> Dans ce cas, les emails de contact par exemple seront envoyés
>  soit à l'utilisateur soit au(x) manageur(s)
>  de l'établissement de l'utilisateur.
> (voir USER_CONTACT_EMAIL_CASE)
> Egalement, les emails de fin d'encodage seront envoyés au(x) manageur(s)
>  de l'établissement du propriétaire de la vidéo encodée,
>  en plus d'un email au propriétaire confirmant la fin d'encodage d'une vidéo.


### 2.2/ Base de données


````
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}
````

> Un dictionnaire contenant les réglages de toutes les bases de données à utiliser avec Django.<br>
> C’est un dictionnaire imbriqué dont les contenus font correspondre l’alias de base de données avec un dictionnaire contenant les options de chacune des bases de données.<br>
> __ref: https://docs.djangoproject.com/fr/3.2/ref/settings/#databases__

Voici un exemple de configuration pour utiliser une base MySQL : 
````
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'pod',
        'USER': 'pod',
        'PASSWORD': 'password',
        'HOST': 'mysql.univ.fr',
        'PORT': '3306',
        'OPTIONS': {
            'init_command': "SET storage_engine=INNODB, sql_mode='STRICT_TRANS_TABLES', innodb_strict_mode=1, foreign_key_checks = 1", 
         },
    }
}
````


### 2.3/ Langues

Par défaut, Esup-Pod est fournie en Francais et en anglais.
Vous pouvez tout à fait rajouter des langues comme vous le souhaitez. Il faudra pour cela créer un fichier de langue et traduire chaque entrée.

- LANGUAGE_CODE = "fr"

> Langue par défaut si non détectée


- LANGUAGES = (
    ('fr', 'Français'), ('en', 'English'))
)

> Langue disponible et traduite

### 2.4/ Gestion des fichiers

- USE_PODFILE = False

> Utiliser l'application de gestion de fichier fourni avec le projet.
> Si False, chaque fichier envoyé ne pourra être utilisé qu'une seule fois.

- FILE_UPLOAD_TEMP_DIR = "/var/tmp"

> Le répertoire dans lequel stocker temporairement les données (typiquement pour les fichiers plus grands que FILE_UPLOAD_MAX_MEMORY_SIZE) lors des téléversements de fichiers.<br>
> _ref: https://docs.djangoproject.com/fr/3.2/ref/settings/#file-upload-temp-dir_


- STATIC_ROOT = "/pod/static"

> Le chemin absolu vers le répertoire dans lequel collectstatic rassemble les fichiers statiques en vue du déploiement. Ce chemin sera précisé dans le fichier de configurtation du vhost nginx.<br>
> _ref: https://docs.djangoproject.com/fr/3.2/ref/settings/#std:setting-STATIC_ROOT_

- STATIC_URL = "/static/"

> prefix url utilisé pour accèder aux fichiers static


- STATICFILES_STORAGE = 'static_compress.CompressedStaticFilesStorage'

> Indique à django de compresser automatiquement les fichiers css/js les plus gros lors du collectstatic pour optimiser les tailles de requetes.<br>
> À combiner avec un réglage webserver ("gzip_static  on;" sur nginx)<br>
> _ref: https://github.com/whs/django-static-compress


- MEDIA_ROOT = "/pod/media"

> Chemin absolu du système de fichiers pointant vers le répertoire qui contiendra les fichiers téléversés par les utilisateurs.<br>
> Attention, ce répertoire doit exister<br>
> _ref: https://docs.djangoproject.com/fr/3.2/ref/settings/#std:setting-MEDIA_ROOT_

- MEDIA_URL = "/media/"

> prefix url utilisé pour accéder aux fichiers du répertoire media

- FILES_DIR = "files"

> Nom du répertoire racine où les fichiers "complémentaires"
> (hors vidéos etc.) sont téléversés. Notament utilisé par PODFILE

### 2.5/ Gestion du Cache

````
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    },
    # Persistent cache setup for select2 (NOT DummyCache or LocMemCache).
    "select2": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/2",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}
````

> A modifier principalement pour indiquer dans LOCATION votre serveur de cache si elle n'est pas sur la même machine que votre POD

### 2.6/ Gestion de l'application de recherche ElasticSearch

- ES_URL = ['http://127.0.0.1:9200/']

> adresse du ou des instances d'Elasticsearch utilisées pour l'indexation et la recherche de vidéo. Ne pas modifier si votre instance ElasticSearch est sur la même machine que votre POD

- ES_INDEX = "pod"

> Valeur pour l’index de ElasticSearch

- ES_TIMEOUT = 30

> Valeur timeout pour configuration de ElasticSearch

- ES_MAX_RETRIES = 10

> Valeur max essai pour configuration de ElasticSearch

- ES_VERSION = 6

> Version d'ElasticSearch
> valeurs possibles 6 ou 7 (pour indiquer utiliser ElasticSearch 6 ou 7)
> pour utiliser la version 7, faire une mise à jour du paquet elasticsearch-py
> elasticsearch==7.10.1
> https://elasticsearch-py.readthedocs.io/en/v7.10.1/

### 2.7/ Gestion de la page d'accueil et des menus


## 3/ Configuration par application

### 3.2/ Configuration application authentification

- AUTH_TYPE :
````
AUTH_TYPE = (
    ('local', _('local')),
    ('CAS', 'CAS'),
    ('OIDC', "OIDC"),
    ("Shibboleth", "Shibboleth")
)
````

> Type d'authentification possible sur votre instance.
>  Choix : local, CAS, OIDC, Shibboleth

- USE_CAS = False

> Activation de l'authentification CAS en plus de l'authentification locale

- CAS_SERVER_URL = "sso_cas"

> Url du serveur cas de l'établissement. Format http://url_cas

- CAS_GATEWAY = False

> Si True, authentifie automatiquement l'individu
> si déjà authentifié sur le serveur CAS

- POPULATE_USER = None

> Si utilisation de la connection CAS, renseigne les champs du compte
> de la personne depuis une source externe.
> Valeurs possibles :
>  - None (pas de renseignement),
>  - CAS (renseigne les champs depuis les informations renvoyées par le CAS),
>  - LDAP (Interroge le serveur LDAP pour renseigner les champs)

- AUTH_CAS_USER_SEARCH = "user"

> Variable utilisée pour trouver les informations de l'individu
> connecté dans le fichier renvoyé par le CAS lors de l'authentification

- USER_CAS_MAPPING_ATTRIBUTES :
````
USER_CAS_MAPPING_ATTRIBUTES = {
    "uid": "uid",
    "mail": "mail",
    "last_name": "sn",
    "first_name": "givenname",
    "affiliation": "eduPersonAffiliation",
    "groups": "memberOf"
}

````

> Liste de correspondance entre les champs d'un compte de Pod
> et les champs renvoyés par le CAS

- CREATE_GROUP_FROM_AFFILIATION = False

> Si True, des groupes sont créés automatiquement
> à partir des affiliations des individus qui se connectent sur la plateforme
> et l'individu qui se connecte est ajouté automatiquement à ces groupes

- CREATE_GROUP_FROM_GROUPS = False

> Si True, des groupes sont créés automatiquement
> à partir des groupes (attribut groups à memberOf)
> des individus qui se connectent sur la plateforme
> et l'individu qui se connecte est ajouté automatiquement à ces groupes

- AFFILIATION_STAFF = ('faculty', 'employee', 'staff')

> Les personnes ayant pour affiliation les valeurs
> renseignées dans cette variable ont automatiquement
> la valeur staff de leur compte à True

- AFFILIATION_EVENT = ['faculty', 'employee', 'staff']

> Groupes ou affiliations des personnes autorisées à créer un évènement

- AFFILIATION :
````
AFFILIATION = (
    ('student', _('student')),
    ('faculty', _('faculty')),
    ('staff', _('staff')),
    ('employee', _('employee')),
    ('member', _('member')),
    ('affiliate', _('affiliate')),
    ('alum', _('alum')),
    ('library-walk-in', _('library-walk-in')),
    ('researcher', _('researcher')),
    ('retired', _('retired')),
    ('emeritus', _('emeritus')),
    ('teacher', _('teacher')),
    ('registered-reader', _('registered-reader'))
)

````

> Valeurs possibles pour l'Affiliation du compte

- LDAP_SERVER = {'url': '', 'port': 389, 'use_ssl': False}

> Information de connection au serveur LDAP.
> Le champ url peut contenir une ou plusieurs url
>  pour ajouter des hôtes de référence, exemple :
> Si un seul host :
> {'url': "ldap.univ.fr'', 'port': 389, 'use_ssl': False}
> Si plusieurs :
> {'url': ("ldap.univ.fr'',"ldap2.univ.fr"), 'port': 389, 'use_ssl': False}

- AUTH_LDAP_BIND_DN = ""

> Identifiant (DN) du compte pour se connecter au serveur LDAP

- AUTH_LDAP_BIND_PASSWORD = ""

> Mot de passe du compte pour se connecter au serveur LDAP

- AUTH_LDAP_USER_SEARCH = ('ou=people,dc=univ,dc=fr', "(uid=%(uid)s)")

> Filtre LDAP permettant la recherche de l'individu dans le serveur LDAP
 
 - USER_LDAP_MAPPING_ATTRIBUTES :
````
USER_LDAP_MAPPING_ATTRIBUTES = {
    "uid": "uid",
    "mail": "mail",
    "last_name": "sn",
    "first_name": "givenname",
    "primaryAffiliation": "eduPersonPrimaryAffiliation",
    "affiliations": "eduPersonAffiliation",
    "groups": "memberOf"
}

````

> Liste de correspondance entre les champs d'un compte de Pod
> et les champs renvoyés par le LDAP

- USE_SHIB = False

> Mettre à True pour utiliser l'authentification Shibboleth

- SHIB_NAME = ""

> Nom de la fédération d'identité utilisée

- SHIBBOLETH_ATTRIBUTE_MAP : 
````
SHIBBOLETH_ATTRIBUTE_MAP = {
    "shib-user": (True, "username"),
    "shib-given-name": (True, "first_name"),
    "shib-sn": (True, "last_name"),
    "shib-mail": (False, "email"),
    "shib-primary-affiliation": (False, "affiliation"),
    "shib-unscoped-affiliation": (False, "affiliations"),
}
````

> Mapping des attributs entre shibboleth et la classe utilisateur

- SHIBBOLETH_STAFF_ALLOWED_DOMAINS = ('univ-domain.fr',)

> permettre à l'utilisateur d'un domaine d'être membre du personnel
> Si vide, tous les domaines seront autorisés

- REMOTE_USER_HEADER = "REMOTE_USER"

> Nom de l'attribut dans les headers qui sert à identifier
> l'utilisateur connecté avec Shibboleth

- SHIB_URL = ""

> URL de connexion à votre instance Shibboleth

- SHIB_LOGOUT_URL = ""

> URL de déconnexion à votre instance Shibboleth

- CAS_FORCE_LOWERCASE_USERNAME = False

> Forcer le passage en minuscule du nom d'utilisateur CAS
> (permet de prévenir des doubles créations de comptes dans certain cas).

- USE_OIDC = False

> Mettre à True pour utiliser l'authentification OpenID Connect

- OIDC_NAME = "" 
> Nom du Service Provider OIDC

- OIDC_RP_CLIENT_ID = os.environ('OIDC_CLIENT_ID')
- OIDC_RP_CLIENT_SECRET = os.environ('OIDC_CLIENT_SECRET')

> CLIENT_ID et CLIENT_SECRET de OIDC sont plutôt à positionner
> à travers des variables d'environnement

- OIDC_OP_AUTHORIZATION_ENDPOINT = "https://plm.math.cnrs.fr/sp/oauth/authorize"
- OIDC_OP_TOKEN_ENDPOINT = "https://plm.math.cnrs.fr/sp/oauth/token"
- OIDC_OP_USER_ENDPOINT = "https://plm.math.cnrs.fr/sp/oauth/userinfo"
- OIDC_RP_SIGN_ALGO = 'RS256'
- OIDC_OP_JWKS_ENDPOINT = "https://plm.math.cnrs.fr/sp/oauth/discovery/keys"

> Différents paramètres pour OIDC
> tant que mozilla_django_oidc n'accepte le mécanisme de discovery
> ref: https://github.com/mozilla/mozilla-django-oidc/pull/309

- OIDC_CLAIM_FAMILY_NAME = "family_name"
- OIDC_CLAIM_GIVEN_NAME = "given_name"

> Noms des Claim permettant de récupérer les attributs nom, prénom, email

- DEFAULT_AFFILIATION = ""

> Affiliation par défaut d'un utilisateur authentifié par OIDC.
> Ce contenu sera comparé à la liste AFFILIATION_STAFF pour déterminer si l'utilisateur doit être admin django

- ESTABLISHMENTS = ???

> A compléter

- GROUP_STAFF = AFFILIATION_STAFF

> utilisé dans populatedCasbackend

- HIDE_USERNAME = False

> Si valeur vaut 'True', le username de l'utilisateur ne sera pas visible sur la plate-forme Pod et si la valeur vaut 'False' le username sera affichés aux utilisateurs authentifiés. (par soucis du respect du RGPD)


### 3.2/ Configuration application video

- ACTIVE_VIDEO_COMMENT = True

> Activer les commentaires au niveau de la plateforme

- AUDIO_BITRATE = "192k"

- AUDIO_SPLIT_TIME = 300

> decoupage de l'audio pour la transcription

- CELERY_TO_ENCODE = False
- CELERY_BROKER_URL = "amqp://pod:xxx@localhost/rabbitpod"

> Utilisation de Celery pour la gestion des taches d'encodage

- CHANNEL_FORM_FIELDS_HELP_TEXT = ""

> Ensemble des textes d'aide affichés avec le formulaire d'édition de chaine.
> voir pod/video/forms.py

- CREATE_THUMBNAIL = ""

> ffmpeg command use to create thumbnail
> ffmpeg -i <video_input> -vf "fps=1/(%(duration)s/%(nb_thumbnail)s)" -vsync vfr "%(output)s_%%04d.png"

- CURSUS_CODES : 
````
CURSUS_CODES = (
    ('0', _("None / All")),
    ('L', _("Bachelor’s Degree")),
    ('M', _("Master’s Degree")),
    ('D', _("Doctorate")),
    ('1', _("Other"))
)
````
> Liste des cursus proposés lors de l'ajout des vidéos.
> Affichés en dessous d'une vidéos, ils sont aussi utilisés pour affiner la recherche.

- CURSUS_CODES_DICT = {}

> dictionnaire créé à partir de CURSUS_CODES

- DEFAULT_DC_COVERAGE = TITLE_ETB + " - Town - Country"

> couverture du droit pour chaque vidéo

- DEFAULT_DC_RIGHTS = "BY-NC-SA"

> droit par défaut affichés dans le flux RSS si non renseigné

- DEFAULT_TYPE_ID = 1

> Les vidéos créées sans type (par importation par exemple)seront affectées au type par défaut (en général, le type ayant pour identifiant '1' est 'Other')

- DEFAULT_YEAR_DATE_DELETE = 2

> Durée d'obsolescence par défaut (en années après la date d'ajout).

- EMAIL_ON_ENCODING_COMPLETION = True

> Si True, un courriel est envoyé aux managers et à l'auteur (si DEBUG est à False) à la fin de l'encodage

- EMAIL_ON_TRANSCRIPTING_COMPLETION = True

> Si True, un courriel est envoyé aux managers et à l'auteur (si DEBUG est à False) à la fin de transcription

- ENCODE_VIDEO = "start_encode"

> Fonction appelée pour lancer l'encodage des vidéos

- ENCODING_CHOICES:
````
ENCODING_CHOICES = (
    ("audio", "audio"),
    ("360p", "360p"),
    ("480p", "480p"),
    ("720p", "720p"),
    ("1080p", "1080p"),
    ("playlist", "playlist")
)
````
> Encodage possible sur la plateforme.
> Associé à un rendu dans le cas d'une vidéo.

- EXTRACT_SUBTITLE = '-map 0:%(index)s -f webvtt -y  "%(output)s" '

> commande ffmpeg utilisée pour extraire une piste de sous-titre d'une video

- EXTRACT_THUMBNAIL = = '-map 0:%(index)s -an -c:v copy -y  "%(output)s" '

> commande ffmpeg utilisée pour extraire une piste image d'une video

- FFMPEG = ?
- FFMPEG_CMD = "ffmpeg"

> commande utilisée pour lancer ffmpeg

- FFMPEG_CRF = 20 

> valeur par défaut du paramètre crf de ffmpeg

- FFMPEG_HLS_COMMON_PARAMS
````
FFMPEG_HLS_COMMON_PARAMS = (
    "-c:v %(libx)s -preset %(preset)s -profile:v %(profile)s -pix_fmt yuv420p "
    + "-level %(level)s -crf %(crf)s -sc_threshold 0 "
    + '-force_key_frames "expr:gte(t,n_forced*1)" '
    + "-c:a aac -ar 48000 -max_muxing_queue_size 4000 "
)
````

- FFMPEG_HLS_ENCODE_PARAMS
````
FFMPEG_HLS_ENCODE_PARAMS = (
    '-vf "scale=-2:%(height)s" -maxrate %(maxrate)s -bufsize %(bufsize)s -b:a:0 %(ba)s '
    + "-hls_playlist_type vod -hls_time %(hls_time)s  -hls_flags single_file "
    + '-master_pl_name "livestream%(height)s.m3u8" '
    + '-y "%(output)s" '
)
````

- FFMPEG_HLS_TIME = 2

> valeur par défaut du paramètre hls_time de ffmpeg

- FFMPEG_INPUT :
````
````

    - FFMPEG_LEVEL
    - FFMPEG_LIBX
    - FFMPEG_M4A_ENCODE
    - FFMPEG_MISC_PARAMS
    - FFMPEG_MP3_ENCODE
    - FFMPEG_MP4_ENCODE
    - FFMPEG_NB_THREADS
    - FFMPEG_PRESET
    - FFMPEG_PROFILE
    - FFMPEG_STATIC_PARAMS
    - FFPROBE
    - FILEPICKER
    - FORMAT_CHOICES
    - GET_DURATION_VIDEO
    - GET_INFO_VIDEO
    - LANG_CHOICES_DICT
    - LAUNCH_ENCODE_VIDEO
    - LICENCE_CHOICES
    - LICENCE_CHOICES_DICT
    - LOGO_SITE
    - MAX_D
    - MAX_DURATION_DATE_DELETE
    - NB_THUMBNAIL
    - NORMALIZE
    - NORMALIZE_TARGET_LEVEL
    - NOTES_STATUS
    - NOTE_ACTION
    - PREF_LANG_CHOICES
    - RESTRICT_EDIT_VIDEO_ACCESS_TO_STAFF_ONLY
    - SAMPLE_OVERLAP
    - SAMPLE_WINDOW
    - SENTENCE_BLANK_SPLIT_TIME
    - SENTENCE_MAX_LENGTH
    - STT_PARAM
    - TEMPLATE_VISIBLE_SETTINGS
    - THEME_ACTION
    - THEME_FORM_FIELDS_HELP_TEXT
    - THIRD_PARTY_APPS
    - THIRD_PARTY_APPS_CHOICES
    - THRESHOLD_UNVOICED
    - THRESHOLD_VOICED
    - TITLE_ETB
    - TITLE_SITE
    - TODAY
    - TRANSCRIPT
    - TRANSCRIPT_VIDEO
    - USE_CATEGORY
    - USE_ESTABLISHMENT
    - USE_OBSOLESCENCE
    - VAD_AGRESSIVITY
    - VERSION_CHOICES
    - VERSION_CHOICES_DICT
    - VIDEOS
    - VIDEOS_DIR
    - VIDEO_ALLOWED_EXTENSIONS
    - VIDEO_FORM_FIELDS
    - VIDEO_FORM_FIELDS_HELP_TEXT
    - VIDEO_MAX_UPLOAD_SIZE
    - VIDEO_RECENT_VIEWCOUNT
    - VIDEO_RENDITIONS
    - VIDEO_REQUIRED_FIELDS
    - VIEW_STATS_AUTH
    - WORDS_PER_LINE

### 3.3/ Application meeting
> Application Meeting pour la gestion de reunion avec BBB.
> Mettre USE_MEETING à True pour activer cette application.
> BBB_API_URL et BBB_SECRET_KEY sont obligatoires pour faire fonctionner l'application

- USE_MEETING = False

> Activer l'application meeting

- BBB_API_URL = ""

> Indiquer l'URL API de BBB par ex https://webconf.univ.fr/bigbluebutton/api

- BBB_SECRET_KEY = ""

> Clé de votre serveur BBB. Vous pouvez récupérer cette clé à l'aide de la commande bbb-conf --secret sur le serveur BBB

- BBB_LOGOUT_URL = ""

> Indiquer l'URL de retour au moment où vous quittez la réunion BBB. Ce champ est optionnel

- RESTRICT_EDIT_MEETING_ACCESS_TO_STAFF_ONLY = False

> Seuls les utilisateurs "staff" pourront éditer les réunions

- MEETING_DISABLE_RECORD = True

> Mettre à True pour désactiver les enregistrements de réunion

````
MEETING_RECORD_FIELDS = (
    "record",
    "auto_start_recording",
    "allow_start_stop_recording"
)
````

> Configuration de l'enregistrement des réunions. Ce champ n'est pas pris en compte si MEETING_DISABLE_RECORD = True

### 3.4/ Configuration application completion

- ACTIVE_MODEL_ENRICH = False

> Définissez à True pour activer la case à cocher dans l'édition des sous-titres.

- ALL_LANG_CHOICES = ()

> liste toutes les langues pour l'ajout de fichier de sous-titre
> voir le fichier pod/main/lang_settings.py

- DEFAULT_LANG_TRACK = "fr"

> langue par défaut pour l'ajout de piste à une vidéo

- KIND_CHOICES = (('subtitles', _('subtitles')), ('captions', _('captions')))

> Liste de type de piste possible pour une vidéo (sous-titre, légende etc.)

- LANG_CHOICES = (PREF_LANG_CHOICES + (('', '----------'),) + ALL_LANG_CHOICES)

> Liste des langues proposées lors de l'ajout des vidéos.
> Affichés en dessous d'une vidéos, les choix sont aussi utilisés pour affiner la recherche.

- LINK_SUPERPOSITION = False

> Si valeur vaut 'True', les URLs contenues dans le texte de superposition seront transformées, à la lecture de la vidéo, en lien cliquable.


- MODEL_COMPILE_DIR = "/path/of/project/Esup-Pod/compile-model"

> paramétrage des chemin du model pour la compilation
> Pour télécharger les Modeles : https://alphacephei.com/vosk/lm#update-process
> Ajouter le model dans les sous-dossier de la lang correspondants
> Exemple pour le français: /path/of/project/Esup-Pod/compile-model/fr/

- MODEL_PARAM :
````
MODEL_PARAM = {
    # le modèle stt
    'STT': {
        'fr': {
            'model': "/path/to/project/Esup-Pod/transcription/model_fr/stt/output_graph.tflite",
            'scorer': "/path/to/project/Esup-Pod/transcription/model_fr/stt/kenlm.scorer",
        }
    },
    # le modèle vosk
    'VOSK': {
        'fr': {
            'model': "/path/of/project/Esup-Pod/transcription/model_fr/vosk/vosk-model-fr-0.6-linto-2.2.0",
        }
    }
}
````
> paramétrage des modele. 
> Pour télécharger les Modeles Vosk : https://alphacephei.com/vosk/models

- PREF_LANG_CHOICES
````
PREF_LANG_CHOICES = (
    ("de", _("German")),
    ("en", _("English")),
    ("ar", _("Arabic")),
    ("zh", _("Chinese")),
    ("es", _("Spanish")),
    ("fr", _("French")),
    ("it", _("Italian")),
    ("ja", _("Japanese")),
    ("ru", _("Russian")),
)
````
> liste des langues affichées en premier dans les propositions de choix

- ROLE_CHOICES : 
````
ROLE_CHOICES = (
    ('actor', _('actor')),
    ('author', _('author')),
    ('designer', _('designer')),
    ('consultant', _('consultant')),
    ('contributor', _('contributor')),
    ('editor', _('editor')),
    ('speaker', _('speaker')),
    ('soundman', _('soundman')),
    ('director', _('director')),
    ('writer', _('writer')),
    ('technician', _('technician')),
    ('voice-over', _('voice-over')),
)
````
> Liste de rôle possible pour un contributeur

- TRANSCRIPTION_TYPE = "STT"

> STT ou VOSK

- USE_ENRICH_READY = False 

> voir ACTIVE_MODEL_ENRICH

### 3.5/ Configuration application live

- DEFAULT_EVENT_PATH = ""

> Chemin racine du répertoire où sont déposés temporairement les  enregistrements des évènements éffectués depuis POD pour convertion en ressource vidéo (VOD)

- DEFAULT_EVENT_THUMBNAIL = "/img/default-event.svg"

> Image par défaut affichée comme poster ou vignette, utilisée pour présenter l'évènement'.
> Cette image doit se situer dans le répertoire static.

- DEFAULT_EVENT_TYPE_ID = 1

> Type par défaut affecté à un évènement direct (en général, le type ayant pour identifiant '1' est 'Other')

- DEFAULT_THUMBNAIL = "img/default.svg"

> Image par défaut affichée comme poster ou vignette,  utilisée pour présenter la vidéo.
> Cette image doit se situer dans le répertoire static.

- EMAIL_ON_EVENT_SCHEDULING = True

> Si True, un courriel est envoyé aux managers et à l'auteur (si DEBUG est à False) à la création/modification d'un event.

- EVENT_ACTIVE_AUTO_START = False

> Permet de lancer automatiquement l'enregistrement sur l'interface utilisée (wowza, ) sur le broadcaster et spécifié par  BROADCASTER_PILOTING_SOFTWARE

- EVENT_GROUP_ADMIN = "event admin"

> Permet de préciser le nom du groupe dans lequel les utilisateurs  peuvent planifier un évènement sur plusieurs jours

- HEARTBEAT_DELAY = 45

> Temps (en seconde) entre deux envois d'un signal au serveur, pour signaler la présence sur un live.
> Peut être augmenté en cas de perte de performance mais au détriment de la qualité du comptage des valeurs

- USE_BBB = True

> Utilisation de BigBlueButton

- USE_BBB_LIVE = False 

> Utilisation du système de diffusion de Webinaires en lien avec BigBlueButton


### 3.X/ Activer le studio Opencast dans Pod

- USE_OPENCAST_STUDIO = False

> Activer l'utilisation du studio Opencast

- OPENCAST_FILES_DIR = "opencast-files"

> Permet de spécifier le dossier de stockage des enregistrements du studio avant traitement.

- OPENCAST_DEFAULT_PRESENTER = "mid"

> Permet de spécifier la valeur par défaut du placement de la vidéo du
> presenteur par rapport à la vidéo de présentation (écran)
> les valeurs possibles sont :
>  * "mid" (écran et caméra ont la même taille)
>  * "piph" (le presenteur, caméra, est incrusté dans la vidéo de présentation, en haut à droite)
>  * "pipb" (le presenteur, caméra, est incrusté dans la vidéo de présentation, en bas à droite)

````
OPENCAST_MEDIAPACKAGE = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <mediapackage xmlns="http://mediapackage.opencastproject.org" id="" start="">
    <media/>
    <metadata/>
    <attachments/>
    <publications/>
    </mediapackage>"""
````

> Contenu par défaut du fichier xml pour créer le mediapackage pour le studio.
> Ce fichier va contenir toutes les spécificités de l'enregistrement
> (source, cutting, title, presenter etc.)

## 4/ Commande de gestion de l'application
### 4.1/ Creation d'un super utilisateur
_
