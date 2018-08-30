# Configuration de la plateforme

**<span style="color:green">Les variables suivantes sont utilisées par la plateforme pour son fonctionnement. Leurs valeurs peuvent être changées dans votre fichier de configuration :</span>**

```console
(django_pod) pod@pod:/usr/local/django_projects/podv2$ vim pod/custom/settings_local.py
```

*La documentation suivante précise pour chaque variable son nom, son usage et sa valeur par défaut.*

## Configuration principale

| Property            | Description                                                                                                                          |   Default Value  |
|---------------------|--------------------------------------------------------------------------------------------------------------------------------------|:----------------:|
| **SECRET_KEY**           | La clé secrète d’une installation Django. Elle est utilisée dans le contexte de la signature cryptographique, et doit être définie à une valeur unique et non prédictible. https://docs.djangoproject.com/fr/1.11/ref/settings/#secret-key | 'A_CHANGER' |
| **DEBUG**           | Une valeur booléenne qui active ou désactive le mode de débogage. **Ne déployez jamais de site en production avec le réglage DEBUG activé.** https://docs.djangoproject.com/fr/1.11/ref/settings/#debug | True |
| **ALLOWED_HOSTS**           | Une liste de chaînes représentant des noms de domaine/d’hôte que ce site Django peut servir. C’est une mesure de sécurité pour empêcher les attaques d’en-tête Host HTTP, qui sont possibles même avec bien des configurations de serveur Web apparemment sécurisées. https://docs.djangoproject.com/fr/1.11/ref/settings/#allowed-hosts | ['localhost'] |
| **`SESSION_COOKIE_AGE`**      | L’âge des cookies de sessions, en secondes. https://docs.djangoproject.com/fr/1.11/ref/settings/#session-cookie-age | 14400 |
| **`SESSION_EXPIRE_AT_BROWSER_CLOSE`**           | Indique s’il faut que la session expire lorsque l’utilisateur ferme son navigateur. https://docs.djangoproject.com/fr/1.11/ref/settings/#session-cookie-age | True |
| **ADMINS**           | Une liste de toutes les personnes qui reçoivent les notifications d’erreurs dans le code. Lorsque DEBUG=False et qu’une vue lève une exception, Django envoie un courriel à ces personnes contenant les informations complètes de l’exception. Chaque élément de la liste doit être un tuple au format « (nom complet, adresse électronique) ». Exemple : ```[('John', 'john@example.com'), ('Mary', 'mary@example.com')]``` Dans Pod, les "admins" sont également destinataires des courriels de contact, d'encodage ou de flux rss si la variable `CONTACT_US_EMAIL` n'est pas renseignée. | ( ('Name', 'adminmail@univ.fr'),) |
| **MANAGERS**           | Dans Pod, les "managers" sont destinataires des courriels de fin d'encodage (et ainsi des vidéos déposées sur la plateforme). Le premier managers renseigné est également contact des flus rss. Ils sont aussi destinataires des courriels de contact si la variable `CONTACT_US_EMAIL` n'est pas renseignée. | ADMINS |
| **DATABASES**           | Un dictionnaire contenant les réglages de toutes les bases de données à utiliser avec Django. C’est un dictionnaire imbriqué dont les contenus font correspondre l’alias de base de données avec un dictionnaire contenant les options de chacune des bases de données. https://docs.djangoproject.com/fr/1.11/ref/settings/#databases |  <div style="text-align: left">{    <br/>'default': {<br/>        'ENGINE': 'django.db.backends.sqlite3',<br/>        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),<br/>    }<br/>} </div>|
| **LANGUAGE_CODE**           | Langue par défaut si non détectée | fr |
| **LANGUAGES**           | Langue disponible et traduite | <div style="text-align: left">(    ('fr', 'Français'),    ('en', 'English'),    ('nl', 'Dutch (Netherlands)'))</div> |
| **TIME_ZONE**           | Une chaîne représentant le fuseau horaire pour cette installation. https://docs.djangoproject.com/fr/1.11/ref/settings/#std:setting-TIME_ZONE | UTC |
| **`FILE_UPLOAD_TEMP_DIR`**           | Le répertoire dans lequel stocker temporairement les données (typiquement pour les fichiers plus grands que FILE_UPLOAD_MAX_MEMORY_SIZE) lors des téléversements de fichiers. https://docs.djangoproject.com/fr/1.11/ref/settings/#file-upload-temp-dir | /var/tmp |
| **STATIC_ROOT**           |  Le chemin absolu vers le répertoire dans lequel collectstatic rassemble les fichiers statiques en vue du déploiement. https://docs.djangoproject.com/fr/1.11/ref/settings/#std:setting-STATIC_ROOT | <repertoire d'installation>/pod/static |
| **MEDIA_ROOT**           | Chemin absolu de système de fichiers pointant vers le répertoire qui contiendra les fichiers téléversés par les utilisateurs.  https://docs.djangoproject.com/fr/1.11/ref/settings/#std:setting-MEDIA_ROOT | <repertoire d'installation>/pod/media |
| **EMAIL_HOST**           | nom du serveur smtp | smtp.univ.fr |
| **EMAIL_PORT**           | port d'écoute du serveur smtp | 25 |
| **SERVER_EMAIL**           | courriel utilisé par défaut pour les envois automatique (erreur de code etc.) | noreply@univ.fr |
| **`DEFAULT_FROM_EMAIL`**           | courriel utilisé par défaut pour les envois de courriel (contact, encodage etc.) | noreply@univ.fr |
| **`MENUBAR_HIDE_INACTIVE_OWNERS`**           | Les utilisateurs inactif ne sont plus affichés dans la barre de menu utilisateur | True |
| **`MENUBAR_SHOW_STAFF_OWNERS_ONLY`**           | Les utilisateurs non staff ne sont plus affichés dans la barre de menu utilisateur | False |
| **`HOMEPAGE_SHOWS_PASSWORDED`**           | Afficher les vidéos dont l'accès est protégé par mot de passe sur la page d'accueil | False |
| **`HOMEPAGE_SHOWS_RESTRICTED`**           | Afficher les vidéos dont l'accès est protégé par authentification sur la page d'accueil | False |
| **`FORCE_LOWERCASE_TAGS`**           | Les mots clés saisis lors de l'ajout de vidéo sont convertis automatiquement en minuscule | True |
| **`MAX_TAG_LENGTH`**           | Les mots clés saisis lors de l'ajout de vidéo ne peuvent dépassé la longueur saisie | 50 |
| **`USE_PODFILE`**           | Utiliser l'application de gestion de fichier fourni avec le projet. Si False, chaque fichier envoyé ne pourra être utilisé qu'une seule fois. | False |
| **`THIRD_PARTY_APPS`**           | Liste des applications tierces accessibles. |[] |
| **`FILES_DIR`**           | Nom du répertoire racine ou les fichiers "complémentaires" (hors videos etc.) sont téléversés. | files |
| **`SUBJECT_CHOICES `**           | Choix de sujet pour les courriels envoyés depuis la plateforme | (        ('', '-----'),        ('info', _('Request more information')),        ('contribute', _('Learn more about how to contribute')),        ('request_password', _('Password request for a video')),        ('inappropriate_content', _('Report inappropriate content')),        ('bug', _('Correction or bug report')),        ('other', _('Other (please specify)'))    ) |


