
# Configuration de la plateforme Esup-Pod 


## Information générale 


La plateforme Esup-Pod se base sur le framework Django écrit en Python.<br>
Elle est compatible avec les versions 3.8, 3.9 et 3.10 de Python.<br>

**Django Version : 3.2 LTS**<br>

> La documentation complète du framework : [https://docs.djangoproject.com/fr/3.2/]() (ou [https://docs.djangoproject.com/en/3.2/]())<br><br>
> L’ensemble des variables de configuration du framework est accessible à cette adresse : [https://docs.djangoproject.com/fr/3.2/ref/settings/]()<br>

Voici les configurations des applications tierces utilisées par Esup-Pod.<br>


 - `CAS`

  > valeur par défaut : `1.5.2`

  >> Système d’authentification SSO_CAS <br>
  >> [https://github.com/kstateome/django-cas]() <br>

 - `ModelTransalation`

  > valeur par défaut : `0.18.7`

  >> L’application modeltranslation est utilisée pour traduire le contenu dynamique des modèles Django existants <br>
  >> [https://django-modeltranslation.readthedocs.io/en/latest/installation.html#configuration]() <br>

 - `captcha`

  > valeur par défaut : `0.5.17`

  >> Gestion du captcha du formulaire de contact <br>
  >> [https://django-simple-captcha.readthedocs.io/en/latest/usage.html]() <br>

 - `chunked_upload`

  > valeur par défaut : `2.0.0`

  >> Envoi de fichier par morceaux // voir pour mettre à jour si nécessaire <br>
  >> [https://github.com/juliomalegria/django-chunked-upload]() <br>

 - `ckeditor`

  > valeur par défaut : `6.3.0`

  >> Application permettant d’ajouter un éditeur CKEditor dans certains champs <br>
  >> [https://django-ckeditor.readthedocs.io/en/latest/#installation]() <br>

 - `django_select2`

  > valeur par défaut : `latest`

  >> Recherche et completion dans les formulaires <br>
  >> [https://django-select2.readthedocs.io/en/latest/]() <br>

 - `honeypot`

  > valeur par défaut : `1.0.3`

  >> Utilisé pour le formulaire de contact de Pod - ajoute un champ caché pour diminuer le spam <br>
  >> [https://github.com/jamesturk/django-honeypot/]() <br>

 - `mozilla_django_oidc`

  > valeur par défaut : `3.0.0`

  >> Système d’authentification OpenID Connect <br>
  >> [https://mozilla-django-oidc.readthedocs.io/en/stable/installation.html]() <br>

 - `pwa`

  > valeur par défaut : `1.1.0`

  >> Mise en place du mode PWA grâce à l'application Django-pwa <br>
  >> Voici la configuration par défaut pour Pod, vous pouvez surcharger chaque variable dans votre fichier de configuration. <br>
  >> PWA_APP_NAME = "Pod" <br>
  >> PWA_APP_DESCRIPTION = _( <br>
  >>     "Pod is aimed at users of our institutions, by allowing the publication of " <br>
  >>     "videos in the fields of research (promotion of platforms, etc.), training " <br>
  >>     "(tutorials, distance training, student reports, etc.), institutional life (video " <br>
  >>     "of events), offering several days of content." <br>
  >> ) <br>
  >> PWA_APP_THEME_COLOR = "#0A0302" <br>
  >> PWA_APP_BACKGROUND_COLOR = "#ffffff" <br>
  >> PWA_APP_DISPLAY = "standalone" <br>
  >> PWA_APP_SCOPE = "/" <br>
  >> PWA_APP_ORIENTATION = "any" <br>
  >> PWA_APP_START_URL = "/" <br>
  >> PWA_APP_STATUS_BAR_COLOR = "default" <br>
  >> PWA_APP_DIR = "ltr" <br>
  >> PWA_APP_LANG = "fr-FR" <br>
  >> Pour en savoir plus : [https://github.com/silviolleite/django-pwa]() <br>

 - `rest_framework`

  > valeur par défaut : `3.14.0`

  >> version 3.14.0: mise en place de l’API rest pour l’application <br>
  >> [https://www.django-rest-framework.org/]() <br>

 - `shibboleth`

  > valeur par défaut : `latest`

  >> Système d’authentification Shibboleth <br>
  >> [https://github.com/Brown-University-Library/django-shibboleth-remoteuser]() <br>

 - `sorl.thumbnail`

  > valeur par défaut : `12.9.0`

  >> Utilisée pour la génération de miniature des images <br>
  >> [https://sorl-thumbnail.readthedocs.io/en/latest/reference/settings.html]() <br>

 - `tagging`

  > valeur par défaut : `0.5.0`

  >> Gestion des mots-clés associés à une vidéo // voir pour référencer une nouvelle application <br>
  >> [https://django-tagging.readthedocs.io/en/develop/#settings]() <br>

## Configuration Générale de la plateforme Esup_Pod 


### Base de données

 - `DATABASES`

  > valeur par défaut :

  ```python
  {
      'default': {
          'ENGINE': 'django.db.backends.sqlite3',
          'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
      }
  }
  ```

  >> Un dictionnaire contenant les réglages de toutes les bases de données à utiliser avec Django. <br>
  >> C’est un dictionnaire imbriqué dont les contenus font correspondre l’alias de base de données avec un dictionnaire contenant les options de chacune des bases de données. <br>
  >> __ref: [https://docs.djangoproject.com/fr/3.2/ref/settings/#databases]()__ <br>
  >> valeur par défaut : une base de données au format sqlite <br>
  >> Voici un exemple de configuration pour utiliser une base MySQL : <br>
  >>
  >> ```
  >> DATABASES = { 
  >>     'default': { 
  >>         'ENGINE': 'django.db.backends.mysql', 
  >>         'NAME': 'pod', 
  >>         'USER': 'pod', 
  >>         'PASSWORD': 'password', 
  >>         'HOST': 'mysql.univ.fr', 
  >>         'PORT': '3306', 
  >>         'OPTIONS': { 
  >>             'init_command': "SET storage_engine=INNODB, sql_mode='STRICT_TRANS_TABLES', innodb_strict_mode=1, foreign_key_checks = 1", 
  >>          }, 
  >>     } 
  >> } 
  >>
  >> ```

### Courriel

 - `CONTACT_US_EMAIL`

  > valeur par défaut : ``

  >> Liste des adresses destinataires des courriels de contact <br>

 - `CUSTOM_CONTACT_US`

  > valeur par défaut : `False`

  >> Si 'True', les e-mails de contacts seront adressés, selon le sujet, <br>
  >> soit au propriétaire de la vidéo soit au(x) manager(s) des vidéos Pod. <br>
  >> (voir `USER_CONTACT_EMAIL_CASE` et `USE_ESTABLISHMENT_FIELD`) <br>

 - `DEFAULT_FROM_EMAIL`

  > valeur par défaut : `noreply`

  >> Expediteur par défaut pour les envois de courriel (contact, encodage etc.) <br>

 - `EMAIL_HOST`

  > valeur par défaut : `smtp.univ.fr`

  >> nom du serveur smtp  <br>
  >> _ref: [https://docs.djangoproject.com/fr/3.2/ref/settings/#email-host]()_ <br>

 - `EMAIL_PORT`

  > valeur par défaut : `25`

  >> Port d’écoute du serveur SMTP. <br>

 - `EMAIL_SUBJECT_PREFIX`

  > valeur par défaut : ``

  >> Préfixe par défaut pour l’objet des courriels. <br>

 - `SERVER_EMAIL`

  > valeur par défaut : `noreply`

  >> Expediteur par défaut pour les envois automatique (erreur de code etc.) <br>

 - `SUBJECT_CHOICES`

  > valeur par défaut : `()`

  >> Choix de sujet pour les courriels envoyés depuis la plateforme <br>
  >>
  >> ```
  >> SUBJECT_CHOICES = ( 
  >>     ('', '-----'), 
  >>     ('info', ('Request more information')), 
  >>     ('contribute', ('Learn more about how to contribute')), 
  >>     ('request_password', ('Password request for a video')), 
  >>     ('inappropriate_content', ('Report inappropriate content')), 
  >>     ('bug', ('Correction or bug report')), 
  >>     ('other', ('Other (please specify)')) 
  >> ) 
  >>
  >> ```

 - `SUPPORT_EMAIL`

  > valeur par défaut : `None`

  >> Liste de destinataire(s) pour les demandes d’assistance, si différent de `CONTACT_US_EMAIL` <br>
  >> i.e.: `SUPPORT_EMAIL = ["assistance_pod@univ.fr"]` <br>

 - `USER_CONTACT_EMAIL_CASE`

  > valeur par défaut : ``

  >> Une liste contenant les sujets de contact dont l’utilisateur <br>
  >> sera seul destinataire plutôt que le(s) manager(s). <br>
  >> Si la liste est vide, les mails de contact seront envoyés au(x) manager(s). <br>
  >> Valeurs possibles : <br>
  >>  `info`, `contribute`, `request_password`, <br>
  >>  `inapropriate_content`, `bug`, `other <br>

 - `USE_ESTABLISHMENT_FIELD`

  > valeur par défaut : `False`

  >> Si valeur vaut 'True', rajoute un attribut 'establishment' <br>
  >> à l’utilisateur Pod, ce qui permet de gérer plus d’un établissement. <br>
  >> Dans ce cas, les emails de contact par exemple seront envoyés <br>
  >>  soit à l’utilisateur soit au(x) manager(s) <br>
  >>  de l’établissement de l’utilisateur. <br>
  >> (voir `USER_CONTACT_EMAIL_CASE`) <br>
  >> Également, les emails de fin d’encodage seront envoyés au(x) manager(s) <br>
  >>  de l’établissement du propriétaire de la vidéo encodée, <br>
  >>  en plus d’un email au propriétaire confirmant la fin d’encodage d’une vidéo. <br>

### Encodage

 - `FFMPEG_AUDIO_BITRATE`

  > valeur par défaut : `192k`



 - `FFMPEG_CMD`

  > valeur par défaut : `ffmpeg`



 - `FFMPEG_CREATE_THUMBNAIL`

  > valeur par défaut : `-vf "fps=1/(%(duration)s/%(nb_thumbnail)s)" -vsync vfr "%(output)s_%%04d.png"`



 - `FFMPEG_CRF`

  > valeur par défaut : `20`



 - `FFMPEG_EXTRACT_SUBTITLE`

  > valeur par défaut : `-map 0:%(index)s -f webvtt -y "%(output)s" `



 - `FFMPEG_EXTRACT_THUMBNAIL`

  > valeur par défaut : `-map 0:%(index)s -an -c:v copy -y "%(output)s" `



 - `FFMPEG_HLS_COMMON_PARAMS`

  > valeur par défaut : `-c:v %(libx)s -preset %(preset)s -profile:v %(profile)s -pix_fmt yuv420p -level %(level)s -crf %(crf)s -sc_threshold 0 -force_key_frames "expr:gte(t,n_forced*1)" -c:a aac -ar 48000 -max_muxing_queue_size 4000 `



 - `FFMPEG_HLS_ENCODE_PARAMS`

  > valeur par défaut : `-vf "scale=-2:%(height)s" -maxrate %(maxrate)s -bufsize %(bufsize)s -b:a:0 %(ba)s -hls_playlist_type vod -hls_time %(hls_time)s -hls_flags single_file -master_pl_name "livestream%(height)s.m3u8" -y "%(output)s" `



 - `FFMPEG_HLS_TIME`

  > valeur par défaut : `2`



 - `FFMPEG_INPUT`

  > valeur par défaut : `-hide_banner -threads %(nb_threads)s -i "%(input)s" `



 - `FFMPEG_LEVEL`

  > valeur par défaut : `3`



 - `FFMPEG_LIBX`

  > valeur par défaut : `libx264`



 - `FFMPEG_M4A_ENCODE`

  > valeur par défaut : `-vn -c:a aac -b:a %(audio_bitrate)s "%(output)s" `



 - `FFMPEG_MP3_ENCODE`

  > valeur par défaut : `-vn -codec:a libmp3lame -qscale:a 2 -y "%(output)s" `



 - `FFMPEG_MP4_ENCODE`

  > valeur par défaut : `-map 0:v:0 %(map_audio)s -c:v %(libx)s -vf "scale=-2:%(height)s" -preset %(preset)s -profile:v %(profile)s -pix_fmt yuv420p -level %(level)s -crf %(crf)s -maxrate %(maxrate)s -bufsize %(bufsize)s -sc_threshold 0 -force_key_frames "expr:gte(t,n_forced*1)" -max_muxing_queue_size 4000 -c:a aac -ar 48000 -b:a %(ba)s -movflags faststart -y -vsync 0 "%(output)s" `



 - `FFMPEG_NB_THREADS`

  > valeur par défaut : `0`



 - `FFMPEG_NB_THUMBNAIL`

  > valeur par défaut : `3`



 - `FFMPEG_PRESET`

  > valeur par défaut : `slow`



 - `FFMPEG_PROFILE`

  > valeur par défaut : `high`



 - `FFMPEG_STUDIO_COMMAND`

  > valeur par défaut : ` -hide_banner -threads %(nb_threads)s %(input)s %(subtime)s -c:a aac -ar 48000 -c:v h264 -profile:v high -pix_fmt yuv420p -crf %(crf)s -sc_threshold 0 -force_key_frames "expr:gte(t,n_forced*1)" -max_muxing_queue_size 4000 -deinterlace `



 - `FFPROBE_CMD`

  > valeur par défaut : `ffprobe`



 - `FFPROBE_GET_INFO`

  > valeur par défaut : `%(ffprobe)s -v quiet -show_format -show_streams %(select_streams)s -print_format json -i %(source)s`



### Gestion des fichiers


 - `FILES_DIR`

  > valeur par défaut : `files`

  >> Nom du répertoire racine où les fichiers "complémentaires" <br>
  >> (hors vidéos etc.) sont téléversés. Notament utilisé par PODFILE <br>
  >> À modifier principalement pour indiquer dans LOCATION votre serveur de cache si elle n’est pas sur la même machine que votre POD. <br>

 - `FILE_UPLOAD_TEMP_DIR`

  > valeur par défaut : `/var/tmp`

  >> Le répertoire dans lequel stocker temporairement les données (typiquement pour les fichiers plus grands que `FILE_UPLOAD_MAX_MEMORY_SIZE`) lors des téléversements de fichiers.<br> <br>
  >> _ref: [https://docs.djangoproject.com/fr/3.2/ref/settings/#file-upload-temp-dir]()_ <br>

 - `MEDIA_ROOT`

  > valeur par défaut : `/pod/media`

  >> Chemin absolu du système de fichiers pointant vers le répertoire qui contiendra les fichiers téléversés par les utilisateurs.<br> <br>
  >> Attention, ce répertoire doit exister<br> <br>
  >> _ref: [https://docs.djangoproject.com/fr/3.2/ref/settings/#std:setting-MEDIA_ROOT]()_ <br>

 - `MEDIA_URL`

  > valeur par défaut : `/media/`

  >> prefix url utilisé pour accéder aux fichiers du répertoire media <br>

 - `STATICFILES_STORAGE`

  > valeur par défaut : ``

  >> Indique à django de compresser automatiquement les fichiers css/js les plus gros lors du collectstatic pour optimiser les tailles de requetes.<br> <br>
  >> À combiner avec un réglage webserver (`gzip_static on;` sur nginx)<br> <br>
  >> _ref: [https://github.com/whs/django-static-compress]() <br>

 - `STATIC_ROOT`

  > valeur par défaut : `/pod/static`

  >> Le chemin absolu vers le répertoire dans lequel collectstatic rassemble les fichiers statiques en vue du déploiement. Ce chemin sera précisé dans le fichier de configurtation du vhost nginx.<br> <br>
  >> _ref: [https://docs.djangoproject.com/fr/3.2/ref/settings/#std:setting-STATIC_ROOT]()_ <br>

 - `STATIC_URL`

  > valeur par défaut : `/static/`

  >> prefix url utilisé pour accèder aux fichiers static <br>

 - `USE_PODFILE`

  > valeur par défaut : `False`

  >> Utiliser l’application de gestion de fichier fourni avec le projet. <br>
  >> Si False, chaque fichier envoyé ne pourra être utilisé qu’une seule fois. <br>

 - `VIDEOS_DIR`

  > valeur par défaut : `videos`

  >> Répertoire par défaut pour le téléversement des vidéos. <br>

### Langue
Par défaut, Esup-Pod est fournie en Francais et en anglais.<br>
Vous pouvez tout à fait rajouter des langues comme vous le souhaitez. Il faudra pour cela créer un fichier de langue et traduire chaque entrée.<br>

 - `LANGUAGES`

  > valeur par défaut : `(('fr', 'Français'), ('en', 'English')))`

  >> Langue disponible et traduite <br>

 - `LANGUAGE_CODE`

  > valeur par défaut : `fr`

  >> Langue par défaut si non détectée <br>

### Divers

 - `ADMINS`

  > valeur par défaut : `[("Name", "adminmail@univ.fr"),]`

  >> Une liste de toutes les personnes qui reçoivent les notifications d’erreurs dans le code.<br> <br>
  >> Lorsque DEBUG=False et qu’une vue lève une exception, Django envoie un courriel à ces personnes contenant les informations complètes de l’exception.<br> <br>
  >> Chaque élément de la liste doit être un tuple au format « (nom complet, adresse électronique) ».<br> <br>
  >> Exemple : `[('John', 'john@example.com'), ('Mary', 'mary@example.com')]`<br> <br>
  >> Dans Pod, les "admins" sont également destinataires des courriels de contact, d’encodage ou de flux RSS si la variable `CONTACT_US_EMAIL` n’est pas renseignée.<br> <br>
  >> __ref: [https://docs.djangoproject.com/fr/3.2/ref/settings/#admins]()__ <br>

 - `ALLOWED_HOSTS`

  > valeur par défaut : `['localhost']`

  >> Une liste de chaînes représentant des noms de domaine/d’hôte que ce site Django peut servir.<br> <br>
  >> C’est une mesure de sécurité pour empêcher les attaques d’en-tête Host HTTP, qui sont possibles même avec bien des configurations de serveur Web apparemment sécurisées.<br> <br>
  >> __ref: [https://docs.djangoproject.com/fr/3.2/ref/settings/#allowed-hosts]()__ <br>

 - `BASE_DIR`

  > valeur par défaut : `os.path.dirname(os.path.dirname(os.path.abspath(__file__)))`

  >> répertoire de base <br>

 - `CACHES`

  > valeur par défaut : `{}`

  >>
  >> ```python
  >> CACHES = { 
  >>     # … default cache config and others 
  >>     # "default": { 
  >>     #     "BACKEND": "django.core.cache.backends.locmem.LocMemCache", 
  >>     # }, 
  >>     "default": { 
  >>         "BACKEND": "django_redis.cache.RedisCache", 
  >>         "LOCATION": "redis://127.0.0.1:6379/1", 
  >>         "OPTIONS": { 
  >>             "CLIENT_CLASS": "django_redis.client.DefaultClient", 
  >>         }, 
  >>     }, 
  >>     # Persistent cache setup for select2 (NOT DummyCache or LocMemCache). 
  >>     "select2": { 
  >>         "BACKEND": "django_redis.cache.RedisCache", 
  >>         "LOCATION": "redis://127.0.0.1:6379/2", 
  >>         "OPTIONS": { 
  >>             "CLIENT_CLASS": "django_redis.client.DefaultClient", 
  >>         }, 
  >>     }, 
  >> } 
  >>
  >> ```

 - `CSRF_COOKIE_SECURE`

  > valeur par défaut : ` not DEBUG`

  >> Ces 3 variables servent à sécuriser la plateforme en passant l’ensemble des requetes en https. Idem pour les cookies de session et de cross-sites qui seront également sécurisés<br> <br>
  >> Il faut les passer à False en cas d’usage du runserver (phase de développement / debugage)<br> <br>
  >> __ref: [https://docs.djangoproject.com/fr/3.2/ref/settings/#secure-ssl-redirect]()__ <br>

 - `DEBUG`

  > valeur par défaut : `True`

  >> Une valeur booléenne qui active ou désactive le mode de débogage.<br> <br>
  >> Ne déployez jamais de site en production avec le réglage DEBUG activé.<br> <br>
  >> __ref: [https://docs.djangoproject.com/fr/3.2/ref/settings/#debug]()__ <br>

 - `LOGIN_URL`

  > valeur par défaut : `/authentication_login/`

  >> url de redirection pour l’authentification de l’utilisateur <br>
  >> voir : [https://docs.djangoproject.com/fr/3.2/ref/settings/#login-url]() <br>

 - `MANAGERS`

  > valeur par défaut : `[]`

  >> Dans Pod, les "managers" sont destinataires des courriels de fin d’encodage (et ainsi des vidéos déposées sur la plateforme).<br> <br>
  >> Le premier manager renseigné est également contact des flus RSS.<br> <br>
  >> Ils sont aussi destinataires des courriels de contact si la variable `CONTACT_US_EMAIL` n’est pas renseignée.<br> <br>
  >> __ref: [https://docs.djangoproject.com/fr/3.2/ref/settings/#managers]()__ <br>

 - `PROXY_HOST`

  > valeur par défaut : ``

  >> Utilisation du proxy - host <br>

 - `PROXY_PORT`

  > valeur par défaut : ``

  >> Utilisation du proxy - port <br>

 - `SECRET_KEY`

  > valeur par défaut : `A_CHANGER`

  >> La clé secrète d’une installation Django.<br> <br>
  >> Elle est utilisée dans le contexte de la signature cryptographique, et doit être définie à une valeur unique et non prédictible.<br> <br>
  >> Vous pouvez utiliser ce site pour en générer une : [https://djecrety.ir/]()<br> <br>
  >> __ref: [https://docs.djangoproject.com/fr/3.2/ref/settings/#secret-key]()__ <br>

 - `SECURE_SSL_REDIRECT`

  > valeur par défaut : `not DEBUG`



 - `SESSION_COOKIE_AGE`

  > valeur par défaut : `14400`

  >> _Valeur par défaut : 14400 (secondes, soit 4 heures)_<br> <br>
  >> L’âge des cookies de sessions, en secondes. <br>

 - `SESSION_COOKIE_SAMESITE`

  > valeur par défaut : `Lax`

  >> Cette option empêche le cookie d’être envoyé dans les requêtes inter-sites, ce qui prévient les attaques CSRF et rend impossible certaines méthodes de vol du cookie de session. <br>
  >> Voir [https://docs.djangoproject.com/en/3.2/ref/settings/#std-setting-SESSION_COOKIE_SAMESITE]() <br>

 - `SESSION_COOKIE_SECURE`

  > valeur par défaut : ` not DEBUG`



 - `SESSION_EXPIRE_AT_BROWSER_CLOSE`

  > valeur par défaut : `True`

  >> Indique s’il faut que la session expire lorsque l’utilisateur ferme son navigateur. <br>

 - `SITE_ID`

  > valeur par défaut : `1`

  >> L’identifiant (nombre entier) du site actuel. Peut être utilisé pour mettre en place une instance multi-tenant et ainsi gérer dans une même base de données du contenu pour plusieurs sites.<br> <br>
  >> __ref : [https://docs.djangoproject.com/fr/3.2/ref/settings/#site-id]()__ <br>

 - `TEST_SETTINGS`

  > valeur par défaut : `False`

  >> Permet de vérifier si la configuration de la plateforme est en mode test. <br>

 - `THIRD_PARTY_APPS`

  > valeur par défaut : `[]`

  >> Liste des applications tierces accessibles. <br>
  >>
  >> ```
  >> THIRD_PARTY_APPS = ["enrichment", "live"] 
  >>
  >> ```

 - `TIME_ZONE`

  > valeur par défaut : `UTC`

  >> Une chaîne représentant le fuseau horaire pour cette installation.<br> <br>
  >> __ref: [https://docs.djangoproject.com/fr/3.2/ref/settings/#std:setting-TIME_ZONE]()__ <br>
  >> Liste des adresses destinataires des courriels de contact <br>

### Obsolescence

 - `ACCOMMODATION_YEARS`

  > valeur par défaut : `{}`

  >> Durée d’obsolescence personnalisée par Affiliation <br>
  >>
  >> ```
  >> ACCOMMODATION_YEARS = { 
  >>     'affiliate': 1 
  >> } 
  >>
  >> ```

 - `ARCHIVE_OWNER_USERNAME`

  > valeur par défaut : `"archive"`

  >> Nom de l’utilisateur pour l’archivage des vidéos. <br>

 - `POD_ARCHIVE_AFFILIATION`

  > valeur par défaut : `[]`

  >> Affiliations pour lesquelles on souhaite archiver la vidéo plutôt que de la supprimer. <br>
  >> Si l’affiliation du propriétaire est dans cette variable, alors les vidéos sont affectées à un utilisateur précis <br>
  >> que l’on peut spécifier via le paramètre `ARCHIVE_OWNER_USERNAME`. <br>
  >> Elles sont mises en mode brouillon et le mot "archived" est ajouté à leur titre. <br>
  >> Enfin, elles sont également ajoutées à l’ensemble `Vidéo à Supprimer` (accessible via l’interface d’admin). <br>
  >>
  >> ```python
  >> POD_ARCHIVE_AFFILIATION = ['faculty', 
  >>                            'staff', 
  >>                            'employee', 
  >>                            'affiliate', 
  >>                            'alum', 
  >>                            'library-walk-in', 
  >>                            'researcher', 
  >>                            'retired', 
  >>                            'emeritus', 
  >>                            'teacher', 
  >>                            'registered-reader', 
  >>                            'member'] 
  >>
  >> ```

 - `WARN_DEADLINES`

  > valeur par défaut : `[60, 30, 7]`

  >> Liste de jours de délais avant l’obsolescence de la vidéo. <br>
  >> À chaque délai, le propriétaire reçoit un mail d’avertissement pour éventuellement changer la date d’obsolescence de sa vidéo. <br>

### Modèle

 - `COOKIE_LEARN_MORE`

  > valeur par défaut : ``

  >> Ce paramètre permet d’afficher un lien "En savoir plus" <br>
  >> sur la boite de dialogue d’information sur l’usage des cookies dans Pod. <br>
  >> On peut préciser un lien vers les mentions légales ou page DPO. <br>

 - `DARKMODE_ENABLED`

  > valeur par défaut : `False`

  >> Activation du mode sombre <br>

 - `DYSLEXIAMODE_ENABLED`

  > valeur par défaut : `False`

  >> Activation du mode dyslexie <br>

 - `HIDE_CHANNEL_TAB`

  > valeur par défaut : `False`

  >> Si True, permet de cacher l’onglet chaine dans la barre de menu du haut. <br>

 - `HIDE_CURSUS`

  > valeur par défaut : `False`

  >> Si True, permet de ne pas afficher les cursus dans la colonne de droite <br>

 - `HIDE_DISCIPLINES`

  > valeur par défaut : `False`

  >> Si True, permet de ne pas afficher les disciplines dans la colonne de droite <br>

 - `HIDE_LANGUAGE_SELECTOR`

  > valeur par défaut : `False`

  >> Si True, permet de cacher le sélecteur de langue dans le menu du haut. <br>

 - `HIDE_SHARE`

  > valeur par défaut : `False`

  >> Si True, permet de ne pas afficher les liens de partage sur les réseaux sociaux dans la colonne de droite. <br>

 - `HIDE_TAGS`

  > valeur par défaut : `False`

  >> Si True, permet de ne pas afficher le nuage de mots clés dans la colonne de droite. <br>

 - `HIDE_TYPES`

  > valeur par défaut : `False`

  >> si True, permet de ne pas afficher la liste des types dans la colonne de droite <br>

 - `HIDE_TYPES_TAB`

  > valeur par défaut : `False`

  >> Si True, permet de cacher l’entrée 'type' dans le menu de navigation. <br>

 - `HIDE_USERNAME`

  > valeur par défaut : `False`

  >> Voir description dans authentification <br>
  >> Si valeur vaut 'True', le username de l’utilisateur ne sera pas visible sur la plate-forme Pod et <br>
  >> si la valeur vaut 'False' le username sera affiché aux utilisateurs authentifiés. (pour respecter le RGPD) <br>

 - `HIDE_USER_FILTER`

  > valeur par défaut : `False`

  >> Si 'True', le filtre des vidéos par utilisateur ne sera plus visible <br>
  >> si 'False' le filtre sera visible qu’aux personnes authentifiées. <br>
  >> (pour respecter le RGPD) <br>

 - `HIDE_USER_TAB`

  > valeur par défaut : `False`

  >> Si valeur vaut 'True', l’onglet Utilisateur ne sera pas visible <br>
  >> et si la valeur vaut 'False' l’onglet Utilisateur ne sera visible <br>
  >> qu’aux personnes authentifiées. <br>
  >> (pour respecter le RGPD) <br>

 - `HOMEPAGE_NB_VIDEOS`

  > valeur par défaut : `12`

  >> Nombre de vidéos à afficher sur la page d’accueil. <br>

 - `HOMEPAGE_SHOWS_PASSWORDED`

  > valeur par défaut : `False`

  >> Afficher les vidéos dont l’accès est protégé par mot de passe sur la page d’accueil. <br>

 - `HOMEPAGE_SHOWS_RESTRICTED`

  > valeur par défaut : `False`

  >> Afficher les vidéos dont l’accès est protégé par authentification sur la page d’accueil. <br>

 - `MENUBAR_HIDE_INACTIVE_OWNERS`

  > valeur par défaut : `True`

  >> Les utilisateurs inactifs ne sont plus affichés dans la barre de menu utilisateur. <br>

 - `MENUBAR_SHOW_STAFF_OWNERS_ONLY`

  > valeur par défaut : `False`

  >> Les utilisateurs non staff ne sont plus affichés dans la barre de menu utilisateur. <br>

 - `SHIB_NAME`

  > valeur par défaut : `Identify Federation`

  >> Nom de la fédération d’identité utilisée <br>
  >> Affiché sur le bouton de connexion si l’authentification Shibboleth est utilisée. <br>

 - `SHOW_EVENTS_ON_HOMEPAGE`

  > valeur par défaut : `False`

  >> Si True, affiche les prochains évènements sur la page d’accueil. <br>

 - `SHOW_ONLY_PARENT_THEMES`

  > valeur par défaut : `False`

  >> Si True, affiche uniquement les thèmes de premier niveau dans l’onglet 'Chaîne'. <br>

 - `TEMPLATE_VISIBLE_SETTINGS`

  > valeur par défaut : `{}`

  >>
  >> ```
  >> TEMPLATE_VISIBLE_SETTINGS = { 
  >> # Titre du site. 
  >> 'TITLE_SITE': 'Pod', 
  >>   
  >> # Description du site. 
  >> 'DESC_SITE': 'L’objectif d’Esup-Pod est de faciliter la mise à disposition de vidéos et ainsi d’encourager son utilisation dans l’enseignement et la recherche.', 
  >>   
  >> # Titre de l’établissement. 
  >> 'TITLE_ETB': 'University name', 
  >>   
  >> # Logo affiché en haut à gauche sur toutes les pages. 
  >> # Doit se situer dans le répertoire static 
  >> 'LOGO_SITE': 'img/logoPod.svg', 
  >>   
  >> # Logo affiché dans le footer sur toutes les pages. 
  >> # Doit se situer dans le répertoire static 
  >> 'LOGO_ETB': 'img/esup-pod.svg', 
  >>   
  >> # Logo affiché sur le player video. 
  >> # Doit se situer dans le répertoire static 
  >> 'LOGO_PLAYER': 'img/pod_favicon.svg', 
  >>   
  >> # Lien de destination du logo affiché sur le player. 
  >> 'LINK_PLAYER': '', 
  >>   
  >> # Intitulé de la page de redirection du logo affiché sur le player. 
  >> 'LINK_PLAYER_NAME': _('Home'), 
  >>   
  >> # Texte affiché dans le footer. Une ligne par entrée, accepte du code html. 
  >> # Par exemple : 
  >> # ( '42, rue Paul Duez', 
  >> #   '59000 Lille - France', 
  >> #   ('<a href="https://goo.gl/maps/AZnyBK4hHaM2"' 
  >> #    ' target="_blank">Google maps</a>') ) 
  >> 'FOOTER_TEXT': ('',), 
  >>   
  >> # Icone affichée dans la barre d'adresse du navigateur 
  >> 'FAVICON': 'img/pod_favicon.svg', 
  >>   
  >> # Si souhaitée, à créer et sauvegarder 
  >> #  dans le répertoire static de l'application custom et 
  >> #  préciser le chemin d'accès. Par exemple : "custom/etab.css" 
  >> 'CSS_OVERRIDE': '', 
  >>   
  >> # Vous pouvez créer un template dans votre application custom et 
  >> #  indiquer son chemin dans cette variable pour que ce code html, 
  >> # ce template soit affiché en haut de votre page, le code est ajouté 
  >> #  juste après la balise body.(Hors iframe) 
  >> # Si le fichier créé est 
  >> # '/opt/django_projects/podv3/pod/custom/templates/custom/preheader.html' 
  >> # alors la variable doit prendre la valeur 'custom/preheader.html' 
  >> 'PRE_HEADER_TEMPLATE': '', 
  >>   
  >> # Idem que pre-header, le code contenu dans le template 
  >> #  sera affiché juste avant la fermeture du body. (Or iframe) 
  >> 'POST_FOOTER_TEMPLATE': '', 
  >>   
  >> # vous pouvez créer un template dans votre application custom 
  >> #  pour y intégrer votre code Piwik ou Google analytics. 
  >> # Ce template est inséré dans toutes les pages de la plateforme, 
  >> #  y compris en mode iframe 
  >> 'TRACKING_TEMPLATE': '', 
  >> } 
  >>
  >> ```

### Transcodage

 - `TRANSCRIPTION_AUDIO_SPLIT_TIME`

  > valeur par défaut : `600`

  >> Découpage de l’audio pour la transcription. <br>

 - `TRANSCRIPTION_MODEL_PARAM`

  > valeur par défaut : `{}`

  >> Paramétrage des modèles pour la transcription <br>
  >> Voir la documentation à cette adresse : [https://www.esup-portail.org/wiki/display/ES/Installation+de+l%27autotranscription+en+Pod+V3]() <br>
  >> Pour télécharger les Modeles Vosk : [https://alphacephei.com/vosk/models]() <br>
  >>
  >> ```
  >> TRANSCRIPTION_MODEL_PARAM = { 
  >>     # le modèle stt 
  >>     'STT': { 
  >>         'fr': { 
  >>             'model': "/path/to/project/Esup-Pod/transcription/model_fr/stt/output_graph.tflite", 
  >>             'scorer': "/path/to/project/Esup-Pod/transcription/model_fr/stt/kenlm.scorer", 
  >>         } 
  >>     }, 
  >>     # le modèle vosk 
  >>     'VOSK': { 
  >>         'fr': { 
  >>             'model': "/path/of/project/Esup-Pod/transcription/model_fr/vosk/vosk-model-fr-0.6-linto-2.2.0", 
  >>         } 
  >>     } 
  >> } 
  >>
  >> ```

 - `TRANSCRIPTION_NORMALIZE`

  > valeur par défaut : `False`

  >> Activation de la normalisation de l’audio avant sa transcription. <br>

 - `TRANSCRIPTION_NORMALIZE_TARGET_LEVEL`

  > valeur par défaut : `-16.0`

  >> Niveau de normalisation de l’audio avant sa transcription. <br>

 - `TRANSCRIPTION_STT_SENTENCE_BLANK_SPLIT_TIME`

  > valeur par défaut : `0.5`

  >> Temps maximum en secondes des blancs entre chaque mot pour le decoupage des sous-titres avec l’outil STT. <br>

 - `TRANSCRIPTION_STT_SENTENCE_MAX_LENGTH`

  > valeur par défaut : `2`

  >> Temps en secondes maximum pour une phrase lors de la transcription avec l’outil STT. <br>

 - `TRANSCRIPTION_TYPE`

  > valeur par défaut : `STT`

  >> Choix de l’outil pour la transcription : STT ou VOSK. <br>

 - `TRANSCRIPT_VIDEO`

  > valeur par défaut : `start_transcript`

  >> Fonction appelée pour lancer la transcription des vidéos. <br>

 - `USE_TRANSCRIPTION`

  > valeur par défaut : `False`

  >> Activation de la transcription. <br>

## Configuration Générale de la plateforme Esup_Pod 


### Configuration application authentification.

 - `AFFILIATION`

  > valeur par défaut : ``

  >> Valeurs possibles pour l’affiliation du compte. <br>

 - `AFFILIATION_EVENT`

  > valeur par défaut : ``

  >> Groupes ou affiliations des personnes autorisées à créer un évènement. <br>

 - `AFFILIATION_STAFF`

  > valeur par défaut : ``

  >> Les personnes ayant pour affiliation les valeurs <br>
  >> renseignées dans cette variable ont automatiquement <br>
  >> la valeur staff de leur compte à True. <br>

 - `AUTH_CAS_USER_SEARCH`

  > valeur par défaut : `user`

  >> Variable utilisée pour trouver les informations de l’individu <br>
  >> connecté dans le fichier renvoyé par le CAS lors de l’authentification. <br>

 - `AUTH_LDAP_BIND_DN`

  > valeur par défaut : ``

  >> Identifiant (DN) du compte pour se connecter au serveur LDAP. <br>

 - `AUTH_LDAP_BIND_PASSWORD`

  > valeur par défaut : ``

  >> Mot de passe du compte pour se connecter au serveur LDAP. <br>

 - `AUTH_LDAP_USER_SEARCH`

  > valeur par défaut : ``

  >> Filtre LDAP permettant la recherche de l’individu dans le serveur LDAP. <br>

 - `AUTH_TYPE`

  > valeur par défaut : ``

  >> Type d’authentification possible sur votre instance. <br>
  >>  Choix : local, CAS, OIDC, Shibboleth <br>

 - `CAS_ADMIN_AUTH`

  > valeur par défaut : `False`

  >> Permet d’activer l’authentification CAS pour la partie admin <br>
  >> Voir : [https://pypi.org/project/django-cas-sso/]() <br>

 - `CAS_FORCE_LOWERCASE_USERNAME`

  > valeur par défaut : `False`

  >> Forcer le passage en minuscule du nom d’utilisateur CAS <br>
  >> (permet de prévenir des doubles créations de comptes dans certain cas). <br>

 - `CAS_GATEWAY`

  > valeur par défaut : `False`

  >> Si True, authentifie automatiquement l’individu <br>
  >> si déjà authentifié sur le serveur CAS <br>

 - `CAS_LOGOUT_COMPLETELY`

  > valeur par défaut : `True`

  >> Voir [https://github.com/kstateome/django-cas]() <br>

 - `CAS_SERVER_URL`

  > valeur par défaut : `sso_cas`

  >> Url du serveur CAS de l’établissement. Format http://url_cas <br>

 - `CREATE_GROUP_FROM_AFFILIATION`

  > valeur par défaut : `False`

  >> Si True, des groupes sont créés automatiquement <br>
  >> à partir des affiliations des individus qui se connectent sur la plateforme <br>
  >> et l’individu qui se connecte est ajouté automatiquement à ces groupes. <br>

 - `CREATE_GROUP_FROM_GROUPS`

  > valeur par défaut : `False`

  >> Si True, des groupes sont créés automatiquement <br>
  >> à partir des groupes (attribut groups à memberOf) <br>
  >> des individus qui se connectent sur la plateforme <br>
  >> et l’individu qui se connecte est ajouté automatiquement à ces groupes <br>

 - `DEFAULT_AFFILIATION`

  > valeur par défaut : ``

  >> Affiliation par défaut d’un utilisateur authentifié par OIDC. <br>
  >> Ce contenu sera comparé à la liste AFFILIATION_STAFF pour déterminer si l’utilisateur doit être admin Django <br>

 - `ESTABLISHMENTS`

  > valeur par défaut : ``

  >> [TODO] À compléter <br>

 - `GROUP_STAFF`

  > valeur par défaut : `AFFILIATION_STAFF`

  >> utilisé dans populatedCasbackend <br>

 - `HIDE_LOCAL_LOGIN`

  > valeur par défaut : `False`

  >> Si True, masque l’authentification locale <br>

 - `HIDE_USERNAME`

  > valeur par défaut : `False`

  >> Si valeur vaut `True`, le username de l’utilisateur ne sera pas visible sur la plate-forme Pod et si la valeur vaut `False` le username sera affiché aux utilisateurs authentifiés. (pour respecter le RGPD) <br>

 - `LDAP`

  > valeur par défaut : ``

  >>  - LDAP (Interroge le serveur LDAP pour renseigner les champs) <br>

 - `LDAP_SERVER`

  > valeur par défaut : ``

  >> Information de connection au serveur LDAP. <br>
  >> Le champ url peut contenir une ou plusieurs url <br>
  >>  pour ajouter des hôtes de référence, exemple : <br>
  >> Si un seul host : <br>
  >>
  >> `{'url': "ldap.univ.fr'', 'port': 389, 'use_ssl': False}`
  >> Si plusieurs : 
  >>
  >> `{'url': ("ldap.univ.fr'',"ldap2.univ.fr"), 'port': 389, 'use_ssl': False}`

 - `OIDC_CLAIM_FAMILY_NAME`

  > valeur par défaut : `family_name`



 - `OIDC_CLAIM_GIVEN_NAME`

  > valeur par défaut : `given_name`

  >> Noms des Claim permettant de récupérer les attributs nom, prénom, email <br>

 - `OIDC_DEFAULT_ACCESS_GROUP_CODE_NAMES`

  > valeur par défaut : `[]`

  >> Groupes d’accès attribués par défaut à un nouvel utilisateur authentifié par OIDC <br>

 - `OIDC_DEFAULT_AFFILIATION`

  > valeur par défaut : ``

  >> Affiliation par défaut d’un utilisateur authentifié par OIDC. <br>
  >> Ce contenu sera comparé à la liste AFFILIATION_STAFF pour déterminer si l’utilisateur doit être admin Django <br>

 - `OIDC_NAME`

  > valeur par défaut : ``

  >> Nom du Service Provider OIDC <br>

 - `OIDC_OP_AUTHORIZATION_ENDPOINT`

  > valeur par défaut : `https`



 - `OIDC_OP_JWKS_ENDPOINT`

  > valeur par défaut : `https`

  >> Différents paramètres pour OIDC <br>
  >> tant que `mozilla_django_oidc` n’accepte pas le mécanisme de discovery <br>
  >> ref: [https://github.com/mozilla/mozilla-django-oidc/pull/309]() <br>

 - `OIDC_OP_TOKEN_ENDPOINT`

  > valeur par défaut : `https`



 - `OIDC_OP_USER_ENDPOINT`

  > valeur par défaut : `https`



 - `OIDC_RP_CLIENT_ID`

  > valeur par défaut : `os.environ`



 - `OIDC_RP_CLIENT_SECRET`

  > valeur par défaut : `os.environ`

  >>
  >> `CLIENT_ID` et `CLIENT_SECRET` de OIDC sont plutôt à positionner
  >> à travers des variables d’environnement. 

 - `OIDC_RP_SIGN_ALGO`

  > valeur par défaut : ``



 - `POPULATE_USER`

  > valeur par défaut : `None`

  >> Si utilisation de la connection CAS, renseigne les champs du compte <br>
  >> de la personne depuis une source externe. <br>
  >> Valeurs possibles : <br>
  >>  - None (pas de renseignement), <br>
  >>  - CAS (renseigne les champs depuis les informations renvoyées par le CAS), <br>

 - `REMOTE_USER_HEADER`

  > valeur par défaut : `REMOTE_USER`

  >> Nom de l’attribut dans les headers qui sert à identifier <br>
  >> l’utilisateur connecté avec Shibboleth. <br>

 - `SHIBBOLETH_ATTRIBUTE_MAP`

  > valeur par défaut : ``

  >> Mapping des attributs entre Shibboleth et la classe utilisateur <br>

 - `SHIBBOLETH_STAFF_ALLOWED_DOMAINS`

  > valeur par défaut : ``

  >> Permettre à l’utilisateur d’un domaine d’être membre du personnel. <br>
  >> Si vide, tous les domaines seront autorisés. <br>

 - `SHIB_LOGOUT_URL`

  > valeur par défaut : ``

  >> URL de déconnexion à votre instance Shibboleth <br>

 - `SHIB_NAME`

  > valeur par défaut : ``

  >> Nom de la fédération d’identité utilisée. <br>

 - `SHIB_URL`

  > valeur par défaut : ``

  >> URL de connexion à votre instance Shibboleth. <br>

 - `USER_CAS_MAPPING_ATTRIBUTES`

  > valeur par défaut : ``

  >> Liste de correspondance entre les champs d’un compte de Pod <br>
  >> et les champs renvoyés par le CAS. <br>

 - `USER_LDAP_MAPPING_ATTRIBUTES`

  > valeur par défaut : ``

  >> Liste de correspondance entre les champs d’un compte de Pod <br>
  >> et les champs renvoyés par le LDAP. <br>

 - `USE_CAS`

  > valeur par défaut : `False`

  >> Activation de l’authentification CAS en plus de l’authentification locale. <br>

 - `USE_OIDC`

  > valeur par défaut : `False`

  >> Mettre à True pour utiliser l’authentification OpenID Connect. <br>

 - `USE_SHIB`

  > valeur par défaut : `False`

  >> Mettre à True pour utiliser l’authentification Shibboleth. <br>

### Configuration application chapter.

### Configuration application completion

 - `ACTIVE_MODEL_ENRICH`

  > valeur par défaut : `False`

  >> Définissez à True pour activer la case à cocher dans l’édition des sous-titres. <br>

 - `ALL_LANG_CHOICES`

  > valeur par défaut : ``

  >> liste toutes les langues pour l’ajout de fichier de sous-titre <br>
  >> voir le fichier `pod/main/lang_settings.py`. <br>

 - `DEFAULT_LANG_TRACK`

  > valeur par défaut : `fr`

  >> langue par défaut pour l’ajout de piste à une vidéo. <br>

 - `KIND_CHOICES`

  > valeur par défaut : ``

  >> Liste de types de piste possibles pour une vidéo (sous-titre, légende etc.) <br>

 - `LANG_CHOICES`

  > valeur par défaut : ``

  >> Liste des langues proposées lors de l’ajout des vidéos. <br>
  >> Affichés en dessous d’une vidéo, les choix sont aussi utilisés pour affiner la recherche. <br>

 - `LINK_SUPERPOSITION`

  > valeur par défaut : `False`

  >> Si valeur vaut 'True', les URLs contenues dans le texte de superposition seront transformées, à la lecture de la vidéo, en liens cliquables. <br>

 - `MODEL_COMPILE_DIR`

  > valeur par défaut : `/path/of/project/Esup-Pod/compile-model`

  >> Paramétrage des chemins du modèle pour la compilation <br>
  >> Pour télécharger les modèles : [https://alphacephei.com/vosk/lm#update-process]() <br>
  >> Ajouter le modèle dans les sous-dossier de la langue correspondante <br>
  >> Exemple pour le français : `/path/of/project/Esup-Pod/compile-model/fr/` <br>

 - `PREF_LANG_CHOICES`

  > valeur par défaut : ``

  >> liste des langues à afficher en premier dans la liste des toutes les langues <br>
  >> voir le fichier `pod/main/lang_settings.py` <br>

 - `ROLE_CHOICES`

  > valeur par défaut : ``

  >> Liste de rôles possibles pour un contributeur. <br>

 - `TRANSCRIPTION_MODEL_PARAM`

  > valeur par défaut : ``

  >> Paramétrage des modèles pour la transcription <br>
  >> Voir la documentation à cette adresse : <br>
  >>  [https://www.esup-portail.org/wiki/display/ES/Installation+de+l%27autotranscription+en+Pod+V3]() <br>
  >> Pour télécharger les modèles Vosk : [https://alphacephei.com/vosk/models]() <br>
  >>
  >> ```python
  >> TRANSCRIPTION_MODEL_PARAM = { 
  >>     # le modèle stt 
  >>     'STT': { 
  >>         'fr': { 
  >>             'model': "/path/to/project/Esup-Pod/transcription/model_fr/stt/output_graph.tflite", 
  >>             'scorer': "/path/to/project/Esup-Pod/transcription/model_fr/stt/kenlm.scorer", 
  >>         } 
  >>     }, 
  >>     # le modèle vosk 
  >>     'VOSK': { 
  >>         'fr': { 
  >>             'model': "/path/of/project/Esup-Pod/transcription/model_fr/vosk/vosk-model-fr-0.6-linto-2.2.0", 
  >>         } 
  >>     } 
  >> } 
  >>
  >> ```

 - `TRANSCRIPTION_TYPE`

  > valeur par défaut : `STT`

  >> STT ou VOSK <br>

 - `USE_ENRICH_READY`

  > valeur par défaut : `False `

  >> voir `ACTIVE_MODEL_ENRICH` <br>

### Configuration application enrichment

### Configuration application d'import vidéo
Application Import_video permettant d'importer des vidéos externes dans Pod.<br>
Mettre `USE_IMPORT_VIDEO` à True pour activer cette application.<br>

 - `MAX_UPLOAD_SIZE_ON_IMPORT`

  > valeur par défaut : `4`

  >> Taille maximum en Go des fichiers vidéos qui peuvent être importés sur la plateforme  <br>
  >> via l'application import_video (0 = pas de taille maximum). <br>

 - `RESTRICT_EDIT_IMPORT_VIDEO_ACCESS_TO_STAFF_ONLY`

  > valeur par défaut : `True`

  >> Seuls les utilisateurs "staff" pourront importer des vidéos <br>

 - `USE_IMPORT_VIDEO`

  > valeur par défaut : `True`

  >> Activation de l’application d'import des vidéos <br>

### Configuration application live

 - `AFFILIATION_EVENT`

  > valeur par défaut : `['faculty', 'employee', 'staff']`

  >> Groupes ou affiliations des personnes autorisées à créer un évènement. <br>

 - `BROADCASTER_PILOTING_SOFTWARE`

  > valeur par défaut : `[]`

  >> Types de logiciel de serveur de streaming utilisés. <br>
  >> Actuellement disponible Wowza et SMP. Il faut préciser cette valeur pour l’activer `['Wowza', 'SMP']` <br>
  >> Si vous utilisez une autre logiciel, <br>
  >> il faut développer une interface dans `pod/live/pilotingInterface.py` <br>

 - `DEFAULT_EVENT_PATH`

  > valeur par défaut : ``

  >> Chemin racine du répertoire où sont déposés temporairement les enregistrements des évènements éffectués depuis POD pour convertion en ressource vidéo (VOD) <br>

 - `DEFAULT_EVENT_THUMBNAIL`

  > valeur par défaut : `/img/default-event.svg`

  >> Image par défaut affichée comme poster ou vignette, utilisée pour présenter l’évènement. <br>
  >> Cette image doit se situer dans le répertoire `static`. <br>

 - `DEFAULT_EVENT_TYPE_ID`

  > valeur par défaut : `1`

  >> Type par défaut affecté à un évènement direct (en général, le type ayant pour identifiant '1' est 'Other') <br>

 - `DEFAULT_THUMBNAIL`

  > valeur par défaut : `img/default.svg`

  >> Image par défaut affichée comme poster ou vignette, utilisée pour présenter la vidéo. <br>
  >> Cette image doit se situer dans le répertoire static. <br>

 - `EMAIL_ON_EVENT_SCHEDULING`

  > valeur par défaut : `True`

  >> Si True, un courriel est envoyé aux managers et à l’auteur (si DEBUG est à False) à la création/modification d’un event. <br>

 - `EVENT_ACTIVE_AUTO_START`

  > valeur par défaut : `False`

  >> Permet de lancer automatiquement l’enregistrement sur l’interface utilisée (wowza, ) sur le broadcaster et spécifié par `BROADCASTER_PILOTING_SOFTWARE` <br>

 - `EVENT_CHECK_MAX_ATTEMPT`

  > valeur par défaut : `10`

  >> Nombre de tentatives maximum pour vérifier la présence / taille d'un fichier sur le filesystem <br>

 - `EVENT_GROUP_ADMIN`

  > valeur par défaut : `event admin`

  >> Permet de préciser le nom du groupe dans lequel les utilisateurs peuvent planifier un évènement sur plusieurs jours. <br>

 - `HEARTBEAT_DELAY`

  > valeur par défaut : `45`

  >> Temps (en secondes) entre deux envois d’un signal au serveur, pour signaler la présence sur un live. <br>
  >> Peut être augmenté en cas de perte de performance, mais au détriment de la qualité du comptage des valeurs. <br>

 - `LIVE_CELERY_TRANSCRIPTION `

  > valeur par défaut : `False`


  >> Activer la transcription déportée sur une machine distante. <br>

 - `LIVE_TRANSCRIPTIONS_FOLDER`

  > valeur par défaut : ``


  >> Dossier contenat les fichiers de sous-titre au format vtt pour les directs <br>

 - `LIVE_VOSK_MODEL`

  > valeur par défaut : `{}`


  >> Paramétrage des modèles pour la transcription des directs <br>
  >> La documentation sera présente prochaînement <br>
  >> Pour télécharger les Modèles Vosk : [https://alphacephei.com/vosk/models]() <br>
  >>
  >> ```
  >> LIVE_VOSK_MODEL = { 
  >>    'fr': { 
  >>        'model': "/path/of/project/django_projects/transcription/live/fr/vosk-model-small-fr-0.22", 
  >>     } 
  >> } 
  >>
  >> ```

 - `USE_BBB`

  > valeur par défaut : `True`

  >> Utilisation de BigBlueButton - [TODO] À retirer dans les futures versions de Pod <br>

 - `USE_BBB_LIVE`

  > valeur par défaut : `False `

  >> Utilisation du système de diffusion de Webinaires en lien avec BigBlueButton - [TODO] À retirer dans les futures versions de Pod <br>

 - `USE_LIVE_TRANSCRIPTION`

  > valeur par défaut : `False`


  >> Activer l'auto-transcription pour les directs <br>

 - `VIEW_EXPIRATION_DELAY`

  > valeur par défaut : `60`

  >> Délai (en seconde) selon lequel une vue est considérée comme expirée si elle n’a pas renvoyé de signal depuis. <br>

### Configuration application LTI

 - `LTI_ENABLED`

  > valeur par défaut : `False`

  >> Configuration / Activation du LTI voir pod/main/settings.py L.224 <br>

 - `PYLTI_CONFIG`

  > valeur par défaut : `{}`

  >> Cette variable permet de configurer l’application cliente et le secret partagé <br>
  >>
  >> ```
  >> PYLTI_CONFIG = { 
  >>     'consumers': { 
  >>         '<random number string>': { 
  >>             'secret': '<random number string>' 
  >>         } 
  >>     } 
  >> } 
  >>
  >> ```

### Configuration application main

 - `HOMEPAGE_VIEW_VIDEOS_FROM_NON_VISIBLE_CHANNELS`

  > valeur par défaut : `False`

  >> Affiche les vidéos de chaines non visibles sur la page d'accueil <br>

 - `USE_BBB`

  > valeur par défaut : `True`

  >> Utilisation de BigBlueButton - [TODO] À retirer dans les futures versions de Pod <br>

 - `USE_BBB_LIVE`

  > valeur par défaut : `False `

  >> Utilisation du système de diffusion de Webinaires en lien avec BigBlueButton - [TODO] À retirer dans les futures versions de Pod <br>

 - `USE_IMPORT_VIDEO`

  > valeur par défaut : `True`

  >> Activation de l’application d'import des vidéos <br>

 - `USE_MEETING`

  > valeur par défaut : `False`

  >> Activation de l’application meeting <br>

 - `USE_OPENCAST_STUDIO`

  > valeur par défaut : `False`

  >> Activation du studio [https://opencast.org/](Opencast) <br>

 - `VERSION`

  > valeur par défaut : ``

  >> Version courante du projet <br>

### Configuration application meeting

Application Meeting pour la gestion de reunion avec BBB.<br>
Mettre `USE_MEETING` à True pour activer cette application.<br>
`BBB_API_URL` et `BBB_SECRET_KEY` sont obligatoires pour faire fonctionner l’application<br>

 - `BBB_API_URL`

  > valeur par défaut : ``

  >> Indiquer l’URL API de BBB par ex `https://webconf.univ.fr/bigbluebutton/api <br>

 - `BBB_LOGOUT_URL`

  > valeur par défaut : ``

  >> Indiquer l’URL de retour au moment où vous quittez la réunion BBB. Ce champ est optionnel. <br>

 - `BBB_MEETING_INFO`

  > valeur par défaut : `{}`

  >> Dictionnaire de clé:valeur permettant d’afficher les informations d’une session de réunion dans BBB <br>
  >> Voici la liste par défaut <br>
  >>
  >> ```
  >> BBB_MEETING_INFO: 
  >> { 
  >>     "meetingName": _("Meeting name"), 
  >>     "hasUserJoined": _("Has user joined?"), 
  >>     "recording": _("Recording"), 
  >>     "participantCount": _("Participant count"), 
  >>     "listenerCount": _("Listener count"), 
  >>     "moderatorCount": _("Moderator count"), 
  >>     "attendees": _("Attendees"), 
  >>     "attendee": _("Attendee"), 
  >>     "fullName": _("Full name"), 
  >>     "role": _("Role"), 
  >> } 
  >>
  >> ```

 - `BBB_SECRET_KEY`

  > valeur par défaut : ``

  >> Clé de votre serveur BBB. <br>
  >> Vous pouvez récupérer cette clé à l’aide de la commande `bbb-conf --secret` sur le serveur BBB. <br>

 - `DEFAULT_MEETING_THUMBNAIL`

  > valeur par défaut : `/img/default-meeting.svg`

  >> Image par défaut affichée comme poster ou vignette, utilisée pour présenter la réunion. <br>
  >> Cette image doit se situer dans le répertoire `static`. <br>

 - `MEETING_DATE_FIELDS`

  > valeur par défaut : `()`

  >> liste des champs du formulaire de creation d’une reunion <br>
  >> les champs sont regroupés dans un ensemble de champs <br>
  >>
  >> ```
  >> MEETING_DATE_FIELDS: 
  >> ( 
  >>     "start", 
  >>     "start_time", 
  >>     "expected_duration", 
  >> ) 
  >>
  >> ```

 - `MEETING_DISABLE_RECORD`

  > valeur par défaut : `True`

  >> Mettre à True pour désactiver les enregistrements de réunion <br>
  >> Configuration de l’enregistrement des réunions. <br>
  >> Ce champ n’est pas pris en compte si `MEETING_DISABLE_RECORD = True`. <br>

 - `MEETING_MAIN_FIELDS`

  > valeur par défaut : `()`

  >> Permet de définir les champs principaux du formulaire de création d’une réunion <br>
  >> les champs principaux sont affichés directement dans la page de formulaire d’une réunion <br>
  >>
  >> ```
  >> MEETING_MAIN_FIELDS: 
  >> ( 
  >>     "name", 
  >>     "owner", 
  >>     "additional_owners", 
  >>     "attendee_password", 
  >>     "is_restricted", 
  >>     "restrict_access_to_groups", 
  >> ) 
  >>
  >> ```

 - `MEETING_MAX_DURATION`

  > valeur par défaut : `5`

  >> permet de définir la durée maximum pour une reunion <br>
  >> (en heure) <br>

 - `MEETING_PRE_UPLOAD_SLIDES`

  > valeur par défaut : ``


  >> Diaporama préchargé pour les réunions virtuelles. <br>
  >> Un utilisateur peut remplacer cette valeur en choisissant un diaporama lors de la création d'une réunion virtuelle. <br>
  >> Doit se trouver dans le répertoire statique. <br>

 - `MEETING_RECORD_FIELDS`

  > valeur par défaut : `()`

  >> ensemble des champs qui seront cachés si `MEETING_DISABLE_RECORD` est défini à true. <br>
  >>
  >> ```
  >> MEETING_RECORD_FIELDS: ("record", "auto_start_recording", "allow_start_stop_recording") 
  >>
  >> ```

 - `MEETING_RECURRING_FIELDS`

  > valeur par défaut : `()`

  >> Liste de tous les champs permettant de définir la récurrence d’une reunion <br>
  >> tous ces champs sont regroupés dans un ensemble de champs affichés dans une modale <br>
  >>
  >> ```
  >> MEETING_RECURRING_FIELDS: 
  >> ( 
  >>     "recurrence", 
  >>     "frequency", 
  >>     "recurring_until", 
  >>     "nb_occurrences", 
  >>     "weekdays", 
  >>     "monthly_type", 
  >> ) 
  >>
  >> ```

 - `RESTRICT_EDIT_MEETING_ACCESS_TO_STAFF_ONLY`

  > valeur par défaut : `False`

  >> Seuls les utilisateurs "staff" pourront éditer les réunions <br>

 - `USE_MEETING`

  > valeur par défaut : `False`

  >> Activer l’application meeting <br>

### Configuration application playlist
Application Playlist pour la gestion des playlists.<br>
Mettre `USE_PLAYLIST` à True pour activer cette application.<br>

 - `COUNTDOWN_PLAYLIST_PLAYER`

  > valeur par défaut : `0`

  >> Compte à rebours utilisé entre chaque vidéo lors de la lecture d'une playlist en lecture automatique. <br>
  >> Le compte à rebours n'est pas présent s'il est à 0. <br>

 - `DEFAULT_PLAYLIST_THUMBNAIL`

  > valeur par défaut : `/static/playlist/img/default-playlist.svg`

  >> Image par défaut affichée comme poster ou vignette, utilisée pour présenter la playlist. <br>
  >> Cette image doit se situer dans le répertoire `static`. <br>

 - `USE_FAVORITES`

  > valeur par défaut : `True`

  >> Activation des vidéos favorites. Permet aux utilisateurs d'ajouter des vidéos dans leurs favoris. <br>

 - `USE_PLAYLIST`

  > valeur par défaut : `True`

  >> Activation des playlist. Permet aux utilisateurs d'ajouter des vidéos dans une playlist. <br>

### Configuration application podfile

 - `FILES_DIR`

  > valeur par défaut : `files`

  >> Nom du répertoire racine où les fichiers "complémentaires" <br>
  >> (hors vidéos etc.) sont téléversés. Notament utilisé par PODFILE <br>
  >> À modifier principalement pour indiquer dans LOCATION votre serveur de cache si elle n’est pas sur la même machine que votre POD. <br>

 - `FILE_ALLOWED_EXTENSIONS`

  > valeur par défaut : `('doc', 'docx', 'odt', 'pdf', 'xls', 'xlsx', 'ods', 'ppt', 'pptx', 'txt', 'html', 'htm', 'vtt', 'srt')`

  >> Extensions autorisées pour les documents téléversés dans le gestionnaire de fichier (en minuscules). <br>

 - `FILE_MAX_UPLOAD_SIZE`

  > valeur par défaut : `10`

  >> Poids maximum en Mo par fichier téléversé dans le gestionnaire de fichier <br>

 - `IMAGE_ALLOWED_EXTENSIONS`

  > valeur par défaut : `('jpg', 'jpeg', 'bmp', 'png', 'gif', 'tiff', 'webp')`

  >> Extensions autorisées pour les images téléversées dans le gestionnaire de fichier. (en minuscules) <br>

### Configuration application progressive_web_app

 - `USE_NOTIFICATIONS`

  > valeur par défaut : `True`

  >> Activation des notifications, attention, elles sont actives par défaut. <br>

 - `WEBPUSH_SETTINGS`

  > valeur par défaut :

  ```python
  {
      'VAPID_PUBLIC_KEY': '',
      'VAPID_PRIVATE_KEY': '',
      'VAPID_ADMIN_EMAIL': 'contact@esup-portail.org'
  }
  ```

  >> Les clés VAPID sont nécessaires à la lib [django-webpush](https://github.com/safwanrahman/django-webpush). Elles peuvent être générées avec [https://web-push-codelab.glitch.me/]() <br>

### Configuration application recorder

 - `ALLOW_MANUAL_RECORDING_CLAIMING`

  > valeur par défaut : `False`

  >> si True, active un lien dans le menu de l’utilisateur permettant de réclamer un enregistrement <br>

 - `ALLOW_RECORDER_MANAGER_CHOICE_VID_OWNER`

  > valeur par défaut : `True`

  >> Si True, le manager de l’enregistreur pourra choisir un propriétaire de l’enregistrement. <br>

 - `DEFAULT_RECORDER_ID`

  > valeur par défaut : `1`

  >> Ajoute un enregistreur par défaut à un enregistrement non identifiable (mauvais chemin dans le dépôt FTP) <br>

 - `DEFAULT_RECORDER_PATH`

  > valeur par défaut : `/data/ftp-pod/ftp/`

  >> Chemin racine du répertoire où sont déposés les enregistrements <br>
  >> (chemin du serveur FTP). <br>

 - `DEFAULT_RECORDER_TYPE_ID`

  > valeur par défaut : `1`

  >> Identifiant du type de vidéo par défaut (si non spécifié). <br>
  >> (Exemple : 3 pour Colloque/conférence, 4 pour Cours...) <br>

 - `DEFAULT_RECORDER_USER_ID`

  > valeur par défaut : `1`

  >> Identifiant du propriétaire par défaut (si non spécifié) des enregistrements déposés. <br>

 - `OPENCAST_DEFAULT_PRESENTER`

  > valeur par défaut : `mid`

  >> Permet de spécifier la valeur par défaut du placement de la vidéo du <br>
  >> presenteur par rapport à la vidéo de présentation (écran) <br>
  >> les valeurs possibles sont : <br>
  >>  * "mid" (écran et caméra ont la même taille) <br>
  >>  * "piph" (le presenteur, caméra, est incrusté dans la vidéo de présentation, en haut à droite) <br>
  >>  * "pipb" (le presenteur, caméra, est incrusté dans la vidéo de présentation, en bas à droite) <br>
  >> Contenu par défaut du fichier xml pour créer le mediapackage pour le studio. <br>
  >> Ce fichier va contenir toutes les spécificités de l’enregistrement <br>
  >> (source, cutting, title, presenter etc.) <br>

 - `OPENCAST_FILES_DIR`

  > valeur par défaut : `opencast-files`

  >> Permet de spécifier le dossier de stockage des enregistrements du studio avant traitement. <br>

 - `OPENCAST_MEDIAPACKAGE`

  > valeur par défaut : `-> see xml content`

  >> Contenu par défaut du fichier xml pour créer le mediapackage pour le studio. Ce fichier va contenir toutes les spécificités de l’enregistrement (source, cutting, title, presenter etc.) <br>
  >>
  >> ```
  >> OPENCAST_MEDIAPACKAGE = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?> 
  >>     <mediapackage xmlns="http://mediapackage.opencastproject.org" id="" start=""> 
  >>     <media/> 
  >>     <metadata/> 
  >>     <attachments/> 
  >>     <publications/> 
  >>     </mediapackage>""" 
  >>
  >> ```

 - `PUBLIC_RECORD_DIR`

  > valeur par défaut : `records`

  >> Chemin d’accès web (public) au répertoire de dépot des enregistrements (`DEFAULT_RECORDER_PATH`). <br>
  >> Attention : penser à modifier la conf de NGINX. <br>

 - `RECORDER_ADDITIONAL_FIELDS`

  > valeur par défaut : `()`

  >> Liste des champs supplémentaires pour le formulaire des enregistreurs. Cette liste reprend le nom des champs correspondants aux paramètres d’édition d’une vidéo (Discipline, Chaine, Theme, mots clés...). <br>
  >> L’exemple suivant comporte l’ensemble des champs possibles, mais peut être allégée en fonction des besoins. <br>
  >> Les vidéos seront alors générées avec les valeurs des champs supplémentaires telles que définies dans leur enregistreur. <br>

 - `RECORDER_ALLOW_INSECURE_REQUESTS`

  > valeur par défaut : `False`

  >> Autorise la requête sur l’application en elle-même sans vérifier le certificat SSL <br>

 - `RECORDER_BASE_URL`

  > valeur par défaut : `https://pod.univ.fr`

  >> url racine de l’instance permettant l’envoi de notification lors de la réception d’enregistrement. <br>

 - `RECORDER_SELF_REQUESTS_PROXIES`

  > valeur par défaut : `{"http": None, "https": None}`

  >> Précise les proxy à utiliser pour une requête vers l’application elle même dans le cadre d’enregistrement par défaut force la non utilisation de proxy. <br>

 - `RECORDER_SKIP_FIRST_IMAGE`

  > valeur par défaut : `False`

  >> Si True, permet de ne pas prendre en compte la 1ère image lors du traitement d’un fichier d’enregistrement de type AudioVideoCast. <br>

 - `RECORDER_TYPE`

  > valeur par défaut : `(('video', _('Video')), ('audiovideocast', _('Audiovideocast')), ('studio', _('Studio')))`

  >> Type d’enregistrement géré par la plateforme. <br>
  >> Un enregistreur ne peut déposer que des fichiers de type proposé par la plateforme. <br>
  >> Le traitement se fait en fonction du type de fichier déposé. <br>

 - `USE_OPENCAST_STUDIO`

  > valeur par défaut : `False`

  >> Activer l’utilisation du studio Opencast. <br>

 - `USE_RECORD_PREVIEW`

  > valeur par défaut : `False`

  >> Si True, affiche l’icone de prévisualisation des vidéos dans la page "Revendiquer un enregistrement". <br>

### Configuration application vidéo.

 - `ACTIVE_VIDEO_COMMENT`

  > valeur par défaut : `False`

  >> Activer les commentaires au niveau de la plateforme <br>

 - `CACHE_VIDEO_DEFAULT_TIMEOUT`

  > valeur par défaut : `600`


  >> Temps en seconde de conservation des données de l'application video <br>

 - `CHANNEL_FORM_FIELDS_HELP_TEXT`

  > valeur par défaut : ``

  >> Ensemble des textes d’aide affichés avec le formulaire d’édition de chaine. <br>
  >> voir pod/video/forms.py <br>

 - `CHUNK_SIZE`

  > valeur par défaut : `1000000`

  >> Taille d’un fragment lors de l’envoi d’une vidéo <br>
  >> le fichier sera mis en ligne par fragment de cette taille. <br>

 - `CURSUS_CODES`

  > valeur par défaut : `()`

  >> Liste des cursus proposés lors de l’ajout des vidéos. <br>
  >> Affichés en dessous d’une vidéos, ils sont aussi utilisés pour affiner la recherche. <br>
  >>
  >> ```
  >> CURSUS_CODES = ( 
  >>     ('0', _("None / All")), 
  >>     ('L', _("Bachelor’s Degree")), 
  >>     ('M', _("Master’s Degree")), 
  >>     ('D', _("Doctorate")), 
  >>     ('1', _("Other")) 
  >> ) 
  >>
  >> ```

 - `DEFAULT_DC_COVERAGE`

  > valeur par défaut : `TITLE_ETB + " - Town - Country"`

  >> couverture du droit pour chaque vidéo <br>

 - `DEFAULT_DC_RIGHTS`

  > valeur par défaut : `BY-NC-SA`

  >> droit par défaut affichés dans le flux RSS si non renseigné <br>

 - `DEFAULT_THUMBNAIL`

  > valeur par défaut : `img/default.svg`

  >> Image par défaut affichée comme poster ou vignette, utilisée pour présenter la vidéo. <br>
  >> Cette image doit se situer dans le répertoire static. <br>

 - `DEFAULT_TYPE_ID`

  > valeur par défaut : `1`

  >> Les vidéos créées sans type (par importation par exemple) seront affectées au type par défaut (en général, le type ayant pour identifiant '1' est 'Other') <br>

 - `DEFAULT_YEAR_DATE_DELETE`

  > valeur par défaut : `2`

  >> Durée d’obsolescence par défaut (en années après la date d’ajout). <br>

 - `FORCE_LOWERCASE_TAGS`

  > valeur par défaut : `True`

  >> Les mots clés saisis lors de l’ajout de vidéo sont convertis automatiquement en minuscule. <br>

 - `LANG_CHOICES`

  > valeur par défaut : ``

  >> Liste des langues proposées lors de l’ajout des vidéos. <br>
  >> Affichés en dessous d’une vidéos, les choix sont aussi utilisés pour affiner la recherche. <br>

 - `LICENCE_CHOICES`

  > valeur par défaut : `()`

  >> Licence proposées pour les vidéos en creative commons :  <br>
  >>
  >> ```
  >> LICENCE_CHOICES = ( 
  >>     ('by', ("Attribution 4.0 International (CC BY 4.0)")), 
  >>     ('by-nd', ("Attribution-NoDerivatives 4.0 " 
  >>                "International (CC BY-ND 4.0)")), 
  >>     ('by-nc-nd', ("Attribution-NonCommercial-NoDerivatives 4.0 " 
  >>                   "International (CC BY-NC-ND 4.0)")), 
  >>     ('by-nc', ("Attribution-NonCommercial 4.0 " 
  >>                "International (CC BY-NC 4.0)")), 
  >>     ('by-nc-sa', ("Attribution-NonCommercial-ShareAlike 4.0 " 
  >>                   "International (CC BY-NC-SA 4.0)")), 
  >>     ('by-sa', ("Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)")) 
  >> ) 
  >>
  >> ```

 - `MAX_DURATION_DATE_DELETE`

  > valeur par défaut : `10`

  >> Fixe une durée maximale que la date de suppression d’une vidéo ne peut dépasser. <br>
  >> Par défaut : 10 (Année courante + 10 ans). <br>

 - `MAX_TAG_LENGTH`

  > valeur par défaut : `50`

  >> Les mots clés saisis lors de l’ajout de vidéo ne peuvent dépasser cette longueur. <br>

 - `NOTES_STATUS`

  > valeur par défaut : `()`

  >> Valeurs possible pour l’accès à une note. <br>
  >>
  >> ```
  >> NOTES_STATUS = ( 
  >>     ("0", _("Private (me only)")), 
  >>     ("1", _("Shared with video owner")), 
  >>     ("2", _("Public")), 
  >> ) 
  >>
  >> ```

 - `OEMBED`

  > valeur par défaut : `False`

  >> Permettre l’usage du oembed, partage dans Moodle, Facebook, Twitter etc. <br>

 - `ORGANIZE_BY_THEME`

  > valeur par défaut : `False`

  >> Affichage uniquement des vidéos de la chaîne ou du thème actuel(le). <br>
  >> Affichage des sous-thèmes directs de la chaîne ou du thème actuel(le) <br>

 - `RESTRICT_EDIT_VIDEO_ACCESS_TO_STAFF_ONLY`

  > valeur par défaut : `False`

  >> Si True, seule les personnes "Staff" peuvent déposer des vidéos <br>

 - `THEME_FORM_FIELDS_HELP_TEXT`

  > valeur par défaut : `""`

  >> Ensemble des textes d’aide affichés avec le formulaire d’édition de theme. <br>
  >> voir pod/video/forms.py <br>
  >>
  >> ```
  >> THEME_FORM_FIELDS_HELP_TEXT = OrderedDict( 
  >>     [ 
  >>         ( 
  >>             "{0}".format(_("Title field")), 
  >>             [ 
  >>                 _( 
  >>                     "Please choose a title as short and accurate as possible, " 
  >>                     "reflecting the main subject / context of the content." 
  >>                 ), 
  >>                 _( 
  >>                     "You can use the “Description” field below for all " 
  >>                     "additional information." 
  >>                 ), 
  >>             ], 
  >>         ), 
  >>         ( 
  >>             "{0}".format(_("Description")), 
  >>             [ 
  >>                 _( 
  >>                     "In this field you can describe your content, add all needed " 
  >>                     "related information, and format the result " 
  >>                     "using the toolbar." 
  >>                 ) 
  >>             ], 
  >>         ), 
  >>     ] 
  >> ) 
  >>
  >> ```

 - `USER_VIDEO_CATEGORY`

  > valeur par défaut : `False`

  >> Permet d’activer le fonctionnement de categorie au niveau de ses vidéos. <br>
  >> Vous pouvez créer des catégories pour pouvoir ranger vos propres vidéos. <br>
  >> Les catégories sont liées à l’utilisateur. <br>

 - `USE_OBSOLESCENCE`

  > valeur par défaut : `False`

  >> Activation de l’obsolescence des video. Permet d’afficher la date de suppression de la video <br>
  >> dans le formulaire d’edition et dans la partie admin. <br>

 - `USE_STATS_VIEW`

  > valeur par défaut : `False`

  >> Permet d’activer la possibilité de voir en details le nombre de visualisation d’une vidéo durant un jour donné ou mois, <br>
  >> année ou encore le nombre de vue total depuis la création de la vidéo. <br>
  >> Un lien est rajouté dans la partie info lors de la lecture d’une vidéo, un lien est rajouté dans la page de visualisation d’une chaîne ou un theme <br>
  >> ou encore toutes les vidéos présentes sur la plateforme. <br>

 - `USE_VIDEO_EVENT_TRACKING`

  > valeur par défaut : `False`

  >> Ce paramètre permet d’activer l’envoi d’évènements sur le lecteur vidéo à Matomo. <br>
  >> N’est utile que si le code piwik / matomo est présent dans l’instance de Esup-Pod. <br>
  >> Les évènements envoyés sont : <br>
  >>    play, pause, seeked, ended, ratechange, fullscreen, error, loadmetadata <br>
  >> Pour rajouter le code Piwik/Matomo dans votre instance de Pod, il suffit de créer un fichier `pod/custom/templates/custom/tracking.html` <br>
  >> Il faut ensuite y insérer le code javascript puis dans votre fichier `settings_local.py`, <br>
  >> de préciser dans la variable `TEMPLATE_VISIBLE_SETTINGS`: `'TRACKING_TEMPLATE': 'custom/tracking.html'` <br>

 - `USE_XAPI_VIDEO`

  > valeur par défaut : `False`


  >> Active l‘envoi d’instructions xAPI pour le lecteur vidéo. <br>
  >> Attention, il faut mettre USE_XAPI à True pour que les instructions soient envoyées. <br>

 - `VIDEO_ALLOWED_EXTENSIONS`

  > valeur par défaut : `()`

  >> Extensions autorisées pour le téléversement vidéo sur la plateforme (en minuscules). <br>
  >>
  >> ```
  >> VIDEO_ALLOWED_EXTENSIONS = ( 
  >>     "3gp", 
  >>     "avi", 
  >>     "divx", 
  >>     "flv", 
  >>     "m2p", 
  >>     "m4v", 
  >>     "mkv", 
  >>     "mov", 
  >>     "mp4", 
  >>     "mpeg", 
  >>     "mpg", 
  >>     "mts", 
  >>     "wmv", 
  >>     "mp3", 
  >>     "ogg", 
  >>     "wav", 
  >>     "wma", 
  >>     "webm", 
  >>     "ts", 
  >> ) 
  >>
  >> ```

 - `VIDEO_FEED_NB_ITEMS`

  > valeur par défaut : `100`


  >> nombre d'item renvoyé par le flux rss <br>

 - `VIDEO_FORM_FIELDS`

  > valeur par défaut : `__all__`

  >> Liste des champs du formulaire d’édition de vidéos affichées. <br>

 - `VIDEO_FORM_FIELDS_HELP_TEXT`

  > valeur par défaut : ``

  >> Ensemble des textes d’aide affichés avec le formulaire d’envoi de vidéo. <br>
  >>
  >> ```
  >> VIDEO_FORM_FIELDS_HELP_TEXT = OrderedDict( 
  >>     [ 
  >>         ( 
  >>             "{0}".format(_("File field")), 
  >>             [ 
  >>                 _("You can send an audio or video file."), 
  >>                 _("The following formats are supported: %s") 
  >>                 % ", ".join(map(str, VIDEO_ALLOWED_EXTENSIONS)), 
  >>             ], 
  >>         ), 
  >>         ( 
  >>             "{0}".format(_("Title field")), 
  >>             [ 
  >>                 _( 
  >>                     "Please choose a title as short and accurate as possible, " 
  >>                     "reflecting the main subject / context of the content." 
  >>                 ), 
  >>                 _( 
  >>                     "You can use the “Description” field below for all " 
  >>                     "additional information." 
  >>                 ), 
  >>                 _( 
  >>                     "You may add contributors later using the second button of " 
  >>                     "the content edition toolbar: they will appear in the “Info” " 
  >>                     "tab at the bottom of the audio / video player." 
  >>                 ), 
  >>             ], 
  >>         ), 
  >>         ( 
  >>             "{0}".format(_("Type")), 
  >>             [ 
  >>                 _( 
  >>                     "Select the type of your content. If the type you wish does " 
  >>                     "not appear in the list, please temporary select “Other” " 
  >>                     "and contact us to explain your needs." 
  >>                 ) 
  >>             ], 
  >>         ), 
  >>         ( 
  >>             "{0}".format(_("Additional owners")), 
  >>             [ 
  >>                 _( 
  >>                     "In this field you can select and add additional owners to the " 
  >>                     "video. These additional owners will have the same rights as " 
  >>                     "you except that they can't delete this video." 
  >>                 ) 
  >>             ], 
  >>         ), 
  >>         ( 
  >>             "{0}".format(_("Description")), 
  >>             [ 
  >>                 _( 
  >>                     "In this field you can describe your content, add all needed " 
  >>                     "related information, and format the result " 
  >>                     "using the toolbar." 
  >>                 ) 
  >>             ], 
  >>         ), 
  >>         ( 
  >>             "{0}".format(_("Date of the event field")), 
  >>             [ 
  >>                 _( 
  >>                     "Enter the date of the event, if applicable, in the " 
  >>                     "AAAA-MM-JJ format." 
  >>                 ) 
  >>             ], 
  >>         ), 
  >>         ( 
  >>             "{0}".format(_("University course")), 
  >>             [ 
  >>                 _( 
  >>                     "Select an university course as audience target of " 
  >>                     "the content." 
  >>                 ), 
  >>                 _( 
  >>                     "Choose “None / All” if it does not apply or if all are " 
  >>                     "concerned, or “Other” for an audience outside " 
  >>                     "the european LMD scheme." 
  >>                 ), 
  >>             ], 
  >>         ), 
  >>         ( 
  >>             "{0}".format(_("Main language")), 
  >>             [_("Select the main language used in the content.")], 
  >>         ), 
  >>         ( 
  >>             "{0}".format(_("Tags")), 
  >>             [ 
  >>                 _( 
  >>                     "Please try to add only relevant keywords that can be " 
  >>                     "useful to other users." 
  >>                 ) 
  >>             ], 
  >>         ), 
  >>         ( 
  >>             "{0}".format(_("Disciplines")), 
  >>             [ 
  >>                 _( 
  >>                     "Select the discipline to which your content belongs. " 
  >>                     "If the discipline you wish does not appear in the list, " 
  >>                     "please select nothing and contact us to explain your needs." 
  >>                 ), 
  >>                 _( 
  >>                     'Hold down "Control", or "Command" on a Mac, ' 
  >>                     "to select more than one." 
  >>                 ), 
  >>             ], 
  >>         ), 
  >>         ( 
  >>             "{0}".format(_("Licence")), 
  >>             [ 
  >>                 ( 
  >>                     '<a href="https://creativecommons.org/licenses/by/4.0/" ' 
  >>                     'title="%(lic)s" target="_blank">%(lic)s</a>' 
  >>                 ) 
  >>                 % {"lic": _("Attribution 4.0 International (CC BY 4.0)")}, 
  >>                 ( 
  >>                     '<a href="https://creativecommons.org/licenses/by-nd/4.0/" ' 
  >>                     'title="%(lic)s" target="_blank">%(lic)s</a>' 
  >>                 ) 
  >>                 % { 
  >>                     "lic": _( 
  >>                         "Attribution-NoDerivatives 4.0 " 
  >>                         "International (CC BY-ND 4.0)" 
  >>                     ) 
  >>                 }, 
  >>                 ( 
  >>                     '<a href="https://creativecommons.org/licenses/by-nc-nd/4.0/" ' 
  >>                     'title="%(lic)s" target="_blank">%(lic)s</a>' 
  >>                 ) 
  >>                 % { 
  >>                     "lic": _( 
  >>                         "Attribution-NonCommercial-NoDerivatives 4.0 " 
  >>                         "International (CC BY-NC-ND 4.0)" 
  >>                     ) 
  >>                 }, 
  >>                 ( 
  >>                     '<a href="https://creativecommons.org/licenses/by-nc/4.0/" ' 
  >>                     'title="%(lic)s" target="_blank">%(lic)s</a>' 
  >>                 ) 
  >>                 % { 
  >>                     "lic": _( 
  >>                         "Attribution-NonCommercial 4.0 " 
  >>                         "International (CC BY-NC 4.0)" 
  >>                     ) 
  >>                 }, 
  >>                 ( 
  >>                     '<a href="https://creativecommons.org/licenses/by-nc-sa/4.0/" ' 
  >>                     'title="%(lic)s" target="_blank">%(lic)s</a>' 
  >>                 ) 
  >>                 % { 
  >>                     "lic": _( 
  >>                         "Attribution-NonCommercial-ShareAlike 4.0 " 
  >>                         "International (CC BY-NC-SA 4.0)" 
  >>                     ) 
  >>                 }, 
  >>                 ( 
  >>                     '<a href="https://creativecommons.org/licenses/by-sa/4.0/" ' 
  >>                     'title="%(lic)s" target="_blank">%(lic)s</a>' 
  >>                 ) 
  >>                 % { 
  >>                     "lic": _( 
  >>                         "Attribution-ShareAlike 4.0 " "International (CC BY-SA 4.0)" 
  >>                     ) 
  >>                 }, 
  >>             ], 
  >>         ), 
  >>         ( 
  >>             "{0} / {1}".format(_("Channels"), _("Themes")), 
  >>             [ 
  >>                 _("Select the channel in which you want your content to appear."), 
  >>                 _( 
  >>                     "Themes related to this channel will " 
  >>                     "appear in the “Themes” list below." 
  >>                 ), 
  >>                 _( 
  >>                     'Hold down "Control", or "Command" on a Mac, ' 
  >>                     "to select more than one." 
  >>                 ), 
  >>                 _( 
  >>                     "If the channel or Themes you wish does not appear " 
  >>                     "in the list, please select nothing and contact " 
  >>                     "us to explain your needs." 
  >>                 ), 
  >>             ], 
  >>         ), 
  >>         ( 
  >>             "{0}".format(_("Draft")), 
  >>             [ 
  >>                 _( 
  >>                     "In “Draft mode”, the content shows nowhere and nobody " 
  >>                     "else but you can see it." 
  >>                 ) 
  >>             ], 
  >>         ), 
  >>         ( 
  >>             "{0}".format(_("Restricted access")), 
  >>             [ 
  >>                 _( 
  >>                     "If you don't select “Draft mode”, you can restrict " 
  >>                     "the content access to only people who can log in" 
  >>                 ) 
  >>             ], 
  >>         ), 
  >>         ( 
  >>             "{0}".format(_("Password")), 
  >>             [ 
  >>                 _( 
  >>                     "If you don't select “Draft mode”, you can add a password " 
  >>                     "which will be asked to anybody willing to watch " 
  >>                     "your content." 
  >>                 ), 
  >>                 _( 
  >>                     "If your video is in a playlist the password of your " 
  >>                     "video will be removed automatically." 
  >>                 ), 
  >>             ], 
  >>         ), 
  >>     ] 
  >> ) 
  >>
  >> ```

 - `VIDEO_MAX_UPLOAD_SIZE`

  > valeur par défaut : `1`

  >> Taille maximum en Go des fichiers téléversés sur la plateforme. <br>

 - `VIDEO_PLAYBACKRATES`

  > valeur par défaut : `[0.5, 1, 1.5, 2]`

  >> Configuration des choix de vitesse de lecture pour le lecteur vidéo. <br>

 - `VIDEO_RECENT_VIEWCOUNT`

  > valeur par défaut : `180`

  >> Durée (en nombre de jours) sur laquelle on souhaite compter le nombre de vues récentes. <br>

 - `VIDEO_REQUIRED_FIELDS`

  > valeur par défaut : `[]`

  >> Permet d’ajouter l’attribut obligatoire dans le formulaire d’edition et d’ajout d’une video : <br>
  >> Exemple de valeur : ["discipline", "tags"] <br>
  >> NB : les champs cachés et suivant ne sont pas pris en compte : <br>
  >>
  >> `(video, title, type, owner, date_added, cursus, main_lang)`

 - `VIEW_STATS_AUTH`

  > valeur par défaut : `False`

  >> Réserve l’accès aux statistiques des vidéos aux personnes authentifiées. <br>

### Configuration application video encodage et transcription

Application pour l’encodage et la transcription de vidéo.<br>
Il est possible d'encoder en local ou en distant.<br>
Attention, il faut configurer Celery pour l’envoi des instructions pour l'encodage distant.<br>

 - `CELERY_BROKER_URL`

  > valeur par défaut : `amqp://pod:xxx@localhost/rabbitpod`

  >> URL de Celery pour la gestion des taches d’encodage. <br>

 - `CELERY_TO_ENCODE`

  > valeur par défaut : `False`

  >> Utilisation de Celery pour la gestion des taches d’encodage <br>

 - `DEFAULT_LANG_TRACK`

  > valeur par défaut : `fr`

  >> langue par défaut pour l’ajout de piste à une vidéo. <br>

 - `EMAIL_ON_ENCODING_COMPLETION`

  > valeur par défaut : `True`

  >> Si True, un courriel est envoyé aux managers et à l’auteur (si DEBUG est à False) à la fin de l’encodage. <br>

 - `EMAIL_ON_TRANSCRIPTING_COMPLETION`

  > valeur par défaut : `True`

  >> Si True, un courriel est envoyé aux managers et à l’auteur (si DEBUG est à False) à la fin de la transcription <br>

 - `ENCODE_STUDIO`

  > valeur par défaut : `start_encode_studio`

  >> Fonction appelée pour lancer l’encodage du studio (merge and cut). <br>

 - `ENCODE_VIDEO`

  > valeur par défaut : `start_encode`

  >> Fonction appelée pour lancer l’encodage des vidéos direct par thread ou distant par celery <br>

 - `ENCODING_CHOICES`

  > valeur par défaut : `()`

  >> Encodage possible sur la plateforme. Associé à un rendu dans le cas d’une vidéo. <br>
  >>
  >> ```
  >> ENCODING_CHOICES = ( 
  >>     ("audio", "audio"), 
  >>     ("360p", "360p"), 
  >>     ("480p", "480p"), 
  >>     ("720p", "720p"), 
  >>     ("1080p", "1080p"), 
  >>     ("playlist", "playlist") 
  >> ) 
  >>
  >> ```

 - `ENCODING_TRANSCODING_CELERY_BROKER_URL`

  > valeur par défaut : `False`


  >> Il faut renseigner l'url du redis sur lequel Celery va chercher les ordres d'encodage et de transcription <br>
  >> par exemple : "redis://redis:6379/7" <br>

 - `FORMAT_CHOICES`

  > valeur par défaut : `()`

  >> Format d’encodage réalisé sur la plateforme. <br>
  >>
  >> ```
  >> FORMAT_CHOICES = ( 
  >>     ("video/mp4", "video/mp4"), 
  >>     ("video/mp2t", "video/mp2t"), 
  >>     ("video/webm", "video/webm"), 
  >>     ("audio/mp3", "audio/mp3"), 
  >>     ("audio/wav", "audio/wav"), 
  >>     ("application/x-mpegURL", "application/x-mpegURL"), 
  >> ) 
  >>
  >> ```

 - `USE_DISTANT_ENCODING_TRANSCODING`

  > valeur par défaut : `False`


  >> Si True, active l'encodage et la transcription sur un environnement distant via redis+celery <br>

 - `VIDEO_RENDITIONS`

  > valeur par défaut : `[]`

  >> Rendu serializé pour l’encodage des videos. <br>
  >> Cela permet de pouvoir encoder les vidéos sans l’environnement de Pod. <br>
  >>
  >> ```
  >> VIDEO_RENDITIONS = [ 
  >>     { 
  >>         "resolution": "640x360", 
  >>         "minrate": "500k", 
  >>         "video_bitrate": "750k", 
  >>         "maxrate": "1000k", 
  >>         "audio_bitrate": "96k", 
  >>         "encoding_resolution_threshold": 0, 
  >>         "encode_mp4": True, 
  >>         "sites": [1], 
  >>     },{ 
  >>         "resolution": "1280x720", 
  >>         "minrate": "1000k", 
  >>         "video_bitrate": "2000k", 
  >>         "maxrate": "3000k", 
  >>         "audio_bitrate": "128k", 
  >>         "encoding_resolution_threshold": 0, 
  >>         "encode_mp4": True, 
  >>         "sites": [1], 
  >>     },{ 
  >>         "resolution": "1920x1080", 
  >>         "minrate": "2000k", 
  >>         "video_bitrate": "3000k", 
  >>         "maxrate": "4500k", 
  >>         "audio_bitrate": "192k", 
  >>         "encoding_resolution_threshold": 0, 
  >>         "encode_mp4": False, 
  >>         "sites": [1], 
  >>     }, 
  >> ] 
  >>
  >> ```

### Configuration application search

 - `ES_INDEX`

  > valeur par défaut : `pod`

  >> Valeur pour l’index de ElasticSearch <br>

 - `ES_MAX_RETRIES`

  > valeur par défaut : `10`

  >> Valeur max de tentatives pour ElasticSearch. <br>

 - `ES_TIMEOUT`

  > valeur par défaut : `30`

  >> Valeur de timeout pour ElasticSearch. <br>

 - `ES_URL`

  > valeur par défaut : `["http://127.0.0.1:9200/"]`

  >> Adresse du ou des instances d’Elasticsearch utilisées pour l’indexation et la recherche de vidéo. <br>

 - `ES_VERSION`

  > valeur par défaut : `6`

  >> Version d’ElasticSearch. <br>
  >> valeurs possibles 6, 7 ou 8 correspondant à la version du Elasticsearch utilisé. <br>
  >> Pour utiliser la version 7 ou 8, faire une mise à jour du paquet elasticsearch-py  <br>
  >> Pour la 7, `pip3 install elasticsearch==7.17.7`, <br>
  >> et pour la 8, `pip3 install elasticsearch==8.8.1`. <br>
  >> Voir [https://elasticsearch-py.readthedocs.io/]() pour plus d'information. <br>

### Configuration application xapi

Application pour l’envoi d‘instructions xAPI à un LRS.<br>
Aucune instruction ne persiste dans Pod, elles sont toutes envoyées au LRS paramétré.<br>
Attention, il faut configurer Celery pour l’envoi des instructions.<br>

 - `USE_XAPI`

  > valeur par défaut : `False`


  >> Activation de l'application xAPI <br>

 - `XAPI_ANONYMIZE_ACTOR`

  > valeur par défaut : `True`


  >> Si False, le nom de l'utilisateur sera stocké en clair dans les statements xAPI, si True, son nom d'utilisateur sera anonymisé <br>

 - `XAPI_LRS_LOGIN`

  > valeur par défaut : ``


  >> identifiant de connexion du LRS pour l'envoi des statements <br>

 - `XAPI_LRS_PWD`

  > valeur par défaut : ``


  >> mot de passe de connexion du LRS pour l'envoi des statements <br>

 - `XAPI_LRS_URL`

  > valeur par défaut : ``


  >> URL de destination pour l'envoi des statements. I.E. : https://ralph.univ.fr/xAPI/statements <br>