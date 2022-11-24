# Configuration de la plateforme Esup-Pod

## 1/ Information

La plateforme Esup-Pod se base sur le framework Django écrit en Python. Elle supporte les versions 3.7 3.8 et 3.9 de Python

**Django Version : 3.2 LTS** 

> La documentation compléte du framework : https://docs.djangoproject.com/fr/3.2/ (ou https://docs.djangoproject.com/en/3.2/)<br>
> L'Ensemble des variables de configuration du framework est accessible à cette adresse : https://docs.djangoproject.com/fr/3.2/ref/settings/

## 2/ Configuration Générale de la plateforme Esup_Pod


- SITE_ID = 1

> _Valeur par défaut : 1_<br>
> L’identifiant (nombre entier) du site actuel. Peut être utilisé pour mettre en place une instance multi-tenant et ainsi gérer dans une même base de données du contenu pour plusieurs sites.<br>
> __ref : https://docs.djangoproject.com/fr/3.2/ref/settings/#site-id__


- SECRET_KEY = 'A_CHANGER'

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

ALLOWED_HOSTS = ['localhost']

> _Valeur par défaut :  ['localhost']_<br>
> Une liste de chaînes représentant des noms de domaine/d’hôte que ce site Django peut servir.<br>
> C’est une mesure de sécurité pour empêcher les attaques d’en-tête Host HTTP, qui sont possibles même avec bien des configurations de serveur Web apparemment sécurisées.<br>
> __ref: https://docs.djangoproject.com/fr/3.2/ref/settings/#allowed-hosts__


- SESSION_COOKIE_AGE = 14400

> _Valeur par défaut :  14400 (secondes, soit 4 heures)_<br>
> L’âge des cookies de sessions, en secondes.<br>
> __ref: https://docs.djangoproject.com/fr/3.2/ref/settings/#session-cookie-age__


- SESSION_EXPIRE_AT_BROWSER_CLOSE = True

> _Valeur par défaut :  True_<br>
> Indique s’il faut que la session expire lorsque l’utilisateur ferme son navigateur.<br>
> __*ref: https://docs.djangoproject.com/fr/3.2/ref/settings/#session-cookie-age*__


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


### 1.1/ Courriel


- CONTACT_US_EMAIL

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


### 1.2/ Base de données


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


### 1.3/ Langues

Par défaut, Esup-Pod est fournie en Francais et en anglais.

Vous pouvez tout à fait rajouter des langues comme vous le souhaitez. Il faudra pour cela créer un fichier de langue et traduire chaque entrée.


- LANGUAGE_CODE = "fr"

> Langue par défaut si non détectée


- LANGUAGES = (
    ('fr', 'Français'), ('en', 'English'))
)

> Langue disponible et traduite

### 1.4/ Gestion des fichiers

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


## 3/ Configuration par application

## 4/ Commande de gestion de l'application

### 4.1/ Creation d'un super utilisateur
_