## Configuration des templates / de l'affichage

L'ensemble des variables ci-après doivent être contnu dans un dictionnnaire `TEMPLATE_VISIBLE_SETTINGS`.

Voici sa valeur par défaut :

```python
TEMPLATE_VISIBLE_SETTINGS = {
    'TITLE_SITE': 'Pod',
    'TITLE_ETB': 'University name',
    'LOGO_SITE': 'img/logoPod.svg',
    'LOGO_ETB': 'img/logo_etb.svg',
    'LOGO_PLAYER': 'img/logoPod.svg',
    'LINK_PLAYER': '',
    'FOOTER_TEXT': ('',),
    'FAVICON': 'img/logoPod.svg',
    'CSS_OVERRIDE' : ''
}

```

| Property            | Description                                                                                                                          |   Default Value  |
|---------------------|--------------------------------------------------------------------------------------------------------------------------------------|:----------------:|
| **`TITLE_SITE`**           | Titre du site. | 'Pod' |
| **`TITLE_ETB`**           | Titre de l'etablissement. | 'University name' |
| **`LOGO_SITE`**           | Logo affiché en haut à gauche sur toutes les pages. Doit se situer dans le répertoire static | 'img/logoPod.svg' |
| **`LOGO_ETB`**           | Logo affiché dans le footer sur toutes les pages. Doit se situer dans le répertoire static | 'img/logo_etb.svg' |
| **`LOGO_PLAYER`**           | Logo affiché sur le player video. Doit se situer dans le répertoire static | 'img/logoPod.svg' |
| **`LINK_PLAYER`**           | Lien de destination du logo affiché sur le player | '' |
| **`FOOTER_TEXT `**           | Texte affiché dans le footer. Une ligne par entrée, accepte du code html. Par exmple : (       '42, rue Paul Duez',       '59000 Lille - France',       ('&lt;a href="https://goo.gl/maps/AZnyBK4hHaM2"'        ' target="_blank"&gt;Google maps&lt;/a&gt;')   ) | ('',) |
| **`FAVICON `**           | Icon affiché dans la barre d'adresse du navigateur | 'img/logoPod.svg' |
| **`CSS_OVERRIDE `**           | Si souhaitée, à créer et sauvegarder dans le répertoire static de 'lapplciation custom et préciser le chemin d'accès. Par exemple : "custom/etab.css" | '' |


## Configuration application recherche

| Property            | Description                                                                                                                          |   Default Value  |
|---------------------|--------------------------------------------------------------------------------------------------------------------------------------|:----------------:|
| **`ES_URL`**           | adresse du ou des instances d'Elasticsearch utilisées pour l'indexation et la recherche de vidéo. | ['http://127.0.0.1:9200/'] |


## Configuration encodage
| Property            | Description                                                                                                                          |   Default Value  |
|---------------------|--------------------------------------------------------------------------------------------------------------------------------------|:----------------:|
| **`FFMPEG`**           | commande ffmpeg | ffmpeg |
| **`FFPROBE`**           | commande ffprobe | ffprobe |
| **`SEGMENT_TARGET_DURATION `**           | durée en seconde des segment HLS | 2 |
| **`RATE_MONITOR_BUFFER_RATIO `**           | la taille du buffer est égale au bitrate vidéo du rendu multiplié par cette valeur | 2 |
| **`FFMPEG_NB_THREADS `**           | nombre de thread possible pour ffmpeg (0 égale maximum possible) | 0 |
| **`GET_INFO_VIDEO `**           | Commande utilisée pour récupérer les informations de la première piste video du fichier envoyé | "%(ffprobe)s -v quiet -show_format -show_streams -select_streams v:0 -print_format json -i %(source)s" |
| **`GET_INFO_AUDIO `**           | Commande utilisée pour récupérer les informations de la première piste audio du fichier envoyé | "%(ffprobe)s -v quiet -show_format -show_streams -select_streams a:0 -print_format json -i %(source)s" |
| **`FFMPEG_STATIC_PARAMS `**           | paramètres de la commande ffmpeg utilisés pour encoder toutes les vidéos, peu importe le rendu | " -c:a aac -ar 48000 -c:v h264 -profile:v high -pix_fmt yuv420p -crf 20 -sc_threshold 0 -force_key_frames \"expr:gte(t,n_forced*1)\" -deinterlace -threads %(nb_threads)s " |
| **`FFMPEG_MISC_PARAMS `**           | autres paramètres qui sont placés au début de la commande | " -hide_banner -y " |
| **`AUDIO_BITRATE `**           | bitrate audio pour l'encodage M4A (encodage des fichiers audio envoyés sur la plateforme) | 192k |
| **`ENCODING_M4A `**           | commande utilisée pour l'encodage des fichiers audio envoyés sur la plateforme | %(ffmpeg)s -i %(source)s %(misc_params)s -c:a aac -b:a %(audio_bitrate)s -vn -threads %(nb_threads)s \"%(output_dir)s/audio_%(audio_bitrate)s.m4a\" |
| **`ENCODE_MP3_CMD `**           | commande utilisée pour l'encodage audio pour tous les fichiers envoyés sur la plateforme | "%(ffmpeg)s -i %(source)s %(misc_params)s -vn -b:a %(audio_bitrate)s -vn -f mp3 -threads %(nb_threads)s \"%(output_dir)s/audio_%(audio_bitrate)s.mp3\"" |
| **`EMAIL_ON_ENCODING_COMPLETION `**           | Si True, un courriel est envoyé aux managers et à l'auteur (si DEBUG est à True) à la fin de l'encodage | True |
| **`FILE_UPLOAD_TEMP_DIR `**           | Répertoire temporaire pour la création des thumbnails | '/tmp' |
| **`CELERY_TO_ENCODE `**           | Utilisation de Celery pour la gestion des taches d'encodage | False |


## Configuration flux RSS
| Property            | Description                                                                                                                          |   Default Value  |
|---------------------|--------------------------------------------------------------------------------------------------------------------------------------|:----------------:|
| **`DEFAULT_DC_COVERAGE`**           | couverture du droit pour chaque vidéo | TITLE_ETB + " - Town - Country" |
| **`DEFAULT_DC_RIGHTS`**           | droit par défaut affichés dans le flux RSS si non renseigné | "BY-NC-SA" |


## Configuration application vidéo
| Property            | Description                                                                                                                          |   Default Value  |
|---------------------|--------------------------------------------------------------------------------------------------------------------------------------|:----------------:|
| **`RESTRICT_EDIT_VIDEO_ACCESS_TO_STAFF_ONLY`**           | Si True, seule les personnes "Staff" peuvent déposer des vidéos sur la plateforme | False |
| **`DEFAULT_THUMBNAIL`**           | image par défaut affichée comme poster ou vignette, utilisée pour présenter la vidéo. Cette image doit se situer dans le répertoire static. | 'img/default.png' |
| **`ENCODING_CHOICES`**           | Encodage possible sur la plateforme. Associé à un rendu dans le cas d'une vidéo. | (        ("audio", "audio"),        ("360p", "360p"),        ("480p", "480p"),        ("720p", "720p"),        ("1080p", "1080p"),        ("playlist", "playlist")    ) |
| **`FORMAT_CHOICES`**           | Format d'encodage réalisé sur la plateforme. | (        ("video/mp4", 'video/mp4'),        ("video/mp2t", 'video/mp2t'),        ("video/webm", 'video/webm'),        ("audio/mp3", "audio/mp3"),        ("audio/wav", "audio/wav"),        ("application/x-mpegURL", application/x-mpegURL"),    ) |
| **`LICENCE_CHOICES`**           | Licence proposées pour les vidéos. | (       ('by', _("Attribution 4.0 International (CC BY 4.0)")),       ('by-nd', _("Attribution-NoDerivatives 4.0 "                   "International (CC BY-ND 4.0)"                   )),       ('by-nc-nd', _(           "Attribution-NonCommercial-NoDerivatives 4.0 "           "International (CC BY-NC-ND 4.0)"       )),       ('by-nc', _("Attribution-NonCommercial 4.0 "                   "International (CC BY-NC 4.0)")),       ('by-nc-sa', _(           "Attribution-NonCommercial-ShareAlike 4.0 "           "International (CC BY-NC-SA 4.0)"       )),       ('by-sa', _(           "Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)"))   ) |
| **`DEFAULT_TYPE_ID`**           | Les vidéos créées sans type (par importation par exemple) seront affectées au type par défaut (en général, le type ayant pour identifiant '1' est 'Other') | 1 |
| **`CURSUS_CODES`**           | Liste des cursus proposés lors de l'ajout des vidéos. Affichés en dessous d'une vidéos, ils sont aussi utilisés pour affiner la recherche. | (       ('0', _("None / All")),       ('L', _("Bachelor’s Degree")),       ('M', _("Master’s Degree")),       ('D', _("Doctorate")),       ('1', _("Other"))   ) |
| **`LANG_CHOICES`**           | Liste des langues proposées lors de l'ajout des vidéos. Affichés en dessous d'une vidéos, ils sont aussi utilisés pour affiner la recherche. | (       settings.PREF_LANG_CHOICES       + (('', '----------'),)       + settings.ALL_LANG_CHOICES   ) |
| **`VIDEOS_DIR`**           | Répertoire par défaut pour le téléversement des vidéos. | videos |
| **`ENCODE_VIDEO`**           | Fonction appelée pour lancer l'encodage des vidéos | start_encode |
| **`VIDEO_ALLOWED_EXTENSIONS `**           | Extension autorisée pour le téléversement sur la plateforme | (       '3gp',       'avi',       'divx',       'flv',       'm2p',       'm4v',       'mkv',       'mov',       'mp4',       'mpeg',       'mpg',       'mts',       'wmv',       'mp3',       'ogg',       'wav',       'wma'   ) |
| **`VIDEO_MAX_UPLOAD_SIZE `**           | Taille maximum en Go des fichiers téléversés sur la plateforme | 1 |
| **`VIDEO_FORM_FIELDS_HELP_TEXT `**           | Ensemble des textes d'aide affichés avec le formulaire d'envoi de vidéo | voir pod/video/forms.py |
| **`VIDEO_FORM_FIELDS `**           | Liste des champs du formulaire d'édition de vidéos affichés | `__all__` |
| **`CHANNEL_FORM_FIELDS_HELP_TEXT `**           | Ensemble des textes d'aide affichés avec le formulaire d'édition de chaine. | voir pod/video/forms.py |
| **`THEME_FORM_FIELDS_HELP_TEXT `**           | Ensemble des textes d'aide affichés avec le formulaire d'édition de theme. | voir pod/video/forms.py |



## Configuration application recorder (enregistreur)
| Property            | Description                                                                                                                          |   Default Value  |
|---------------------|--------------------------------------------------------------------------------------------------------------------------------------|:----------------:|
| **`RECORDER_TYPE`**           | Type d'enregistrement géré par la plateforme. Un enregistreur ne peut déposer que des fichier de type proposé par la plateforme. Le traitement se fait en fonction du type de fichier déposé. | (        ('video', _('Video')),        ('audiovideocast', _('Audiovideocast')),    ) |
| **`DEFAULT_RECORDER_PATH`**           | Chemin du répertoire où sont déposés les enregistrements (chemin du serveur FTP) | "/data/ftp-pod/ftp/" |
| **`DEFAULT_RECORDER_USER_ID`**           | Identifiant du propriétaire par défaut (si non spécifié) des enregistrements déposés | 1 |

## Configuration application podfile (gestion de fichier)
| Property            | Description                                                                                                                          |   Default Value  |
|---------------------|--------------------------------------------------------------------------------------------------------------------------------------|:----------------:|
| **`FILE_ALLOWED_EXTENSIONS`**           | Extensions autorisées pour les documents téléversés dans le gestionnaire de fichier | (        'doc',        'docx',        'odt',        'pdf',        'xls',        'xlsx',        'ods',        'ppt',        'pptx',        'txt',        'html',        'htm',        'vtt',        'srt',    ) |
| **`IMAGE_ALLOWED_EXTENSIONS`**           | Extensions autorisées pour les images téléversés dans le gestionnaire de fichier | (        'jpg',        'jpeg',        'bmp',        'png',        'gif',        'tiff',    ) |
| **`FILE_MAX_UPLOAD_SIZE`**           | Poids maximum en Mo par fichier téléversé dans le gestionnaire de fichier | 10 |

## Configuration application completion (contributeur, sous-titre, document à télécharger, superposition)
| Property            | Description                                                                                                                          |   Default Value  |
|---------------------|--------------------------------------------------------------------------------------------------------------------------------------|:----------------:|
| **`ROLE_CHOICES`**           | Liste de rôle possible pour un contributeur | (        ('actor', _('actor')),        ('author', _('author')),        ('designer', _('designer')),        ('consultant', _('consultant')),        ('contributor', _('contributor')),        ('editor', _('editor')),        ('speaker', _('speaker')),        ('soundman', _('soundman')),        ('director', _('director')),        ('writer', _('writer')),        ('technician', _('technician')),        ('voice-over', _('voice-over')),    ) |
| **`KIND_CHOICES`**           | Liste de type de piste possible pour une vidéo (sous-titre, légende etc.) | (        ('subtitles', _('subtitles')),        ('captions', _('captions')),    ) |

## Configuration application authentification (Local, CAS et LDAP)
| Property            | Description                                                                                                                          |   Default Value  |
|---------------------|--------------------------------------------------------------------------------------------------------------------------------------|:----------------:|


