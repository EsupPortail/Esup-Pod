# Configuration de la plateforme Esup-Pod

> [!IMPORTANT]
> Cette documentation est une référence pour les variables historiques du projet.
> Pour comprendre **comment configurer** votre instance (fichiers de surcharge, hiérarchie), merci de vous référer au guide principal : **[Documentation de Configuration (EN)](configuration.md)**.

## Informations générales


La plateforme Esup-Pod se base sur le framework Django écrit en Python.<br>
Elle est compatible avec les versions 3.9, 3.10 et 3.12 de Python.<br>

**Django Version : 4.2 LTS**<br>

> La documentation complète du framework : [docs.djangoproject.com](https://docs.djangoproject.com/fr/4.2/)<br><br>
> L’ensemble des variables de configuration du framework est accessible à cette adresse : [docs.djangoproject.com](https://docs.djangoproject.com/fr/4.2/ref/settings/)<br>

Voici les configurations des applications tierces utilisées par Esup-Pod.<br>

* `CAS`
  > default value: `1.5.3`
  >> Système d’authentification SSO_CAS<br>
  >> [kstateome/django-cas](https://github.com/kstateome/django-cas)<br>
* `ModelTranslation`
  > default value: `0.19.11`
  >> L’application modeltranslation est utilisée pour traduire le contenu dynamique<br>
  >> des modèles Django existants<br>
  >> [django-modeltranslation.readthedocs.io](https://django-modeltranslation.readthedocs.io/en/latest/installation.html#configuration)<br>
* `captcha`
  > default value: `0.6.0`
  >> Gestion du captcha du formulaire de contact<br>
  >> [django-simple-captcha.readthedocs.io](https://django-simple-captcha.readthedocs.io/en/latest/usage.html)<br>
* `chunked_upload`
  > default value: `2.0.0`
  >> Envoi de fichier par morceaux // voir pour mettre à jour si nécessaire<br>
  >> [juliomalegria/django-chunked-upload](https://github.com/juliomalegria/django-chunked-upload)<br>
* `ckeditor`
  > default value: `6.3.0`
  >> ATTENTION. django-ckeditor integre la version gratuite de CKEditor 4.22.1,<br>
  >> qui n'est plus prise en charge et qui présente des problèmes de sécurité non résolus,<br>
  >> voir par exemple <https://ckeditor.com/cke4/release/CKEditor-4.24.0-LTS>.<br>
* `django_select2`
  > default value: `latest`
  >> Recherche et completion dans les formulaires<br>
  >> [django-select2.readthedocs.io](https://django-select2.readthedocs.io/en/latest/)<br>
* `honeypot`
  > default value: `1.2.1`
  >> Utilisé pour le formulaire de contact de Pod -<br>
  >> ajoute un champ caché pour diminuer le spam<br>
  >> [jamesturk/django-honeypot](https://github.com/jamesturk/django-honeypot/)<br>
* `mozilla_django_oidc`
  > default value: `4.0.1`
  >> Système d’authentification OpenID Connect<br>
  >> [mozilla-django-oidc.readthedocs.io](https://mozilla-django-oidc.readthedocs.io/en/stable/installation.html)<br>
* `pwa`
  > default value: `2.0.1`
  >> Mise en place du mode PWA grâce à l’application Django-pwa<br>
  >> Voici la configuration par défaut pour Pod,<br>
  >> vous pouvez surcharger chaque variable dans votre fichier de configuration.<br>
  >>
  >> ```python
  >> PWA_APP_NAME = "Pod"
  >> PWA_APP_DESCRIPTION = (
  >>     "Pod is aimed at users of our institutions, by allowing the publication of "
  >>     "videos in the fields of research (promotion of platforms, etc.), training "
  >>     "(tutorials, distance training, student reports, etc.), institutional life "
  >>     "(video of events), offering several days of content."
  >> )
  >> PWA_APP_THEME_COLOR = "#0A0302"
  >> PWA_APP_BACKGROUND_COLOR = "#ffffff"
  >> PWA_APP_DISPLAY = "standalone"
  >> PWA_APP_SCOPE = "/"
  >> PWA_APP_ORIENTATION = "any"
  >> PWA_APP_START_URL = "/"
  >> PWA_APP_STATUS_BAR_COLOR = "default"
  >> PWA_APP_DIR = "ltr"
  >> PWA_APP_LANG = "fr-FR"
  >> ```
  >>
  >> Pour en savoir plus : [silviolleite/django-pwa](https://github.com/silviolleite/django-pwa)<br>
* `rest_framework`
  > default value: `3.15.2`
  >> mise en place de l’API rest pour l’application<br>
  >> [django-rest-framework.org](https://www.django-rest-framework.org/)<br>
* `shibboleth`
  > default value: `latest`
  >> Système d’authentification Shibboleth<br>
  >> [Brown-University-Library/django-shibboleth-remoteuser](https://github.com/Brown-University-Library/django-shibboleth-remoteuser)<br>
* `sorl.thumbnail`
  > default value: `12.11.0`
  >> Utilisée pour la génération de miniature des images<br>
  >> [sorl-thumbnail.readthedocs.io](https://sorl-thumbnail.readthedocs.io/en/latest/reference/settings.html)<br>
* `tagging`
  > default value: `0.5.0`
  >> Gestion des mots-clés associés à une vidéo // voir pour référencer une nouvelle application<br>
  >> [django-tagging.readthedocs.io](https://django-tagging.readthedocs.io/en/develop/#settings)<br>
* `tagulous`
  > default value: `2.1.0`
  >> Gestion des mots-clés associés à un objet Django.<br>
  >> [django-tagulous.readthedocs.io](https://django-tagulous.readthedocs.io)<br>

## Configuration générale de la plateforme Esup_Pod

### Base de données

* `DATABASES`
  > default value:

  ```python
  {
      'default': {
          'ENGINE': 'django.db.backends.sqlite3',
          'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
      }
  }
  ```

  >> Un dictionnaire contenant les réglages de toutes les bases de données<br>
  >> à utiliser avec Django.<br>
  >> C’est un dictionnaire imbriqué dont les contenus font correspondre<br>
  >> l’alias de base de données avec un dictionnaire contenant<br>
  >> les options de chacune des bases de données.<br>
  >> _ref : [docs.djangoproject.com](https://docs.djangoproject.com/fr/4.2/ref/settings/#databases)_<br>
  >> valeur par défaut : une base de données au format sqlite<br>
  >> Voici un exemple de configuration pour utiliser une base MySQL :<br>
  >>
  >> ```python
  >> DATABASES = {
  >>     'default': {
  >>         'ENGINE': 'django.db.backends.mysql',
  >>         'NAME': 'pod',
  >>         'USER': 'pod',
  >>         'PASSWORD': 'password',
  >>         'HOST': 'mysql.univ.fr',
  >>         'PORT': '3306',
  >>         'OPTIONS': {
  >>             'init_command': "SET storage_engine=INNODB, sql_mode='STRICT_TRANS_TABLES',
  >>              innodb_strict_mode=1, foreign_key_checks = 1",
  >>          },
  >>     }
  >> }
  >> ```
  >>

### Courriel

* `CONTACT_US_EMAIL`
  > default value: ``
  >> Liste des adresses destinataires des courriels de contact<br>
* `CUSTOM_CONTACT_US`
  > default value: `False`
  >> Si 'True', les e-mails de contacts seront adressés, selon le sujet,<br>
  >> soit au propriétaire de la vidéo soit au(x) manager(s) des vidéos Pod.<br>
  >> (voir `USER_CONTACT_EMAIL_CASE` et `USE_ESTABLISHMENT_FIELD`)<br>
* `DEFAULT_FROM_EMAIL`
  > default value: `noreply`
  >> Expediteur par défaut pour les envois de courriel (contact, encodage etc.)<br>
* `EMAIL_BACKEND`
  > default value: `django.core.mail.backends.smtp.EmailBackend`
  >> Le backend à utiliser pour l'envoi de courriels.<br>
* `EMAIL_HOST`
  > default value: `smtp.univ.fr`
  >> nom du serveur smtp<br>
  >> _ref : [docs.djangoproject.com](https://docs.djangoproject.com/fr/4.2/ref/settings/#email-host)_<br>
* `EMAIL_HOST_PASSWORD`
  > default value: ``
  >> Mot de passe à utiliser pour le serveur SMTP défini dans EMAIL_HOST.<br>
* `EMAIL_HOST_USER`
  > default value: ``
  >> Nom d'utilisateur à utiliser pour le serveur SMTP défini dans EMAIL_HOST.<br>
* `EMAIL_PORT`
  > default value: `25`
  >> Port d’écoute du serveur SMTP.<br>
* `EMAIL_SUBJECT_PREFIX`
  > default value: ``
  >> Préfixe par défaut pour l’objet des courriels.<br>
* `EMAIL_USE_TLS`
  > default value: `False`
  >> Indique s'il faut utiliser une connexion TLS (sécurisée) lors de la communication avec le serveur SMTP.<br>
* `NOTIFY_SENDER`
  > default value: `True`
  >> En mode non authentifié, lors de l'utilisation du formulaire de contact, envoie une copie du message à l'adresse saisie dans le formulaire.<br>
* `SERVER_EMAIL`
  > default value: `noreply`
  >> Expediteur par défaut pour les envois automatique (erreur de code etc.)<br>
* `SUBJECT_CHOICES`
  > default value: `()`
  >> Choix de sujet pour les courriels envoyés depuis la plateforme<br>
  >>
  >> ```python
  >> SUBJECT_CHOICES = (
  >>     ('', '-----'),
  >>     ('info', ('Request more information')),
  >>     ('contribute', ('Learn more about how to contribute')),
  >>     ('request_password', ('Password request for a video')),
  >>     ('inappropriate_content', ('Report inappropriate content')),
  >>     ('bug', ('Correction or bug report')),
  >>     ('other', ('Other (please specify)'))
  >> )
  >> ```
  >>
* `SUPPORT_EMAIL`
  > default value: `None`
  >> Liste de destinataire(s) pour les demandes d’assistance, si différent de `CONTACT_US_EMAIL`<br>
  >> i.e.: `SUPPORT_EMAIL = ["assistance_pod@univ.fr"]`<br>
* `USER_CONTACT_EMAIL_CASE`
  > default value: ``
  >> Une liste contenant les sujets de contact dont l’utilisateur<br>
  >> sera seul destinataire plutôt que le(s) manager(s).<br>
  >> Si la liste est vide, les mails de contact seront envoyés au(x) manager(s).<br>
  >> Valeurs possibles :<br>
  >> `info`, `contribute`, `request_password`,<br>
  >> `inapropriate_content`, `bug`, `other`<br>
* `USE_ESTABLISHMENT_FIELD`
  > default value: `False`
  >> Si valeur vaut 'True', rajoute un attribut 'establishment'<br>
  >> à l’utilisateur Pod, ce qui permet de gérer plus d’un établissement.<br>
  >> Dans ce cas, les emails de contact par exemple seront envoyés<br>
  >> soit à l’utilisateur soit au(x) manager(s)<br>
  >> de l’établissement de l’utilisateur.<br>
  >> (voir `USER_CONTACT_EMAIL_CASE`)<br>
  >> Également, les emails de fin d’encodage seront envoyés au(x) manager(s)<br>
  >> de l’établissement du propriétaire de la vidéo encodée,<br>
  >> en plus d’un email au propriétaire confirmant la fin d’encodage d’une vidéo.<br>

### Encodage

* `FFMPEG_AUDIO_BITRATE`
  > default value: `192k`
  >>
* `FFMPEG_CMD`
  > default value: `ffmpeg`
  >>
* `FFMPEG_CREATE_THUMBNAIL`
  > default value: `-vf "fps=1/(%(duration)s/%(nb_thumbnail)s)" -vsync vfr "%(output)s_%%04d.png"`
  >>
* `FFMPEG_CRF`
  > default value: `20`
  >>
* `FFMPEG_DRESSING_AUDIO`
  > default value: `[%(param_in)s]anull[%(param_out)s]`
  >> Traite l'audio sans modifications pour l'inclure dans la vidéo temporaire d'habillage.<br>
* `FFMPEG_DRESSING_CONCAT`
  > default value: `%(params)sconcat=n=%(number)s:v=1:a=1:unsafe=1[v][a]`
  >> Concatène plusieurs flux vidéo et audio en une seule sortie de vidéo temporaire d'habillage.<br>
* `FFMPEG_DRESSING_FILTER_COMPLEX`
  > default value: ` -filter_complex "%(filter)s" `
  >> Applique des chaînes de filtres complexes à la vidéo intermédiaire d'habillage avec FFmpeg.<br>
* `FFMPEG_DRESSING_INPUT`
  > default value: ` -i "%(input)s" `
  >> Définit le fichier d'entrée pour le traitement FFmpeg de la vidéo intermédiaire d'habillage.<br>
* `FFMPEG_DRESSING_OUTPUT`
  > default value: ` -c:v libx264 -y -vsync 0 "%(output)s" `
  >> Spécifie les paramètres d'encodage de sortie FFmpeg pour générer le fichier vidéo temporaire d'habillage, utilisant le codec H.264 avec écrasement forcé et synchronisation de la sortie vidéo.<br>
* `FFMPEG_DRESSING_SCALE`
  > default value: `[%(number)s]scale=w='if(gt(a,16/9),16/9*%(height)s,-2)':h='if(gt(a,16/9),-2,%(height)s)',pad=ceil(16/9*%(height)s):%(height)s:(ow-iw)/2:(oh-ih)/2[%(name)s]`
  >> Redimensionne la vidéo intermédiaire d'habillage pour maintenir un ratio d'aspect 16:9 avec ajout de bordures si nécessaire.<br>
* `FFMPEG_DRESSING_SILENT`
  > default value: ` -f lavfi -t %(duration)s -i anullsrc=r=44100:cl=stereo`
  >> Génère un audio silencieux d'une durée spécifiée pour la vidéo temporaire d'habillage.<br>
* `FFMPEG_DRESSING_WATERMARK`
  > default value: ` [1]format=rgba,colorchannelmixer=aa=%(opacity)s[logo]; [logo][vid]scale2ref=oh*mdar:ih*0.1[logo][video2]; [video2][logo]%(position)s%(name_out)s `
  >> Ajoute un filigrane à la vidéo intermédiaire d'habillage avec une opacité et une position personnalisables.<br>
* `FFMPEG_EXTRACT_SUBTITLE`
  > default value: `-map 0:%(index)s -f webvtt -y "%(output)s"`
  >>
* `FFMPEG_EXTRACT_THUMBNAIL`
  > default value: `-map 0:%(index)s -an -c:v copy -y "%(output)s"`
  >>
* `FFMPEG_HLS_COMMON_PARAMS`
  > default value: `-c:v %(libx)s -preset %(preset)s -profile:v %(profile)s -pix_fmt yuv420p -level %(level)s -crf %(crf)s -sc_threshold 0 -force_key_frames "expr:gte(t,n_forced*1)" -c:a aac -ar 48000 -max_muxing_queue_size 4000`
  >>
* `FFMPEG_HLS_ENCODE_PARAMS`
  > default value: `-vf "scale=-2:%(height)s" -maxrate %(maxrate)s -bufsize %(bufsize)s -b:a:0 %(ba)s -hls_playlist_type vod -hls_time %(hls_time)s -hls_flags single_file -master_pl_name "livestream%(height)s.m3u8" -y "%(output)s"`
  >>
* `FFMPEG_HLS_TIME`
  > default value: `2`
  >>
* `FFMPEG_INPUT`
  > default value: `-hide_banner -threads %(nb_threads)s -i "%(input)s"`
  >>
* `FFMPEG_LEVEL`
  > default value: `3`
  >>
* `FFMPEG_LIBX`
  > default value: `libx264`
  >>
* `FFMPEG_M4A_ENCODE`
  > default value: `-vn -c:a aac -b:a %(audio_bitrate)s "%(output)s"`
  >>
* `FFMPEG_MP3_ENCODE`
  > default value: `-vn -codec:a libmp3lame -qscale:a 2 -y "%(output)s"`
  >>
* `FFMPEG_MP4_ENCODE`
  > default value: `-map 0:v:0 %(map_audio)s -c:v %(libx)s -vf "scale=-2:%(height)s" -preset %(preset)s -profile:v %(profile)s -pix_fmt yuv420p -level %(level)s -crf %(crf)s -maxrate %(maxrate)s -bufsize %(bufsize)s -sc_threshold 0 -force_key_frames "expr:gte(t,n_forced*1)" -max_muxing_queue_size 4000 -c:a aac -ar 48000 -b:a %(ba)s -movflags faststart -y -vsync 0 "%(output)s"`
  >>
* `FFMPEG_NB_THREADS`
  > default value: `0`
  >>
* `FFMPEG_NB_THUMBNAIL`
  > default value: `3`
  >>
* `FFMPEG_PRESET`
  > default value: `slow`
  >>
* `FFMPEG_PROFILE`
  > default value: `high`
  >>
* `FFMPEG_STUDIO_COMMAND`
  > default value: `-hide_banner -threads %(nb_threads)s %(input)s %(subtime)s -c:a aac -ar 48000 -c:v h264 -profile:v high -pix_fmt yuv420p -crf %(crf)s -sc_threshold 0 -force_key_frames "expr:gte(t,n_forced*1)" -max_muxing_queue_size 4000 -deinterlace`
  >>
* `FFPROBE_CMD`
  > default value: `ffprobe`
  >>
* `FFPROBE_GET_INFO`
  > default value: `%(ffprobe)s -v quiet -show_format -show_streams %(select_streams)s -print_format json -i %(source)s`
  >>

### Gestion des fichiers

* `FILES_DIR`
  > default value: `files`
  >> Nom du répertoire racine où les fichiers "complémentaires"<br>
  >> (hors vidéos etc.) sont téléversés. Notament utilisé par PODFILE<br>
  >> À modifier principalement pour indiquer dans LOCATION<br>
  >> votre serveur de cache si elle n’est pas sur la même machine que votre POD.<br>
* `FILE_UPLOAD_TEMP_DIR`
  > default value: `/var/tmp`
  >> Le répertoire dans lequel stocker temporairement les données<br>
  >> (typiquement pour les fichiers plus grands que `FILE_UPLOAD_MAX_MEMORY_SIZE`)<br>
  >> lors des téléversements de fichiers.<br>
  >> _ref : [docs.djangoproject.com](https://docs.djangoproject.com/fr/4.2/ref/settings/#file-upload-temp-dir)_<br>
* `MEDIA_ROOT`
  > default value: `/pod/media`
  >> Chemin absolu du système de fichiers pointant vers le répertoire qui contiendra<br>
  >> les fichiers téléversés par les utilisateurs.<br><br>
  >> Attention, ce répertoire doit exister.<br><br>
  >> _ref : [docs.djangoproject.com](https://docs.djangoproject.com/fr/4.2/ref/settings/#std:setting-MEDIA_ROOT)_<br>
* `MEDIA_URL`
  > default value: `/media/`
  >> prefix url utilisé pour accéder aux fichiers du répertoire media<br>
* `STATICFILES_STORAGE`
  > default value: ``
  >> Indique à django de compresser automatiquement les fichiers css/js<br>
  >> les plus gros lors du collectstatic pour optimiser les tailles de requetes.<br><br>
  >> À combiner avec un réglage webserver (`gzip_static on;` sur nginx)<br><br>
  >> _ref : [whs/django-static-compress](https://github.com/whs/django-static-compress)<br>
* `STATIC_ROOT`
  > default value: `/pod/static`
  >> Le chemin absolu vers le répertoire dans lequel collectstatic rassemble<br>
  >> les fichiers statiques en vue du déploiement.<br>
  >> Ce chemin sera précisé dans le fichier de configurtation du vhost nginx.<br><br>
  >> _ref : [docs.djangoproject.com](https://docs.djangoproject.com/fr/4.2/ref/settings/#std:setting-STATIC_ROOT)_<br>
* `STATIC_URL`
  > default value: `/static/`
  >> prefix url utilisé pour accèder aux fichiers static<br>
* `USE_PODFILE`
  > default value: `False`
  >> Utiliser l’application de gestion de fichier fourni avec le projet.<br>
  >> Si False, chaque fichier envoyé ne pourra être utilisé qu’une seule fois.<br>
* `VIDEOS_DIR`
  > default value: `videos`
  >> Répertoire par défaut pour le téléversement des vidéos.<br>

### Langue

Par défaut, Esup-Pod est fournie en Francais et en anglais.<br>
Vous pouvez tout à fait rajouter des langues comme vous le souhaitez.<br>
Il faudra pour cela créer un fichier de langue et traduire chaque entrée.<br>

* `LANGUAGES`
  > default value: `(('fr', 'Français'), ('en', 'English')))`
  >> Langue disponible et traduite<br>
* `LANGUAGE_CODE`
  > default value: `fr`
  >> Langue par défaut si non détectée<br>

### Divers

* `ADMINS`
  > default value: `[("Name", "adminmail@univ.fr"),]`
  >> Une liste de toutes les personnes qui reçoivent les notifications d’erreurs dans le code.<br><br>
  >> Lorsque DEBUG=False et qu’une vue lève une exception,<br>
  >> Django envoie un courriel à ces personnes contenant les informations complètes de l’exception.<br><br>
  >> Chaque élément de la liste doit être un tuple au format<br>
  >> « (nom complet, adresse électronique) ».<br><br>
  >> Exemple : `[('John', 'john@example.com'), ('Mary', 'mary@example.com')]`<br><br>
  >> Dans Pod, les "admins" sont également destinataires des courriels de contact,<br>
  >> d’encodage ou de flux RSS si la variable `CONTACT_US_EMAIL` n’est pas renseignée.<br><br>
  >> _ref : [docs.djangoproject.com](https://docs.djangoproject.com/fr/4.2/ref/settings/#admins)_<br>
* `ALLOWED_HOSTS`
  > default value: `['pod.localhost']`
  >> Une liste de chaînes représentant des noms de domaine/d’hôte que ce site Django peut servir.<br><br>
  >> C’est une mesure de sécurité pour empêcher les attaques d’en-tête Host HTTP,<br>
  >> qui sont possibles même avec bien des configurations de serveur Web apparemment sécurisées.<br><br>
  >> _ref : [docs.djangoproject.com](https://docs.djangoproject.com/fr/4.2/ref/settings/#allowed-hosts)_<br>
* `ASGI_APPLICATION`
  > default value: `config.asgi.application`
  >> Chemin vers l'objet application ASGI.<br>
* `AUTHENTICATION_BACKENDS`
  > default value: `['django.contrib.auth.backends.ModelBackend']`
  >> Liste des backends d'authentification à utiliser (ex: ModelBackend, CASBackend).
<br>
* `BASE_DIR`
  > default value: `os.path.dirname(os.path.dirname(os.path.abspath(__file__)))`
  >> répertoire de base<br>
* `CACHES`
  > default value: `{}`
  >>
  >> ```python
  >> CACHES = {
  >>     # … default cache config and others
  >>     # "default": {
  >>     #     "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
  >>     # },
  >>     "default": {
  >>         "BACKEND": "django_redis.cache.RedisCache",
  >>         "LOCATION": "redis://redis.localhost:6379/1",
  >>         "OPTIONS": {
  >>             "CLIENT_CLASS": "django_redis.client.DefaultClient",
  >>         },
  >>     },
  >>     # Persistent cache setup for select2 (NOT DummyCache or LocMemCache).
  >>     "select2": {
  >>         "BACKEND": "django_redis.cache.RedisCache",
  >>         "LOCATION": "redis://redis.localhost:6379/2",
  >>         "OPTIONS": {
  >>             "CLIENT_CLASS": "django_redis.client.DefaultClient",
  >>         },
  >>     },
  >> }
  >> ```
  >>
* `CACHE_MIDDLEWARE_ALIAS`
  > default value: `default`
  >> L'alias de cache à utiliser pour le middleware de cache.
<br>
* `CACHE_MIDDLEWARE_KEY_PREFIX`
  > default value: ``
  >> Préfixe de clés de cache générées par le middleware de cache.
<br>
* `CACHE_MIDDLEWARE_SECONDS`
  > default value: `600`
  >> D<br>
  >> u<br>
  >> r<br>
  >> é<br>
  >> e<br>
  >> <br>
  >> p<br>
  >> a<br>
  >> r<br>
  >> <br>
  >> d<br>
  >> é<br>
  >> f<br>
  >> a<br>
  >> u<br>
  >> t<br>
  >> <br>
  >> e<br>
  >> n<br>
  >> <br>
  >> s<br>
  >> e<br>
  >> c<br>
  >> o<br>
  >> n<br>
  >> d<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> p<br>
  >> o<br>
  >> u<br>
  >> r<br>
  >> <br>
  >> l<br>
  >> a<br>
  >> <br>
  >> m<br>
  >> i<br>
  >> s<br>
  >> e<br>
  >> <br>
  >> e<br>
  >> n<br>
  >> <br>
  >> c<br>
  >> a<br>
  >> c<br>
  >> h<br>
  >> e<br>
  >> <br>
  >> d<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> p<br>
  >> a<br>
  >> g<br>
  >> e<br>
  >> s<br>
  >> .<br>
* `CORS_ALLOW_ALL_ORIGINS`
  > default value: `False`
  >> Autoriser toutes les origines pour les requêtes CORS.<br>
* `CSRF_COOKIE_SECURE`
  > default value: `not DEBUG`
  >> Ces 3 variables servent à sécuriser la plateforme en passant<br>
  >> l’ensemble des requetes en https.<br>
  >> Idem pour les cookies de session et de cross-sites qui seront également sécurisés<br><br>
  >> Il faut les passer à False en cas d’usage du runserver (phase de développement / debugage)<br><br>
  >> _ref : [docs.djangoproject.com](https://docs.djangoproject.com/fr/4.2/ref/settings/#secure-ssl-redirect)_<br>
* `DATABASE_ROUTERS`
  > default value: `[]`
  >> Liste des classes de routeurs pour contrôler les opérations de base de données.
<br>
* `DATA_UPLOAD_MAX_MEMORY_SIZE`
  > default value: `2621440`
  >> T<br>
  >> a<br>
  >> i<br>
  >> l<br>
  >> l<br>
  >> e<br>
  >> <br>
  >> m<br>
  >> a<br>
  >> x<br>
  >> i<br>
  >> m<br>
  >> a<br>
  >> l<br>
  >> e<br>
  >> <br>
  >> e<br>
  >> n<br>
  >> <br>
  >> o<br>
  >> c<br>
  >> t<br>
  >> e<br>
  >> t<br>
  >> s<br>
  >> <br>
  >> (<br>
  >> d<br>
  >> é<br>
  >> f<br>
  >> a<br>
  >> u<br>
  >> t<br>
  >> <br>
  >> 2<br>
  >> .<br>
  >> 5<br>
  >> M<br>
  >> B<br>
  >> )<br>
  >> <br>
  >> d<br>
  >> u<br>
  >> <br>
  >> c<br>
  >> o<br>
  >> r<br>
  >> p<br>
  >> s<br>
  >> <br>
  >> d<br>
  >> '<br>
  >> u<br>
  >> n<br>
  >> e<br>
  >> <br>
  >> r<br>
  >> e<br>
  >> q<br>
  >> u<br>
  >> ê<br>
  >> t<br>
  >> e<br>
  >> <br>
  >> a<br>
  >> v<br>
  >> a<br>
  >> n<br>
  >> t<br>
  >> <br>
  >> d<br>
  >> e<br>
  >> <br>
  >> l<br>
  >> e<br>
  >> v<br>
  >> e<br>
  >> r<br>
  >> <br>
  >> u<br>
  >> n<br>
  >> e<br>
  >> <br>
  >> S<br>
  >> u<br>
  >> s<br>
  >> p<br>
  >> i<br>
  >> c<br>
  >> i<br>
  >> o<br>
  >> u<br>
  >> s<br>
  >> O<br>
  >> p<br>
  >> e<br>
  >> r<br>
  >> a<br>
  >> t<br>
  >> i<br>
  >> o<br>
  >> n<br>
  >> .<br>
* `DATA_UPLOAD_MAX_NUMBER_FIELDS`
  > default value: `1000`
  >> N<br>
  >> o<br>
  >> m<br>
  >> b<br>
  >> r<br>
  >> e<br>
  >> <br>
  >> m<br>
  >> a<br>
  >> x<br>
  >> i<br>
  >> m<br>
  >> u<br>
  >> m<br>
  >> <br>
  >> d<br>
  >> e<br>
  >> <br>
  >> c<br>
  >> h<br>
  >> a<br>
  >> m<br>
  >> p<br>
  >> s<br>
  >> <br>
  >> a<br>
  >> u<br>
  >> t<br>
  >> o<br>
  >> r<br>
  >> i<br>
  >> s<br>
  >> é<br>
  >> s<br>
  >> <br>
  >> d<br>
  >> a<br>
  >> n<br>
  >> s<br>
  >> <br>
  >> u<br>
  >> n<br>
  >> e<br>
  >> <br>
  >> r<br>
  >> e<br>
  >> q<br>
  >> u<br>
  >> ê<br>
  >> t<br>
  >> e<br>
  >> <br>
  >> G<br>
  >> E<br>
  >> T<br>
  >> <br>
  >> o<br>
  >> u<br>
  >> <br>
  >> P<br>
  >> O<br>
  >> S<br>
  >> T<br>
  >> .<br>
* `DATA_UPLOAD_MAX_NUMBER_FILES`
  > default value: `100`
  >> N<br>
  >> o<br>
  >> m<br>
  >> b<br>
  >> r<br>
  >> e<br>
  >> <br>
  >> m<br>
  >> a<br>
  >> x<br>
  >> i<br>
  >> m<br>
  >> u<br>
  >> m<br>
  >> <br>
  >> d<br>
  >> e<br>
  >> <br>
  >> f<br>
  >> i<br>
  >> c<br>
  >> h<br>
  >> i<br>
  >> e<br>
  >> r<br>
  >> s<br>
  >> <br>
  >> a<br>
  >> u<br>
  >> t<br>
  >> o<br>
  >> r<br>
  >> i<br>
  >> s<br>
  >> é<br>
  >> s<br>
  >> <br>
  >> d<br>
  >> a<br>
  >> n<br>
  >> s<br>
  >> <br>
  >> u<br>
  >> n<br>
  >> <br>
  >> s<br>
  >> e<br>
  >> u<br>
  >> l<br>
  >> <br>
  >> t<br>
  >> é<br>
  >> l<br>
  >> é<br>
  >> c<br>
  >> h<br>
  >> a<br>
  >> r<br>
  >> g<br>
  >> e<br>
  >> m<br>
  >> e<br>
  >> n<br>
  >> t<br>
  >> .<br>
* `DATETIME_FORMAT`
  > default value: `N j, Y, P`
  >> L<br>
  >> e<br>
  >> <br>
  >> f<br>
  >> o<br>
  >> r<br>
  >> m<br>
  >> a<br>
  >> t<br>
  >> <br>
  >> d<br>
  >> e<br>
  >> <br>
  >> s<br>
  >> o<br>
  >> r<br>
  >> t<br>
  >> i<br>
  >> e<br>
  >> <br>
  >> p<br>
  >> a<br>
  >> r<br>
  >> <br>
  >> d<br>
  >> é<br>
  >> f<br>
  >> a<br>
  >> u<br>
  >> t<br>
  >> <br>
  >> p<br>
  >> o<br>
  >> u<br>
  >> r<br>
  >> <br>
  >> l<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> o<br>
  >> b<br>
  >> j<br>
  >> e<br>
  >> t<br>
  >> s<br>
  >> <br>
  >> d<br>
  >> a<br>
  >> t<br>
  >> e<br>
  >> t<br>
  >> i<br>
  >> m<br>
  >> e<br>
  >> <br>
  >> d<br>
  >> a<br>
  >> n<br>
  >> s<br>
  >> <br>
  >> l<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> t<br>
  >> e<br>
  >> m<br>
  >> p<br>
  >> l<br>
  >> a<br>
  >> t<br>
  >> e<br>
  >> s<br>
  >> .<br>
* `DATETIME_INPUT_FORMATS`
  > default value: `['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M', '%Y-%m-%d']`
  >> L<br>
  >> i<br>
  >> s<br>
  >> t<br>
  >> e<br>
  >> <br>
  >> d<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> f<br>
  >> o<br>
  >> r<br>
  >> m<br>
  >> a<br>
  >> t<br>
  >> s<br>
  >> <br>
  >> a<br>
  >> c<br>
  >> c<br>
  >> e<br>
  >> p<br>
  >> t<br>
  >> é<br>
  >> s<br>
  >> <br>
  >> l<br>
  >> o<br>
  >> r<br>
  >> s<br>
  >> <br>
  >> d<br>
  >> e<br>
  >> <br>
  >> l<br>
  >> '<br>
  >> a<br>
  >> n<br>
  >> a<br>
  >> l<br>
  >> y<br>
  >> s<br>
  >> e<br>
  >> <br>
  >> d<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> d<br>
  >> a<br>
  >> t<br>
  >> e<br>
  >> s<br>
  >> /<br>
  >> h<br>
  >> e<br>
  >> u<br>
  >> r<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> d<br>
  >> a<br>
  >> n<br>
  >> s<br>
  >> <br>
  >> l<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> f<br>
  >> o<br>
  >> r<br>
  >> m<br>
  >> u<br>
  >> l<br>
  >> a<br>
  >> i<br>
  >> r<br>
  >> e<br>
  >> s<br>
  >> .<br>
* `DATE_FORMAT`
  > default value: `N j, Y`
  >> L<br>
  >> e<br>
  >> <br>
  >> f<br>
  >> o<br>
  >> r<br>
  >> m<br>
  >> a<br>
  >> t<br>
  >> <br>
  >> d<br>
  >> e<br>
  >> <br>
  >> s<br>
  >> o<br>
  >> r<br>
  >> t<br>
  >> i<br>
  >> e<br>
  >> <br>
  >> p<br>
  >> a<br>
  >> r<br>
  >> <br>
  >> d<br>
  >> é<br>
  >> f<br>
  >> a<br>
  >> u<br>
  >> t<br>
  >> <br>
  >> p<br>
  >> o<br>
  >> u<br>
  >> r<br>
  >> <br>
  >> l<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> o<br>
  >> b<br>
  >> j<br>
  >> e<br>
  >> t<br>
  >> s<br>
  >> <br>
  >> d<br>
  >> a<br>
  >> t<br>
  >> e<br>
  >> <br>
  >> d<br>
  >> a<br>
  >> n<br>
  >> s<br>
  >> <br>
  >> l<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> t<br>
  >> e<br>
  >> m<br>
  >> p<br>
  >> l<br>
  >> a<br>
  >> t<br>
  >> e<br>
  >> s<br>
  >> .<br>
* `DATE_INPUT_FORMATS`
  > default value: `['%Y-%m-%d', '%m/%d/%Y', '%m/%d/%y']`
  >> L<br>
  >> i<br>
  >> s<br>
  >> t<br>
  >> e<br>
  >> <br>
  >> d<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> f<br>
  >> o<br>
  >> r<br>
  >> m<br>
  >> a<br>
  >> t<br>
  >> s<br>
  >> <br>
  >> a<br>
  >> c<br>
  >> c<br>
  >> e<br>
  >> p<br>
  >> t<br>
  >> é<br>
  >> s<br>
  >> <br>
  >> l<br>
  >> o<br>
  >> r<br>
  >> s<br>
  >> <br>
  >> d<br>
  >> e<br>
  >> <br>
  >> l<br>
  >> '<br>
  >> a<br>
  >> n<br>
  >> a<br>
  >> l<br>
  >> y<br>
  >> s<br>
  >> e<br>
  >> <br>
  >> d<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> d<br>
  >> a<br>
  >> t<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> d<br>
  >> a<br>
  >> n<br>
  >> s<br>
  >> <br>
  >> l<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> f<br>
  >> o<br>
  >> r<br>
  >> m<br>
  >> u<br>
  >> l<br>
  >> a<br>
  >> i<br>
  >> r<br>
  >> e<br>
  >> s<br>
  >> .<br>
* `DEBUG`
  > default value: `True`
  >> Une valeur booléenne qui active ou désactive le mode de débogage.<br><br>
  >> Ne déployez jamais de site en production avec le réglage DEBUG activé.<br><br>
  >> _ref : [docs.djangoproject.com](https://docs.djangoproject.com/fr/4.2/ref/settings/#debug)_<br>
* `DECIMAL_SEPARATOR`
  > default value: `.`
  >> L<br>
  >> e<br>
  >> <br>
  >> s<br>
  >> é<br>
  >> p<br>
  >> a<br>
  >> r<br>
  >> a<br>
  >> t<br>
  >> e<br>
  >> u<br>
  >> r<br>
  >> <br>
  >> d<br>
  >> é<br>
  >> c<br>
  >> i<br>
  >> m<br>
  >> a<br>
  >> l<br>
  >> <br>
  >> u<br>
  >> t<br>
  >> i<br>
  >> l<br>
  >> i<br>
  >> s<br>
  >> é<br>
  >> <br>
  >> l<br>
  >> o<br>
  >> r<br>
  >> s<br>
  >> <br>
  >> d<br>
  >> u<br>
  >> <br>
  >> f<br>
  >> o<br>
  >> r<br>
  >> m<br>
  >> a<br>
  >> t<br>
  >> a<br>
  >> g<br>
  >> e<br>
  >> <br>
  >> d<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> n<br>
  >> o<br>
  >> m<br>
  >> b<br>
  >> r<br>
  >> e<br>
  >> s<br>
  >> .<br>
* `DEFAULT_AUTO_FIELD`
  > default value: `django.db.models.AutoField`
  >> Type par défaut pour les clés primaires créées automatiquement.<br>
* `DISALLOWED_USER_AGENTS`
  > default value: `[]`
  >> L<br>
  >> i<br>
  >> s<br>
  >> t<br>
  >> e<br>
  >> <br>
  >> d<br>
  >> '<br>
  >> e<br>
  >> x<br>
  >> p<br>
  >> r<br>
  >> e<br>
  >> s<br>
  >> s<br>
  >> i<br>
  >> o<br>
  >> n<br>
  >> s<br>
  >> <br>
  >> r<br>
  >> é<br>
  >> g<br>
  >> u<br>
  >> l<br>
  >> i<br>
  >> è<br>
  >> r<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> c<br>
  >> o<br>
  >> m<br>
  >> p<br>
  >> i<br>
  >> l<br>
  >> é<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> r<br>
  >> e<br>
  >> p<br>
  >> r<br>
  >> é<br>
  >> s<br>
  >> e<br>
  >> n<br>
  >> t<br>
  >> a<br>
  >> n<br>
  >> t<br>
  >> <br>
  >> l<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> c<br>
  >> h<br>
  >> a<br>
  >> î<br>
  >> n<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> U<br>
  >> s<br>
  >> e<br>
  >> r<br>
  >> -<br>
  >> A<br>
  >> g<br>
  >> e<br>
  >> n<br>
  >> t<br>
  >> <br>
  >> q<br>
  >> u<br>
  >> i<br>
  >> <br>
  >> n<br>
  >> e<br>
  >> <br>
  >> s<br>
  >> o<br>
  >> n<br>
  >> t<br>
  >> <br>
  >> p<br>
  >> a<br>
  >> s<br>
  >> <br>
  >> a<br>
  >> u<br>
  >> t<br>
  >> o<br>
  >> r<br>
  >> i<br>
  >> s<br>
  >> é<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> à<br>
  >> <br>
  >> v<br>
  >> i<br>
  >> s<br>
  >> i<br>
  >> t<br>
  >> e<br>
  >> r<br>
  >> <br>
  >> l<br>
  >> e<br>
  >> <br>
  >> s<br>
  >> i<br>
  >> t<br>
  >> e<br>
  >> .<br>
* `FIRST_DAY_OF_WEEK`
  > default value: `0`
  >> N<br>
  >> o<br>
  >> m<br>
  >> b<br>
  >> r<br>
  >> e<br>
  >> <br>
  >> r<br>
  >> e<br>
  >> p<br>
  >> r<br>
  >> é<br>
  >> s<br>
  >> e<br>
  >> n<br>
  >> t<br>
  >> a<br>
  >> n<br>
  >> t<br>
  >> <br>
  >> l<br>
  >> e<br>
  >> <br>
  >> p<br>
  >> r<br>
  >> e<br>
  >> m<br>
  >> i<br>
  >> e<br>
  >> r<br>
  >> <br>
  >> j<br>
  >> o<br>
  >> u<br>
  >> r<br>
  >> <br>
  >> d<br>
  >> e<br>
  >> <br>
  >> l<br>
  >> a<br>
  >> <br>
  >> s<br>
  >> e<br>
  >> m<br>
  >> a<br>
  >> i<br>
  >> n<br>
  >> e<br>
  >> <br>
  >> (<br>
  >> 0<br>
  >> =<br>
  >> D<br>
  >> i<br>
  >> m<br>
  >> a<br>
  >> n<br>
  >> c<br>
  >> h<br>
  >> e<br>
  >> ,<br>
  >> <br>
  >> 1<br>
  >> =<br>
  >> L<br>
  >> u<br>
  >> n<br>
  >> d<br>
  >> i<br>
  >> )<br>
  >> .<br>
* `FIXTURE_DIRS`
  > default value: `[]`
  >> L<br>
  >> i<br>
  >> s<br>
  >> t<br>
  >> e<br>
  >> <br>
  >> d<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> r<br>
  >> é<br>
  >> p<br>
  >> e<br>
  >> r<br>
  >> t<br>
  >> o<br>
  >> i<br>
  >> r<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> o<br>
  >> ù<br>
  >> <br>
  >> c<br>
  >> h<br>
  >> e<br>
  >> r<br>
  >> c<br>
  >> h<br>
  >> e<br>
  >> r<br>
  >> <br>
  >> d<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> f<br>
  >> i<br>
  >> c<br>
  >> h<br>
  >> i<br>
  >> e<br>
  >> r<br>
  >> s<br>
  >> <br>
  >> f<br>
  >> i<br>
  >> x<br>
  >> t<br>
  >> u<br>
  >> r<br>
  >> e<br>
  >> s<br>
  >> ,<br>
  >> <br>
  >> e<br>
  >> n<br>
  >> <br>
  >> p<br>
  >> l<br>
  >> u<br>
  >> s<br>
  >> <br>
  >> d<br>
  >> u<br>
  >> <br>
  >> r<br>
  >> é<br>
  >> p<br>
  >> e<br>
  >> r<br>
  >> t<br>
  >> o<br>
  >> i<br>
  >> r<br>
  >> e<br>
  >> <br>
  >> '<br>
  >> f<br>
  >> i<br>
  >> x<br>
  >> t<br>
  >> u<br>
  >> r<br>
  >> e<br>
  >> s<br>
  >> '<br>
  >> <br>
  >> d<br>
  >> e<br>
  >> <br>
  >> c<br>
  >> h<br>
  >> a<br>
  >> q<br>
  >> u<br>
  >> e<br>
  >> <br>
  >> a<br>
  >> p<br>
  >> p<br>
  >> l<br>
  >> i<br>
  >> c<br>
  >> a<br>
  >> t<br>
  >> i<br>
  >> o<br>
  >> n<br>
  >> .<br>
* `FORCE_SCRIPT_NAME`
  > default value: `None`
  >> S<br>
  >> i<br>
  >> <br>
  >> n<br>
  >> o<br>
  >> n<br>
  >> <br>
  >> d<br>
  >> é<br>
  >> f<br>
  >> i<br>
  >> n<br>
  >> i<br>
  >> <br>
  >> à<br>
  >> <br>
  >> N<br>
  >> o<br>
  >> n<br>
  >> e<br>
  >> ,<br>
  >> <br>
  >> c<br>
  >> e<br>
  >> t<br>
  >> t<br>
  >> e<br>
  >> <br>
  >> v<br>
  >> a<br>
  >> l<br>
  >> e<br>
  >> u<br>
  >> r<br>
  >> <br>
  >> s<br>
  >> e<br>
  >> r<br>
  >> a<br>
  >> <br>
  >> u<br>
  >> t<br>
  >> i<br>
  >> l<br>
  >> i<br>
  >> s<br>
  >> é<br>
  >> e<br>
  >> <br>
  >> c<br>
  >> o<br>
  >> m<br>
  >> m<br>
  >> e<br>
  >> <br>
  >> v<br>
  >> a<br>
  >> l<br>
  >> e<br>
  >> u<br>
  >> r<br>
  >> <br>
  >> d<br>
  >> e<br>
  >> <br>
  >> l<br>
  >> a<br>
  >> <br>
  >> v<br>
  >> a<br>
  >> r<br>
  >> i<br>
  >> a<br>
  >> b<br>
  >> l<br>
  >> e<br>
  >> <br>
  >> d<br>
  >> '<br>
  >> e<br>
  >> n<br>
  >> v<br>
  >> i<br>
  >> r<br>
  >> o<br>
  >> n<br>
  >> n<br>
  >> e<br>
  >> m<br>
  >> e<br>
  >> n<br>
  >> t<br>
  >> <br>
  >> S<br>
  >> C<br>
  >> R<br>
  >> I<br>
  >> P<br>
  >> T<br>
  >> _<br>
  >> N<br>
  >> A<br>
  >> M<br>
  >> E<br>
  >> <br>
  >> d<br>
  >> a<br>
  >> n<br>
  >> s<br>
  >> <br>
  >> t<br>
  >> o<br>
  >> u<br>
  >> t<br>
  >> e<br>
  >> <br>
  >> r<br>
  >> e<br>
  >> q<br>
  >> u<br>
  >> ê<br>
  >> t<br>
  >> e<br>
  >> <br>
  >> H<br>
  >> T<br>
  >> T<br>
  >> P<br>
  >> .<br>
* `FORMAT_MODULE_PATH`
  > default value: `None`
  >> C<br>
  >> h<br>
  >> e<br>
  >> m<br>
  >> i<br>
  >> n<br>
  >> <br>
  >> P<br>
  >> y<br>
  >> t<br>
  >> h<br>
  >> o<br>
  >> n<br>
  >> <br>
  >> v<br>
  >> e<br>
  >> r<br>
  >> s<br>
  >> <br>
  >> u<br>
  >> n<br>
  >> <br>
  >> m<br>
  >> o<br>
  >> d<br>
  >> u<br>
  >> l<br>
  >> e<br>
  >> <br>
  >> c<br>
  >> o<br>
  >> n<br>
  >> t<br>
  >> e<br>
  >> n<br>
  >> a<br>
  >> n<br>
  >> t<br>
  >> <br>
  >> d<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> d<br>
  >> é<br>
  >> f<br>
  >> i<br>
  >> n<br>
  >> i<br>
  >> t<br>
  >> i<br>
  >> o<br>
  >> n<br>
  >> s<br>
  >> <br>
  >> d<br>
  >> e<br>
  >> <br>
  >> f<br>
  >> o<br>
  >> r<br>
  >> m<br>
  >> a<br>
  >> t<br>
  >> <br>
  >> s<br>
  >> p<br>
  >> é<br>
  >> c<br>
  >> i<br>
  >> f<br>
  >> i<br>
  >> q<br>
  >> u<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> a<br>
  >> u<br>
  >> <br>
  >> p<br>
  >> r<br>
  >> o<br>
  >> j<br>
  >> e<br>
  >> t<br>
  >> .<br>
* `FORMS_URLFIELD_ASSUME_HTTPS`
  > default value: `False`
  >> S<br>
  >> i<br>
  >> <br>
  >> T<br>
  >> r<br>
  >> u<br>
  >> e<br>
  >> ,<br>
  >> <br>
  >> U<br>
  >> R<br>
  >> L<br>
  >> F<br>
  >> i<br>
  >> e<br>
  >> l<br>
  >> d<br>
  >> <br>
  >> s<br>
  >> u<br>
  >> p<br>
  >> p<br>
  >> o<br>
  >> s<br>
  >> e<br>
  >> r<br>
  >> a<br>
  >> <br>
  >> H<br>
  >> T<br>
  >> T<br>
  >> P<br>
  >> S<br>
  >> <br>
  >> s<br>
  >> i<br>
  >> <br>
  >> a<br>
  >> u<br>
  >> c<br>
  >> u<br>
  >> n<br>
  >> <br>
  >> s<br>
  >> c<br>
  >> h<br>
  >> é<br>
  >> m<br>
  >> a<br>
  >> <br>
  >> n<br>
  >> '<br>
  >> e<br>
  >> s<br>
  >> t<br>
  >> <br>
  >> f<br>
  >> o<br>
  >> u<br>
  >> r<br>
  >> n<br>
  >> i<br>
  >> .<br>
* `FORM_RENDERER`
  > default value: `django.forms.renderers.DjangoTemplates`
  >> L<br>
  >> a<br>
  >> <br>
  >> c<br>
  >> l<br>
  >> a<br>
  >> s<br>
  >> s<br>
  >> e<br>
  >> <br>
  >> u<br>
  >> t<br>
  >> i<br>
  >> l<br>
  >> i<br>
  >> s<br>
  >> é<br>
  >> e<br>
  >> <br>
  >> p<br>
  >> o<br>
  >> u<br>
  >> r<br>
  >> <br>
  >> l<br>
  >> e<br>
  >> <br>
  >> r<br>
  >> e<br>
  >> n<br>
  >> d<br>
  >> u<br>
  >> <br>
  >> d<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> f<br>
  >> o<br>
  >> r<br>
  >> m<br>
  >> u<br>
  >> l<br>
  >> a<br>
  >> i<br>
  >> r<br>
  >> e<br>
  >> s<br>
  >> .<br>
* `IGNORABLE_404_URLS`
  > default value: `[]`
  >> L<br>
  >> i<br>
  >> s<br>
  >> t<br>
  >> e<br>
  >> <br>
  >> d<br>
  >> '<br>
  >> o<br>
  >> b<br>
  >> j<br>
  >> e<br>
  >> t<br>
  >> s<br>
  >> <br>
  >> d<br>
  >> '<br>
  >> e<br>
  >> x<br>
  >> p<br>
  >> r<br>
  >> e<br>
  >> s<br>
  >> s<br>
  >> i<br>
  >> o<br>
  >> n<br>
  >> s<br>
  >> <br>
  >> r<br>
  >> é<br>
  >> g<br>
  >> u<br>
  >> l<br>
  >> i<br>
  >> è<br>
  >> r<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> c<br>
  >> o<br>
  >> m<br>
  >> p<br>
  >> i<br>
  >> l<br>
  >> é<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> d<br>
  >> é<br>
  >> c<br>
  >> r<br>
  >> i<br>
  >> v<br>
  >> a<br>
  >> n<br>
  >> t<br>
  >> <br>
  >> l<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> U<br>
  >> R<br>
  >> L<br>
  >> <br>
  >> q<br>
  >> u<br>
  >> i<br>
  >> <br>
  >> d<br>
  >> o<br>
  >> i<br>
  >> v<br>
  >> e<br>
  >> n<br>
  >> t<br>
  >> <br>
  >> ê<br>
  >> t<br>
  >> r<br>
  >> e<br>
  >> <br>
  >> i<br>
  >> g<br>
  >> n<br>
  >> o<br>
  >> r<br>
  >> é<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> l<br>
  >> o<br>
  >> r<br>
  >> s<br>
  >> <br>
  >> d<br>
  >> u<br>
  >> <br>
  >> s<br>
  >> i<br>
  >> g<br>
  >> n<br>
  >> a<br>
  >> l<br>
  >> e<br>
  >> m<br>
  >> e<br>
  >> n<br>
  >> t<br>
  >> <br>
  >> d<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> e<br>
  >> r<br>
  >> r<br>
  >> e<br>
  >> u<br>
  >> r<br>
  >> s<br>
  >> <br>
  >> 4<br>
  >> 0<br>
  >> 4<br>
  >> <br>
  >> p<br>
  >> a<br>
  >> r<br>
  >> <br>
  >> e<br>
  >> -<br>
  >> m<br>
  >> a<br>
  >> i<br>
  >> l<br>
  >> .<br>
* `LANGUAGE_COOKIE_AGE`
  > default value: `None`
  >> L<br>
  >> a<br>
  >> <br>
  >> d<br>
  >> u<br>
  >> r<br>
  >> é<br>
  >> e<br>
  >> <br>
  >> d<br>
  >> e<br>
  >> <br>
  >> v<br>
  >> i<br>
  >> e<br>
  >> <br>
  >> d<br>
  >> u<br>
  >> <br>
  >> c<br>
  >> o<br>
  >> o<br>
  >> k<br>
  >> i<br>
  >> e<br>
  >> <br>
  >> d<br>
  >> e<br>
  >> <br>
  >> l<br>
  >> a<br>
  >> n<br>
  >> g<br>
  >> u<br>
  >> e<br>
  >> ,<br>
  >> <br>
  >> e<br>
  >> n<br>
  >> <br>
  >> s<br>
  >> e<br>
  >> c<br>
  >> o<br>
  >> n<br>
  >> d<br>
  >> e<br>
  >> s<br>
  >> .<br>
* `LANGUAGE_COOKIE_DOMAIN`
  > default value: `None`
  >> L<br>
  >> e<br>
  >> <br>
  >> d<br>
  >> o<br>
  >> m<br>
  >> a<br>
  >> i<br>
  >> n<br>
  >> e<br>
  >> <br>
  >> à<br>
  >> <br>
  >> u<br>
  >> t<br>
  >> i<br>
  >> l<br>
  >> i<br>
  >> s<br>
  >> e<br>
  >> r<br>
  >> <br>
  >> p<br>
  >> o<br>
  >> u<br>
  >> r<br>
  >> <br>
  >> l<br>
  >> e<br>
  >> <br>
  >> c<br>
  >> o<br>
  >> o<br>
  >> k<br>
  >> i<br>
  >> e<br>
  >> <br>
  >> d<br>
  >> e<br>
  >> <br>
  >> l<br>
  >> a<br>
  >> n<br>
  >> g<br>
  >> u<br>
  >> e<br>
  >> .<br>
* `LANGUAGE_COOKIE_HTTPONLY`
  > default value: `False`
  >> S<br>
  >> i<br>
  >> <br>
  >> l<br>
  >> e<br>
  >> <br>
  >> d<br>
  >> r<br>
  >> a<br>
  >> p<br>
  >> e<br>
  >> a<br>
  >> u<br>
  >> <br>
  >> H<br>
  >> T<br>
  >> T<br>
  >> P<br>
  >> O<br>
  >> n<br>
  >> l<br>
  >> y<br>
  >> <br>
  >> d<br>
  >> o<br>
  >> i<br>
  >> t<br>
  >> <br>
  >> ê<br>
  >> t<br>
  >> r<br>
  >> e<br>
  >> <br>
  >> u<br>
  >> t<br>
  >> i<br>
  >> l<br>
  >> i<br>
  >> s<br>
  >> é<br>
  >> <br>
  >> s<br>
  >> u<br>
  >> r<br>
  >> <br>
  >> l<br>
  >> e<br>
  >> <br>
  >> c<br>
  >> o<br>
  >> o<br>
  >> k<br>
  >> i<br>
  >> e<br>
  >> <br>
  >> d<br>
  >> e<br>
  >> <br>
  >> l<br>
  >> a<br>
  >> n<br>
  >> g<br>
  >> u<br>
  >> e<br>
  >> .<br>
* `LANGUAGE_COOKIE_NAME`
  > default value: `django_language`
  >> L<br>
  >> e<br>
  >> <br>
  >> n<br>
  >> o<br>
  >> m<br>
  >> <br>
  >> d<br>
  >> u<br>
  >> <br>
  >> c<br>
  >> o<br>
  >> o<br>
  >> k<br>
  >> i<br>
  >> e<br>
  >> <br>
  >> d<br>
  >> e<br>
  >> <br>
  >> l<br>
  >> a<br>
  >> n<br>
  >> g<br>
  >> u<br>
  >> e<br>
  >> .<br>
* `LANGUAGE_COOKIE_PATH`
  > default value: `/`
  >> L<br>
  >> e<br>
  >> <br>
  >> c<br>
  >> h<br>
  >> e<br>
  >> m<br>
  >> i<br>
  >> n<br>
  >> <br>
  >> d<br>
  >> é<br>
  >> f<br>
  >> i<br>
  >> n<br>
  >> i<br>
  >> <br>
  >> s<br>
  >> u<br>
  >> r<br>
  >> <br>
  >> l<br>
  >> e<br>
  >> <br>
  >> c<br>
  >> o<br>
  >> o<br>
  >> k<br>
  >> i<br>
  >> e<br>
  >> <br>
  >> d<br>
  >> e<br>
  >> <br>
  >> l<br>
  >> a<br>
  >> n<br>
  >> g<br>
  >> u<br>
  >> e<br>
  >> .<br>
* `LANGUAGE_COOKIE_SAMESITE`
  > default value: `Lax`
  >> L<br>
  >> a<br>
  >> <br>
  >> v<br>
  >> a<br>
  >> l<br>
  >> e<br>
  >> u<br>
  >> r<br>
  >> <br>
  >> d<br>
  >> u<br>
  >> <br>
  >> d<br>
  >> r<br>
  >> a<br>
  >> p<br>
  >> e<br>
  >> a<br>
  >> u<br>
  >> <br>
  >> S<br>
  >> a<br>
  >> m<br>
  >> e<br>
  >> S<br>
  >> i<br>
  >> t<br>
  >> e<br>
  >> <br>
  >> s<br>
  >> u<br>
  >> r<br>
  >> <br>
  >> l<br>
  >> e<br>
  >> <br>
  >> c<br>
  >> o<br>
  >> o<br>
  >> k<br>
  >> i<br>
  >> e<br>
  >> <br>
  >> d<br>
  >> e<br>
  >> <br>
  >> l<br>
  >> a<br>
  >> n<br>
  >> g<br>
  >> u<br>
  >> e<br>
  >> .<br>
* `LANGUAGE_COOKIE_SECURE`
  > default value: `False`
  >> S<br>
  >> i<br>
  >> <br>
  >> l<br>
  >> e<br>
  >> <br>
  >> d<br>
  >> r<br>
  >> a<br>
  >> p<br>
  >> e<br>
  >> a<br>
  >> u<br>
  >> <br>
  >> S<br>
  >> e<br>
  >> c<br>
  >> u<br>
  >> r<br>
  >> e<br>
  >> <br>
  >> d<br>
  >> o<br>
  >> i<br>
  >> t<br>
  >> <br>
  >> ê<br>
  >> t<br>
  >> r<br>
  >> e<br>
  >> <br>
  >> u<br>
  >> t<br>
  >> i<br>
  >> l<br>
  >> i<br>
  >> s<br>
  >> é<br>
  >> <br>
  >> s<br>
  >> u<br>
  >> r<br>
  >> <br>
  >> l<br>
  >> e<br>
  >> <br>
  >> c<br>
  >> o<br>
  >> o<br>
  >> k<br>
  >> i<br>
  >> e<br>
  >> <br>
  >> d<br>
  >> e<br>
  >> <br>
  >> l<br>
  >> a<br>
  >> n<br>
  >> g<br>
  >> u<br>
  >> e<br>
  >> .<br>
* `LOGGING`
  > default value: `{}`
  >> Dictionnaire de configuration pour la journalisation (logging).<br>
* `LOGIN_URL`
  > default value: `/authentication_login/`
  >> url de redirection pour l’authentification de l’utilisateur<br>
  >> voir : [docs.djangoproject.com](https://docs.djangoproject.com/fr/4.2/ref/settings/#login-url)<br>
* `MANAGERS`
  > default value: `[]`
  >> Dans Pod, les "managers" sont destinataires des courriels de fin d’encodage<br>
  >> (et ainsi des vidéos déposées sur la plateforme).<br><br>
  >> Le premier manager renseigné est également contact des flus RSS.<br><br>
  >> Ils sont aussi destinataires des courriels de contact<br>
  >> si la variable `CONTACT_US_EMAIL` n’est pas renseignée.<br><br>
  >> _ref : [docs.djangoproject.com](https://docs.djangoproject.com/fr/4.2/ref/settings/#managers)_<br>
* `MONTH_DAY_FORMAT`
  > default value: `F j`
  >> L<br>
  >> e<br>
  >> <br>
  >> f<br>
  >> o<br>
  >> r<br>
  >> m<br>
  >> a<br>
  >> t<br>
  >> a<br>
  >> g<br>
  >> e<br>
  >> <br>
  >> p<br>
  >> a<br>
  >> r<br>
  >> <br>
  >> d<br>
  >> é<br>
  >> f<br>
  >> a<br>
  >> u<br>
  >> t<br>
  >> <br>
  >> p<br>
  >> o<br>
  >> u<br>
  >> r<br>
  >> <br>
  >> l<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> c<br>
  >> h<br>
  >> a<br>
  >> m<br>
  >> p<br>
  >> s<br>
  >> <br>
  >> d<br>
  >> e<br>
  >> <br>
  >> d<br>
  >> a<br>
  >> t<br>
  >> e<br>
  >> <br>
  >> d<br>
  >> a<br>
  >> n<br>
  >> s<br>
  >> <br>
  >> l<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> t<br>
  >> e<br>
  >> m<br>
  >> p<br>
  >> l<br>
  >> a<br>
  >> t<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> D<br>
  >> j<br>
  >> a<br>
  >> n<br>
  >> g<br>
  >> o<br>
  >> .<br>
* `NUMBER_GROUPING`
  > default value: `0`
  >> N<br>
  >> o<br>
  >> m<br>
  >> b<br>
  >> r<br>
  >> e<br>
  >> <br>
  >> d<br>
  >> e<br>
  >> <br>
  >> c<br>
  >> h<br>
  >> i<br>
  >> f<br>
  >> f<br>
  >> r<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> g<br>
  >> r<br>
  >> o<br>
  >> u<br>
  >> p<br>
  >> é<br>
  >> s<br>
  >> <br>
  >> e<br>
  >> n<br>
  >> s<br>
  >> e<br>
  >> m<br>
  >> b<br>
  >> l<br>
  >> e<br>
  >> <br>
  >> s<br>
  >> u<br>
  >> r<br>
  >> <br>
  >> l<br>
  >> a<br>
  >> <br>
  >> p<br>
  >> a<br>
  >> r<br>
  >> t<br>
  >> i<br>
  >> e<br>
  >> <br>
  >> e<br>
  >> n<br>
  >> t<br>
  >> i<br>
  >> è<br>
  >> r<br>
  >> e<br>
  >> <br>
  >> d<br>
  >> '<br>
  >> u<br>
  >> n<br>
  >> <br>
  >> n<br>
  >> o<br>
  >> m<br>
  >> b<br>
  >> r<br>
  >> e<br>
  >> .<br>
* `POD_VERSION`
  > default value: ``
  >> Version actuelle de l'application Pod.<br>
* `PREPEND_WWW`
  > default value: `False`
  >> S<br>
  >> i<br>
  >> <br>
  >> l<br>
  >> e<br>
  >> <br>
  >> s<br>
  >> o<br>
  >> u<br>
  >> s<br>
  >> -<br>
  >> d<br>
  >> o<br>
  >> m<br>
  >> a<br>
  >> i<br>
  >> n<br>
  >> e<br>
  >> <br>
  >> '<br>
  >> w<br>
  >> w<br>
  >> w<br>
  >> .<br>
  >> '<br>
  >> <br>
  >> d<br>
  >> o<br>
  >> i<br>
  >> t<br>
  >> <br>
  >> ê<br>
  >> t<br>
  >> r<br>
  >> e<br>
  >> <br>
  >> a<br>
  >> j<br>
  >> o<br>
  >> u<br>
  >> t<br>
  >> é<br>
  >> <br>
  >> a<br>
  >> u<br>
  >> x<br>
  >> <br>
  >> U<br>
  >> R<br>
  >> L<br>
  >> <br>
  >> q<br>
  >> u<br>
  >> i<br>
  >> <br>
  >> n<br>
  >> e<br>
  >> <br>
  >> l<br>
  >> '<br>
  >> o<br>
  >> n<br>
  >> t<br>
  >> <br>
  >> p<br>
  >> a<br>
  >> s<br>
  >> .<br>
* `PROXY_HOST`
  > default value: ``
  >> Utilisation du proxy - host<br>
* `PROXY_PORT`
  > default value: ``
  >> Utilisation du proxy - port<br>
* `REST_FRAMEWORK`
  > default value: `{}`
  >> Paramètres spécifiques au REST Framework.<br>
* `SECRET_KEY`
  > default value: `A_CHANGER`
  >> La clé secrète d’une installation Django.<br><br>
  >> Elle est utilisée dans le contexte de la signature cryptographique,<br>
  >> et doit être définie à une valeur unique et non prédictible.<br><br>
  >> Vous pouvez utiliser ce site pour en générer une : [djecrety.ir](https://djecrety.ir/)<br><br>
  >> _ref : [docs.djangoproject.com](https://docs.djangoproject.com/fr/4.2/ref/settings/#secret-key)_<br>
* `SECURE_SSL_REDIRECT`
  > default value: `False`
  >> À moins que votre site ne doive être disponible sur des connexions SSL et non SSL,<br>
  >> vous souhaiterez probablement définir ce paramètre sur True ou configurer un<br>
  >> load balancer ou reverse-proxy pour rediriger toutes les connexions vers HTTPS.<br>
* `SESSION_COOKIE_AGE`
  > default value: `14400`
  >> L’âge des cookies de sessions, en secondes (4h par défaut).<br>
* `SESSION_COOKIE_SAMESITE`
  > default value: `Lax`
  >> Cette option empêche le cookie d’être envoyé dans les requêtes inter-sites,<br>
  >> ce qui prévient les attaques CSRF et rend impossible<br>
  >> certaines méthodes de vol du cookie de session.<br>
  >> Voir [docs.djangoproject.com](https://docs.djangoproject.com/fr/4.2/ref/settings/#std-setting-SESSION_COOKIE_SAMESITE)<br>
* `SESSION_COOKIE_SECURE`
  > default value: `not DEBUG`
  >>
* `SESSION_EXPIRE_AT_BROWSER_CLOSE`
  > default value: `True`
  >> Indique s’il faut que la session expire lorsque l’utilisateur ferme son navigateur.<br>
* `SETTINGS_MODULE`
  > default value: `None`
  >> L<br>
  >> e<br>
  >> <br>
  >> c<br>
  >> h<br>
  >> e<br>
  >> m<br>
  >> i<br>
  >> n<br>
  >> <br>
  >> P<br>
  >> y<br>
  >> t<br>
  >> h<br>
  >> o<br>
  >> n<br>
  >> <br>
  >> v<br>
  >> e<br>
  >> r<br>
  >> s<br>
  >> <br>
  >> l<br>
  >> e<br>
  >> <br>
  >> m<br>
  >> o<br>
  >> d<br>
  >> u<br>
  >> l<br>
  >> e<br>
  >> <br>
  >> d<br>
  >> e<br>
  >> <br>
  >> c<br>
  >> o<br>
  >> n<br>
  >> f<br>
  >> i<br>
  >> g<br>
  >> u<br>
  >> r<br>
  >> a<br>
  >> t<br>
  >> i<br>
  >> o<br>
  >> n<br>
  >> <br>
  >> u<br>
  >> t<br>
  >> i<br>
  >> l<br>
  >> i<br>
  >> s<br>
  >> é<br>
  >> .<br>
* `SHORT_DATETIME_FORMAT`
  > default value: `m/d/Y P`
  >> L<br>
  >> e<br>
  >> <br>
  >> f<br>
  >> o<br>
  >> r<br>
  >> m<br>
  >> a<br>
  >> t<br>
  >> a<br>
  >> g<br>
  >> e<br>
  >> <br>
  >> p<br>
  >> a<br>
  >> r<br>
  >> <br>
  >> d<br>
  >> é<br>
  >> f<br>
  >> a<br>
  >> u<br>
  >> t<br>
  >> <br>
  >> p<br>
  >> o<br>
  >> u<br>
  >> r<br>
  >> <br>
  >> l<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> o<br>
  >> b<br>
  >> j<br>
  >> e<br>
  >> t<br>
  >> s<br>
  >> <br>
  >> d<br>
  >> a<br>
  >> t<br>
  >> e<br>
  >> t<br>
  >> i<br>
  >> m<br>
  >> e<br>
  >> <br>
  >> d<br>
  >> a<br>
  >> n<br>
  >> s<br>
  >> <br>
  >> l<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> t<br>
  >> e<br>
  >> m<br>
  >> p<br>
  >> l<br>
  >> a<br>
  >> t<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> D<br>
  >> j<br>
  >> a<br>
  >> n<br>
  >> g<br>
  >> o<br>
  >> .<br>
* `SHORT_DATE_FORMAT`
  > default value: `m/d/Y`
  >> L<br>
  >> e<br>
  >> <br>
  >> f<br>
  >> o<br>
  >> r<br>
  >> m<br>
  >> a<br>
  >> t<br>
  >> a<br>
  >> g<br>
  >> e<br>
  >> <br>
  >> p<br>
  >> a<br>
  >> r<br>
  >> <br>
  >> d<br>
  >> é<br>
  >> f<br>
  >> a<br>
  >> u<br>
  >> t<br>
  >> <br>
  >> p<br>
  >> o<br>
  >> u<br>
  >> r<br>
  >> <br>
  >> l<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> o<br>
  >> b<br>
  >> j<br>
  >> e<br>
  >> t<br>
  >> s<br>
  >> <br>
  >> d<br>
  >> a<br>
  >> t<br>
  >> e<br>
  >> <br>
  >> d<br>
  >> a<br>
  >> n<br>
  >> s<br>
  >> <br>
  >> l<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> t<br>
  >> e<br>
  >> m<br>
  >> p<br>
  >> l<br>
  >> a<br>
  >> t<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> D<br>
  >> j<br>
  >> a<br>
  >> n<br>
  >> g<br>
  >> o<br>
  >> .<br>
* `SHOW_SQL_QUERIES`
  > default value: `False`
  >> Afficher les requêtes SQL dans la console (mode debug).<br>
* `SIGNING_BACKEND`
  > default value: `django.core.signing.TimestampSigner`
  >> L<br>
  >> e<br>
  >> <br>
  >> b<br>
  >> a<br>
  >> c<br>
  >> k<br>
  >> e<br>
  >> n<br>
  >> d<br>
  >> <br>
  >> u<br>
  >> t<br>
  >> i<br>
  >> l<br>
  >> i<br>
  >> s<br>
  >> é<br>
  >> <br>
  >> p<br>
  >> o<br>
  >> u<br>
  >> r<br>
  >> <br>
  >> s<br>
  >> i<br>
  >> g<br>
  >> n<br>
  >> e<br>
  >> r<br>
  >> <br>
  >> l<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> c<br>
  >> o<br>
  >> o<br>
  >> k<br>
  >> i<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> e<br>
  >> t<br>
  >> <br>
  >> a<br>
  >> u<br>
  >> t<br>
  >> r<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> d<br>
  >> o<br>
  >> n<br>
  >> n<br>
  >> é<br>
  >> e<br>
  >> s<br>
  >> .<br>
* `SITE_ID`
  > default value: `1`
  >> L’identifiant (nombre entier) du site actuel.<br>
  >> Peut être utilisé pour mettre en place une instance multi-tenant<br>
  >> et ainsi gérer dans une même base de données du contenu pour plusieurs sites.<br><br>
  >> _ref : [docs.djangoproject.com](https://docs.djangoproject.com/fr/4.2/ref/settings/#site-id)_<br>
* `SPECTACULAR_SETTINGS`
  > default value: `{}`
  >> Configuration pour la génération du schéma OpenAPI via drf-spectacular.<br>
* `STORAGES`
  > default value: `{'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'}, 'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'}}`
  >> C<br>
  >> o<br>
  >> n<br>
  >> t<br>
  >> r<br>
  >> ô<br>
  >> l<br>
  >> e<br>
  >> <br>
  >> l<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> b<br>
  >> a<br>
  >> c<br>
  >> k<br>
  >> e<br>
  >> n<br>
  >> d<br>
  >> s<br>
  >> <br>
  >> d<br>
  >> e<br>
  >> <br>
  >> s<br>
  >> t<br>
  >> o<br>
  >> c<br>
  >> k<br>
  >> a<br>
  >> g<br>
  >> e<br>
  >> <br>
  >> p<br>
  >> o<br>
  >> u<br>
  >> r<br>
  >> <br>
  >> l<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> f<br>
  >> i<br>
  >> c<br>
  >> h<br>
  >> i<br>
  >> e<br>
  >> r<br>
  >> s<br>
  >> <br>
  >> (<br>
  >> D<br>
  >> j<br>
  >> a<br>
  >> n<br>
  >> g<br>
  >> o<br>
  >> <br>
  >> 4<br>
  >> .<br>
  >> 2<br>
  >> +<br>
  >> )<br>
  >> .<br>
* `TEST_SETTINGS`
  > default value: `False`
  >> Permet de vérifier si la configuration de la plateforme est en mode test.<br>
* `THIRD_PARTY_APPS`
  > default value: `[]`
  >> Liste des applications tierces accessibles.<br>
  >>
  >> ```python
  >> THIRD_PARTY_APPS = ["enrichment", "live"]
  >> ```
  >>
* `THOUSAND_SEPARATOR`
  > default value: `,`
  >> L<br>
  >> e<br>
  >> <br>
  >> s<br>
  >> é<br>
  >> p<br>
  >> a<br>
  >> r<br>
  >> a<br>
  >> t<br>
  >> e<br>
  >> u<br>
  >> r<br>
  >> <br>
  >> d<br>
  >> e<br>
  >> <br>
  >> m<br>
  >> i<br>
  >> l<br>
  >> l<br>
  >> i<br>
  >> e<br>
  >> r<br>
  >> s<br>
  >> <br>
  >> p<br>
  >> a<br>
  >> r<br>
  >> <br>
  >> d<br>
  >> é<br>
  >> f<br>
  >> a<br>
  >> u<br>
  >> t<br>
  >> <br>
  >> u<br>
  >> t<br>
  >> i<br>
  >> l<br>
  >> i<br>
  >> s<br>
  >> é<br>
  >> <br>
  >> l<br>
  >> o<br>
  >> r<br>
  >> s<br>
  >> <br>
  >> d<br>
  >> u<br>
  >> <br>
  >> f<br>
  >> o<br>
  >> r<br>
  >> m<br>
  >> a<br>
  >> t<br>
  >> a<br>
  >> g<br>
  >> e<br>
  >> <br>
  >> d<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> n<br>
  >> o<br>
  >> m<br>
  >> b<br>
  >> r<br>
  >> e<br>
  >> s<br>
  >> .<br>
* `TIME_FORMAT`
  > default value: `P`
  >> L<br>
  >> e<br>
  >> <br>
  >> f<br>
  >> o<br>
  >> r<br>
  >> m<br>
  >> a<br>
  >> t<br>
  >> <br>
  >> d<br>
  >> e<br>
  >> <br>
  >> s<br>
  >> o<br>
  >> r<br>
  >> t<br>
  >> i<br>
  >> e<br>
  >> <br>
  >> p<br>
  >> a<br>
  >> r<br>
  >> <br>
  >> d<br>
  >> é<br>
  >> f<br>
  >> a<br>
  >> u<br>
  >> t<br>
  >> <br>
  >> p<br>
  >> o<br>
  >> u<br>
  >> r<br>
  >> <br>
  >> l<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> o<br>
  >> b<br>
  >> j<br>
  >> e<br>
  >> t<br>
  >> s<br>
  >> <br>
  >> h<br>
  >> e<br>
  >> u<br>
  >> r<br>
  >> e<br>
  >> <br>
  >> d<br>
  >> a<br>
  >> n<br>
  >> s<br>
  >> <br>
  >> l<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> t<br>
  >> e<br>
  >> m<br>
  >> p<br>
  >> l<br>
  >> a<br>
  >> t<br>
  >> e<br>
  >> s<br>
  >> .<br>
* `TIME_INPUT_FORMATS`
  > default value: `['%H:%M:%S', '%H:%M:%S.%f', '%H:%M']`
  >> L<br>
  >> i<br>
  >> s<br>
  >> t<br>
  >> e<br>
  >> <br>
  >> d<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> f<br>
  >> o<br>
  >> r<br>
  >> m<br>
  >> a<br>
  >> t<br>
  >> s<br>
  >> <br>
  >> a<br>
  >> c<br>
  >> c<br>
  >> e<br>
  >> p<br>
  >> t<br>
  >> é<br>
  >> s<br>
  >> <br>
  >> l<br>
  >> o<br>
  >> r<br>
  >> s<br>
  >> <br>
  >> d<br>
  >> e<br>
  >> <br>
  >> l<br>
  >> '<br>
  >> a<br>
  >> n<br>
  >> a<br>
  >> l<br>
  >> y<br>
  >> s<br>
  >> e<br>
  >> <br>
  >> d<br>
  >> e<br>
  >> <br>
  >> l<br>
  >> '<br>
  >> h<br>
  >> e<br>
  >> u<br>
  >> r<br>
  >> e<br>
  >> <br>
  >> d<br>
  >> a<br>
  >> n<br>
  >> s<br>
  >> <br>
  >> l<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> f<br>
  >> o<br>
  >> r<br>
  >> m<br>
  >> u<br>
  >> l<br>
  >> a<br>
  >> i<br>
  >> r<br>
  >> e<br>
  >> s<br>
  >> .<br>
* `TIME_ZONE`
  > default value: `UTC`
  >> Une chaîne représentant le fuseau horaire pour cette installation.<br><br>
  >> _ref : [docs.djangoproject.com](https://docs.djangoproject.com/fr/4.2/ref/settings/#std:setting-TIME_ZONE)_<br>
  >> Liste des adresses destinataires des courriels de contact<br>
* `USE_DEBUG_TOOLBAR`
  > default value: `True`
  >> Une valeur booléenne qui active ou désactive l’outil de débogage.<br><br>
  >> Ne déployez jamais de site en production avec le réglage USE_DEBUG_TOOLBAR activé.<br><br>
  >> _ref : [django-debug-toolbar.readthedocs.io](https://django-debug-toolbar.readthedocs.io/en/latest/)_<br>
* `USE_I18N`
  > default value: `True`
  >> Activer le système de traduction de Django.<br>
* `USE_THOUSAND_SEPARATOR`
  > default value: `False`
  >> S<br>
  >> i<br>
  >> <br>
  >> l<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> n<br>
  >> o<br>
  >> m<br>
  >> b<br>
  >> r<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> d<br>
  >> o<br>
  >> i<br>
  >> v<br>
  >> e<br>
  >> n<br>
  >> t<br>
  >> <br>
  >> ê<br>
  >> t<br>
  >> r<br>
  >> e<br>
  >> <br>
  >> a<br>
  >> f<br>
  >> f<br>
  >> i<br>
  >> c<br>
  >> h<br>
  >> é<br>
  >> s<br>
  >> <br>
  >> a<br>
  >> v<br>
  >> e<br>
  >> c<br>
  >> <br>
  >> u<br>
  >> n<br>
  >> <br>
  >> s<br>
  >> é<br>
  >> p<br>
  >> a<br>
  >> r<br>
  >> a<br>
  >> t<br>
  >> e<br>
  >> u<br>
  >> r<br>
  >> <br>
  >> d<br>
  >> e<br>
  >> <br>
  >> m<br>
  >> i<br>
  >> l<br>
  >> l<br>
  >> i<br>
  >> e<br>
  >> r<br>
  >> s<br>
  >> .<br>
* `USE_TZ`
  > default value: `True`
  >> Activer la prise en charge des fuseaux horaires.<br>
* `USE_X_FORWARDED_HOST`
  > default value: `False`
  >> S<br>
  >> i<br>
  >> <br>
  >> l<br>
  >> '<br>
  >> e<br>
  >> n<br>
  >> -<br>
  >> t<br>
  >> ê<br>
  >> t<br>
  >> e<br>
  >> <br>
  >> X<br>
  >> -<br>
  >> F<br>
  >> o<br>
  >> r<br>
  >> w<br>
  >> a<br>
  >> r<br>
  >> d<br>
  >> e<br>
  >> d<br>
  >> -<br>
  >> H<br>
  >> o<br>
  >> s<br>
  >> t<br>
  >> <br>
  >> d<br>
  >> o<br>
  >> i<br>
  >> t<br>
  >> <br>
  >> ê<br>
  >> t<br>
  >> r<br>
  >> e<br>
  >> <br>
  >> u<br>
  >> t<br>
  >> i<br>
  >> l<br>
  >> i<br>
  >> s<br>
  >> é<br>
  >> <br>
  >> à<br>
  >> <br>
  >> l<br>
  >> a<br>
  >> <br>
  >> p<br>
  >> l<br>
  >> a<br>
  >> c<br>
  >> e<br>
  >> <br>
  >> d<br>
  >> e<br>
  >> <br>
  >> l<br>
  >> '<br>
  >> e<br>
  >> n<br>
  >> -<br>
  >> t<br>
  >> ê<br>
  >> t<br>
  >> e<br>
  >> <br>
  >> H<br>
  >> o<br>
  >> s<br>
  >> t<br>
  >> .<br>
* `USE_X_FORWARDED_PORT`
  > default value: `False`
  >> S<br>
  >> i<br>
  >> <br>
  >> l<br>
  >> '<br>
  >> e<br>
  >> n<br>
  >> -<br>
  >> t<br>
  >> ê<br>
  >> t<br>
  >> e<br>
  >> <br>
  >> X<br>
  >> -<br>
  >> F<br>
  >> o<br>
  >> r<br>
  >> w<br>
  >> a<br>
  >> r<br>
  >> d<br>
  >> e<br>
  >> d<br>
  >> -<br>
  >> P<br>
  >> o<br>
  >> r<br>
  >> t<br>
  >> <br>
  >> d<br>
  >> o<br>
  >> i<br>
  >> t<br>
  >> <br>
  >> ê<br>
  >> t<br>
  >> r<br>
  >> e<br>
  >> <br>
  >> u<br>
  >> t<br>
  >> i<br>
  >> l<br>
  >> i<br>
  >> s<br>
  >> é<br>
  >> <br>
  >> p<br>
  >> o<br>
  >> u<br>
  >> r<br>
  >> <br>
  >> d<br>
  >> é<br>
  >> t<br>
  >> e<br>
  >> r<br>
  >> m<br>
  >> i<br>
  >> n<br>
  >> e<br>
  >> r<br>
  >> <br>
  >> l<br>
  >> e<br>
  >> <br>
  >> p<br>
  >> o<br>
  >> r<br>
  >> t<br>
  >> <br>
  >> d<br>
  >> e<br>
  >> <br>
  >> l<br>
  >> a<br>
  >> <br>
  >> r<br>
  >> e<br>
  >> q<br>
  >> u<br>
  >> ê<br>
  >> t<br>
  >> e<br>
  >> .<br>
* `WSGI_APPLICATION`
  > default value: `config.wsgi.application`
  >> Chemin vers l'objet application WSGI.<br>
* `YEAR_MONTH_FORMAT`
  > default value: `F Y`
  >> L<br>
  >> e<br>
  >> <br>
  >> f<br>
  >> o<br>
  >> r<br>
  >> m<br>
  >> a<br>
  >> t<br>
  >> a<br>
  >> g<br>
  >> e<br>
  >> <br>
  >> p<br>
  >> a<br>
  >> r<br>
  >> <br>
  >> d<br>
  >> é<br>
  >> f<br>
  >> a<br>
  >> u<br>
  >> t<br>
  >> <br>
  >> d<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> c<br>
  >> h<br>
  >> a<br>
  >> m<br>
  >> p<br>
  >> s<br>
  >> <br>
  >> d<br>
  >> e<br>
  >> <br>
  >> d<br>
  >> a<br>
  >> t<br>
  >> e<br>
  >> <br>
  >> l<br>
  >> o<br>
  >> r<br>
  >> s<br>
  >> q<br>
  >> u<br>
  >> e<br>
  >> <br>
  >> s<br>
  >> e<br>
  >> u<br>
  >> l<br>
  >> s<br>
  >> <br>
  >> l<br>
  >> '<br>
  >> a<br>
  >> n<br>
  >> n<br>
  >> é<br>
  >> e<br>
  >> <br>
  >> e<br>
  >> t<br>
  >> <br>
  >> l<br>
  >> e<br>
  >> <br>
  >> m<br>
  >> o<br>
  >> i<br>
  >> s<br>
  >> <br>
  >> s<br>
  >> o<br>
  >> n<br>
  >> t<br>
  >> <br>
  >> a<br>
  >> f<br>
  >> f<br>
  >> i<br>
  >> c<br>
  >> h<br>
  >> é<br>
  >> s<br>
  >> .<br>

### Obsolescence

* `ACCOMMODATION_YEARS`
  > default value: `{}`
  >> Durée d’obsolescence personnalisée par Affiliation<br>
  >>
  >> ```python
  >> ACCOMMODATION_YEARS = {
  >>     'affiliate': 1
  >> }
  >> ```
  >>
* `ARCHIVE_HOW_MANY_DAYS`
  > default value: `365`
  >> Délai avant qu'une vidéo archivée ne soit déplacée vers archive_ROOT.<br>
* `ARCHIVE_OWNER_USERNAME`
  > default value: `"archive"`
  >> Nom de l’utilisateur pour l’archivage des vidéos.<br>
* `POD_ARCHIVE_AFFILIATION`
  > default value: `[]`
  >> Affiliations pour lesquelles on souhaite archiver la vidéo plutôt que de la supprimer.<br>
  >> Si l’affiliation du propriétaire est dans cette variable,<br>
  >> alors les vidéos sont affectées à un utilisateur précis<br>
  >> que l’on peut spécifier via le paramètre `ARCHIVE_OWNER_USERNAME`.<br>
  >> Elles sont mises en mode brouillon et le mot "archived" est ajouté à leur titre.<br>
  >> Enfin, elles sont également ajoutées à l’ensemble `Vidéo à Supprimer`<br>
  >> (accessible via l’interface d’admin).<br>
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
  >> ```
  >>
* `WARN_DEADLINES`
  > default value: `[60, 30, 7]`
  >> Liste de jours de délais avant l’obsolescence de la vidéo.<br>
  >> À chaque délai, le propriétaire reçoit un mail d’avertissement<br>
  >> pour éventuellement changer la date d’obsolescence de sa vidéo.<br>

### Modèle

* `COOKIE_LEARN_MORE`
  > default value: ``
  >> Ce paramètre permet d’afficher un lien "En savoir plus"<br>
  >> sur la boite de dialogue d’information sur l’usage des cookies dans Pod.<br>
  >> On peut préciser un lien vers les mentions légales ou page DPO.<br>
* `DARKMODE_ENABLED`
  > default value: `True`
  >> Permet aux utilisateurs d’activer un mode sombre.<br>
* `DYSLEXIAMODE_ENABLED`
  > default value: `True`
  >> Permet d’utiliser une police de caractères plus adaptée<br>
  >> aux personnes atteintes de dyslexie.<br>
* `HIDE_CHANNEL_TAB`
  > default value: `False`
  >> Si True, permet de cacher l’onglet chaine dans la barre de menu du haut.<br>
* `HIDE_CURSUS`
  > default value: `False`
  >> Si True, permet de ne pas afficher les cursus dans la colonne de droite.<br>
* `HIDE_DISCIPLINES`
  > default value: `False`
  >> Si True, permet de ne pas afficher les disciplines dans la colonne de droite.<br>
* `HIDE_LANGUAGE_SELECTOR`
  > default value: `False`
  >> Si True, permet de cacher le sélecteur de langue dans le menu du haut.<br>
* `HIDE_SHARE`
  > default value: `False`
  >> Si True, permet de ne pas afficher les liens de partage<br>
  >> sur les réseaux sociaux dans la colonne de droite.<br>
* `HIDE_TAGS`
  > default value: `False`
  >> Si True, permet de ne pas afficher le nuage de mots clés dans la colonne de droite.<br>
* `HIDE_TYPES`
  > default value: `False`
  >> Si True, permet de ne pas afficher la liste des types dans la colonne de droite.<br>
* `HIDE_TYPES_TAB`
  > default value: `False`
  >> Si True, permet de cacher l’entrée 'type' dans le menu de navigation.<br>
* `HIDE_USERNAME`
  > default value: `False`
  >> Voir description dans authentification<br>
  >> Si valeur vaut 'True', le username de l’utilisateur ne sera pas visible et<br>
  >> si la valeur vaut 'False' le username sera affiché aux utilisateurs authentifiés.<br>
  >> (pour respecter le RGPD)<br>
* `HIDE_USER_FILTER`
  > default value: `False`
  >> Si 'True', le filtre des vidéos par utilisateur ne sera plus visible<br>
  >> si 'False' le filtre ne sera visible qu’aux personnes authentifiées.<br>
  >> (pour respecter le RGPD)<br>
* `HIDE_USER_TAB`
  > default value: `False`
  >> Si valeur vaut 'True', l’onglet Utilisateur ne sera pas visible<br>
  >> et si la valeur vaut 'False' l’onglet Utilisateur ne sera visible<br>
  >> qu’aux personnes authentifiées.<br>
  >> (pour respecter le RGPD)<br>
* `HOMEPAGE_NB_VIDEOS`
  > default value: `12`
  >> Nombre de vidéos à afficher sur la page d’accueil.<br>
* `HOMEPAGE_SHOWS_PASSWORDED`
  > default value: `False`
  >> Afficher les vidéos dont l’accès est protégé par mot de passe sur la page d’accueil.<br>
* `HOMEPAGE_SHOWS_RESTRICTED`
  > default value: `False`
  >> Afficher les vidéos dont l’accès est protégé par authentification sur la page d’accueil.<br>
* `MENUBAR_HIDE_INACTIVE_OWNERS`
  > default value: `True`
  >> Les utilisateurs inactifs ne sont plus affichés dans la barre de menu utilisateur.<br>
* `MENUBAR_SHOW_STAFF_OWNERS_ONLY`
  > default value: `False`
  >> Les utilisateurs non staff ne sont plus affichés dans la barre de menu utilisateur.<br>
* `SHIB_NAME`
  > default value: `Identify Federation`
  >> Nom de la fédération d’identité utilisée<br>
  >> Affiché sur le bouton de connexion si l’authentification Shibboleth est utilisée.<br>
* `SHOW_EVENTS_ON_HOMEPAGE`
  > default value: `False`
  >> Si True, affiche les prochains évènements sur la page d’accueil.<br>
* `SHOW_ONLY_PARENT_THEMES`
  > default value: `False`
  >> Si True, affiche uniquement les thèmes de premier niveau dans l’onglet 'Chaîne'.<br>
* `TEMPLATE_VISIBLE_SETTINGS`
  > default value: `{}`
  >>
  >> ```python
  >> TEMPLATE_VISIBLE_SETTINGS = {
  >> # Titre du site.
  >> 'TITLE_SITE': 'Pod',
  >>  
  >> # Description du site.
  >> 'DESC_SITE': 'L’objectif d’Esup-Pod est de faciliter la mise à disposition
  >> de vidéos et ainsi d’encourager son utilisation dans l’enseignement et la recherche.',
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
  >> # Par exemple :
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
  >> #  dans le répertoire static de l’application custom et
  >> #  préciser le chemin d’accès. Par exemple : "custom/etab.css"
  >> 'CSS_OVERRIDE': '',
  >>  
  >> # Vous pouvez créer un template dans votre application custom et
  >> #  indiquer son chemin dans cette variable pour que ce code html,
  >> # ce template soit affiché en haut de votre page, le code est ajouté
  >> #  juste après la balise body.(Hors iframe)
  >> # Si le fichier créé est
  >> # '/opt/django_projects/podv4/pod/custom/templates/custom/preheader.html'
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
  >> ```
  >>

### Transcodage

* `TRANSCRIPTION_AUDIO_SPLIT_TIME`
  > default value: `600`
  >> Découpage de l’audio pour la transcription.<br>
* `TRANSCRIPTION_MODEL_PARAM`
  > default value: ``
  >> Paramétrage des modèles pour la transcription<br>
  >> Voir la documentation à cette adresse :<br>
  >> [esupportail.github.io](https://esupportail.github.io/Esup-Pod/4.x/Installation/optional/auto-transcription-install_fr)<br>
  >> Pour télécharger les modèles Vosk : [alphacephei.com/vosk/models](https://alphacephei.com/vosk/models)<br>
  >>
  >> ```python
  >> TRANSCRIPTION_MODEL_PARAM = {
  >>     # le modèle vosk
  >>     'VOSK': {
  >>         'fr': {
  >>             'model': "/path/of/project/Esup-Pod/transcription/model_fr/vosk/vosk-model-fr-0.6-linto-2.2.0",
  >>         }
  >>     }
  >>     # le modèle Whisper
  >>     'WHISPER': {
  >>         'fr': {
  >>             'model': "small",
  >>             'download_root': "/pod-transcription/transcription/whisper/",
  >>         },
  >>         'en': {
  >>             'model': "small",
  >>             'download_root': "/pod-transcription/transcription/whisper/",
  >>         }
  >>     }
  >> }
  >> ```
  >>
* `TRANSCRIPTION_NORMALIZE`
  > default value: `False`
  >> Activation de la normalisation de l’audio avant sa transcription.<br>
* `TRANSCRIPTION_NORMALIZE_TARGET_LEVEL`
  > default value: `-16.0`
  >> Niveau de normalisation de l’audio avant sa transcription.<br>
* `TRANSCRIPTION_STT_SENTENCE_BLANK_SPLIT_TIME`
  > default value: `0.5`
  >> Temps maximum en secondes des blancs entre chaque mot<br>
  >> pour le decoupage des sous-titres avec l’outil STT.<br>
* `TRANSCRIPTION_STT_SENTENCE_MAX_LENGTH`
  > default value: `2`
  >> Temps en secondes maximum pour une phrase lors de la transcription avec l’outil STT.<br>
* `TRANSCRIPTION_TYPE`
  > default value: `WHISPER`
  >> Choix de l’outil pour la transcription : `VOSK`ou `WHISPER`.<br>
* `TRANSCRIPT_VIDEO`
  > default value: `start_transcript`
  >> Fonction appelée pour lancer la transcription des vidéos.<br>
* `USE_TRANSCRIPTION`
  > default value: `False`
  >> Activation de la transcription.<br>

## Configuration des applications Esup_Pod

### Configuration application AI Enhancement

Application AI Enhancement pour pouvoir utiliser les améliorations des vidéos par l'intelligence artifficielle.<br>
Mettre `USE_AI_ENHANCEMENT` à True pour activer cette application.<br>

* `AI_ENHANCEMENT_API_URL`
  > default value: ``
  >> L’URL de l’API pour l’IA d’amélioration des vidéos.<br>
  >> Exemple : '<https://aristote.univ.fr/api>'<br>
  >> Lien du projet : <https://www.demainestingenieurs.centralesupelec.fr/aristote/><br>
* `AI_ENHANCEMENT_API_VERSION`
  > default value: ``
  >> La version de l’API pour l’IA d’amélioration des vidéos.<br>
* `AI_ENHANCEMENT_CGU_URL`
  > default value: ``
  >> L’URL des conditions générales d’utilisation de l’API pour l’IA d’amélioration des vidéos.<br>
  >> Exemple : '<https://aristote.univ.fr/cgu>'<br>
  >> Lien du projet : <https://www.demainestingenieurs.centralesupelec.fr/aristote/><br>
* `AI_ENHANCEMENT_CLIENT_ID`
  > default value: `mocked_id`
  >> L’ID du client de l’IA d’amélioration des vidéos.<br>
  >> Exemple : 'v1'<br>
* `AI_ENHANCEMENT_CLIENT_SECRET`
  > default value: `mocked_secret`
  >> Le mot de passe secret du client de l’IA d’amélioration des vidéos.<br>
* `AI_ENHANCEMENT_FIELDS_HELP_TEXT`
  > default value: ``
  >> Ensemble des textes d’aide affichés avec le formulaire d'amélioration d'une vidéo avec l'IA d'Aristote.<br>
* `AI_ENHANCEMENT_PROXY_URL`
  > default value: ``
  >> L’URL du serveur proxy pour les requêtes venant d'Aristote.<br>
  >> Exemple : '<https://proxy_aristote.univ.fr>'<br>
* `USE_AI_ENHANCEMENT`
  > default value: `False`
  >> Activation des améliorations de l'intelligence artificielle. Permet aux utilisateurs de l'utiliser.<br>

### Configuration de l’application authentification

* `AFFILIATION`
  > default value: ``
  >> Valeurs possibles pour l’affiliation du compte.<br>
* `AFFILIATION_EVENT`
  > default value: ``
  >> Groupes ou affiliations des personnes autorisées à créer un évènement.<br>
* `AFFILIATION_STAFF`
  > default value: ``
  >> Les personnes ayant pour affiliation les valeurs<br>
  >> renseignées dans cette variable ont automatiquement<br>
  >> la valeur staff de leur compte à True.<br>
* `ALLOWED_SUPERUSER_IPS`
  > default value: `[]`
  >> Liste d’IP et/ou de plages depuis lesquelles le statut 'superuser'<br>
  >> est autorisé.<br>
  >> Laissez vide pour autoriser toutes les sources.<br>
* `AUTH_CAS_USER_SEARCH`
  > default value: `user`
  >> Variable utilisée pour trouver les informations de l’individu<br>
  >> connecté dans le fichier renvoyé par le CAS lors de l’authentification.<br>
* `AUTH_LDAP_BIND_DN`
  > default value: ``
  >> Identifiant (DN) du compte pour se connecter au serveur LDAP.<br>
* `AUTH_LDAP_BIND_PASSWORD`
  > default value: ``
  >> Mot de passe du compte pour se connecter au serveur LDAP.<br>
* `AUTH_LDAP_USER_SEARCH`
  > default value: ``
  >> Filtre LDAP permettant la recherche de l’individu dans le serveur LDAP.<br>
* `AUTH_TYPE`
  > default value: ``
  >> Type d’authentification possible sur votre instance.<br>
  >> Choix : local, CAS, OIDC, Shibboleth<br>
* `CAS_ADMIN_AFFILIATION`
  > default value: `None`
  >> A<br>
  >> f<br>
  >> f<br>
  >> i<br>
  >> l<br>
  >> i<br>
  >> a<br>
  >> t<br>
  >> i<br>
  >> o<br>
  >> n<br>
  >> <br>
  >> r<br>
  >> e<br>
  >> q<br>
  >> u<br>
  >> i<br>
  >> s<br>
  >> e<br>
  >> <br>
  >> p<br>
  >> o<br>
  >> u<br>
  >> r<br>
  >> <br>
  >> a<br>
  >> c<br>
  >> c<br>
  >> é<br>
  >> d<br>
  >> e<br>
  >> r<br>
  >> <br>
  >> à<br>
  >> <br>
  >> l<br>
  >> '<br>
  >> i<br>
  >> n<br>
  >> t<br>
  >> e<br>
  >> r<br>
  >> f<br>
  >> a<br>
  >> c<br>
  >> e<br>
  >> <br>
  >> d<br>
  >> '<br>
  >> a<br>
  >> d<br>
  >> m<br>
  >> i<br>
  >> n<br>
  >> i<br>
  >> s<br>
  >> t<br>
  >> r<br>
  >> a<br>
  >> t<br>
  >> i<br>
  >> o<br>
  >> n<br>
  >> <br>
  >> D<br>
  >> j<br>
  >> a<br>
  >> n<br>
  >> g<br>
  >> o<br>
  >> <br>
  >> v<br>
  >> i<br>
  >> a<br>
  >> <br>
  >> C<br>
  >> A<br>
  >> S<br>
  >> .<br>
* `CAS_ADMIN_AUTH`
  > default value: `False`
  >> Permet d’activer l’authentification CAS pour la partie admin<br>
  >> Voir : [pypi.org/project/django-cas-sso](https://pypi.org/project/django-cas-sso/)<br>
* `CAS_ADMIN_PREFIX`
  > default value: `None`
  >> P<br>
  >> r<br>
  >> é<br>
  >> f<br>
  >> i<br>
  >> x<br>
  >> e<br>
  >> <br>
  >> d<br>
  >> e<br>
  >> <br>
  >> l<br>
  >> '<br>
  >> U<br>
  >> R<br>
  >> L<br>
  >> <br>
  >> d<br>
  >> '<br>
  >> a<br>
  >> d<br>
  >> m<br>
  >> i<br>
  >> n<br>
  >> i<br>
  >> s<br>
  >> t<br>
  >> r<br>
  >> a<br>
  >> t<br>
  >> i<br>
  >> o<br>
  >> n<br>
  >> <br>
  >> à<br>
  >> <br>
  >> p<br>
  >> r<br>
  >> o<br>
  >> t<br>
  >> é<br>
  >> g<br>
  >> e<br>
  >> r<br>
  >> <br>
  >> a<br>
  >> v<br>
  >> e<br>
  >> c<br>
  >> <br>
  >> C<br>
  >> A<br>
  >> S<br>
  >> <br>
  >> (<br>
  >> o<br>
  >> p<br>
  >> t<br>
  >> i<br>
  >> o<br>
  >> n<br>
  >> n<br>
  >> e<br>
  >> l<br>
  >> )<br>
  >> .<br>
* `CAS_ADMIN_REDIRECT`
  > default value: `False`
  >> Rediriger vers la connexion CAS pour l'interface d'administration.<br>
* `CAS_AFFILIATIONS_HANDLERS`
  > default value: `[]`
  >> L<br>
  >> i<br>
  >> s<br>
  >> t<br>
  >> e<br>
  >> <br>
  >> d<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> g<br>
  >> e<br>
  >> s<br>
  >> t<br>
  >> i<br>
  >> o<br>
  >> n<br>
  >> n<br>
  >> a<br>
  >> i<br>
  >> r<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> p<br>
  >> e<br>
  >> r<br>
  >> s<br>
  >> o<br>
  >> n<br>
  >> n<br>
  >> a<br>
  >> l<br>
  >> i<br>
  >> s<br>
  >> é<br>
  >> s<br>
  >> <br>
  >> p<br>
  >> o<br>
  >> u<br>
  >> r<br>
  >> <br>
  >> g<br>
  >> é<br>
  >> r<br>
  >> e<br>
  >> r<br>
  >> <br>
  >> l<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> a<br>
  >> f<br>
  >> f<br>
  >> i<br>
  >> l<br>
  >> i<br>
  >> a<br>
  >> t<br>
  >> i<br>
  >> o<br>
  >> n<br>
  >> s<br>
  >> <br>
  >> C<br>
  >> A<br>
  >> S<br>
  >> .<br>
* `CAS_AFFILIATIONS_KEY`
  > default value: `affiliation`
  >> C<br>
  >> l<br>
  >> é<br>
  >> <br>
  >> d<br>
  >> e<br>
  >> <br>
  >> l<br>
  >> '<br>
  >> a<br>
  >> t<br>
  >> t<br>
  >> r<br>
  >> i<br>
  >> b<br>
  >> u<br>
  >> t<br>
  >> <br>
  >> r<br>
  >> e<br>
  >> n<br>
  >> v<br>
  >> o<br>
  >> y<br>
  >> é<br>
  >> <br>
  >> p<br>
  >> a<br>
  >> r<br>
  >> <br>
  >> l<br>
  >> e<br>
  >> <br>
  >> C<br>
  >> A<br>
  >> S<br>
  >> <br>
  >> c<br>
  >> o<br>
  >> n<br>
  >> t<br>
  >> e<br>
  >> n<br>
  >> a<br>
  >> n<br>
  >> t<br>
  >> <br>
  >> l<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> a<br>
  >> f<br>
  >> f<br>
  >> i<br>
  >> l<br>
  >> i<br>
  >> a<br>
  >> t<br>
  >> i<br>
  >> o<br>
  >> n<br>
  >> s<br>
  >> <br>
  >> d<br>
  >> e<br>
  >> <br>
  >> l<br>
  >> '<br>
  >> u<br>
  >> t<br>
  >> i<br>
  >> l<br>
  >> i<br>
  >> s<br>
  >> a<br>
  >> t<br>
  >> e<br>
  >> u<br>
  >> r<br>
  >> .<br>
* `CAS_APPLY_ATTRIBUTES_TO_USER`
  > default value: `True`
  >> Appliquer automatiquement les attributs renvoyés par le CAS au profil de l'utilisateur.<br>
* `CAS_CHECK_NEXT`
  > default value: `True`
  >> V<br>
  >> é<br>
  >> r<br>
  >> i<br>
  >> f<br>
  >> i<br>
  >> e<br>
  >> <br>
  >> q<br>
  >> u<br>
  >> e<br>
  >> <br>
  >> l<br>
  >> e<br>
  >> <br>
  >> p<br>
  >> a<br>
  >> r<br>
  >> a<br>
  >> m<br>
  >> è<br>
  >> t<br>
  >> r<br>
  >> e<br>
  >> <br>
  >> '<br>
  >> n<br>
  >> e<br>
  >> x<br>
  >> t<br>
  >> '<br>
  >> <br>
  >> r<br>
  >> e<br>
  >> d<br>
  >> i<br>
  >> r<br>
  >> i<br>
  >> g<br>
  >> e<br>
  >> <br>
  >> v<br>
  >> e<br>
  >> r<br>
  >> s<br>
  >> <br>
  >> u<br>
  >> n<br>
  >> <br>
  >> d<br>
  >> o<br>
  >> m<br>
  >> a<br>
  >> i<br>
  >> n<br>
  >> e<br>
  >> <br>
  >> i<br>
  >> n<br>
  >> t<br>
  >> e<br>
  >> r<br>
  >> n<br>
  >> e<br>
  >> <br>
  >> p<br>
  >> o<br>
  >> u<br>
  >> r<br>
  >> <br>
  >> é<br>
  >> v<br>
  >> i<br>
  >> t<br>
  >> e<br>
  >> r<br>
  >> <br>
  >> l<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> r<br>
  >> e<br>
  >> d<br>
  >> i<br>
  >> r<br>
  >> e<br>
  >> c<br>
  >> t<br>
  >> i<br>
  >> o<br>
  >> n<br>
  >> s<br>
  >> <br>
  >> o<br>
  >> u<br>
  >> v<br>
  >> e<br>
  >> r<br>
  >> t<br>
  >> e<br>
  >> s<br>
  >> .<br>
* `CAS_CREATE_USER`
  > default value: `True`
  >> C<br>
  >> r<br>
  >> é<br>
  >> e<br>
  >> r<br>
  >> <br>
  >> u<br>
  >> n<br>
  >> <br>
  >> u<br>
  >> t<br>
  >> i<br>
  >> l<br>
  >> i<br>
  >> s<br>
  >> a<br>
  >> t<br>
  >> e<br>
  >> u<br>
  >> r<br>
  >> <br>
  >> D<br>
  >> j<br>
  >> a<br>
  >> n<br>
  >> g<br>
  >> o<br>
  >> <br>
  >> a<br>
  >> u<br>
  >> t<br>
  >> o<br>
  >> m<br>
  >> a<br>
  >> t<br>
  >> i<br>
  >> q<br>
  >> u<br>
  >> e<br>
  >> m<br>
  >> e<br>
  >> n<br>
  >> t<br>
  >> <br>
  >> s<br>
  >> i<br>
  >> <br>
  >> l<br>
  >> '<br>
  >> u<br>
  >> t<br>
  >> i<br>
  >> l<br>
  >> i<br>
  >> s<br>
  >> a<br>
  >> t<br>
  >> e<br>
  >> u<br>
  >> r<br>
  >> <br>
  >> a<br>
  >> u<br>
  >> t<br>
  >> h<br>
  >> e<br>
  >> n<br>
  >> t<br>
  >> i<br>
  >> f<br>
  >> i<br>
  >> é<br>
  >> <br>
  >> C<br>
  >> A<br>
  >> S<br>
  >> <br>
  >> n<br>
  >> '<br>
  >> e<br>
  >> x<br>
  >> i<br>
  >> s<br>
  >> t<br>
  >> e<br>
  >> <br>
  >> p<br>
  >> a<br>
  >> s<br>
  >> .<br>
* `CAS_CREATE_USER_WITH_ID`
  > default value: `False`
  >> U<br>
  >> t<br>
  >> i<br>
  >> l<br>
  >> i<br>
  >> s<br>
  >> e<br>
  >> r<br>
  >> <br>
  >> l<br>
  >> '<br>
  >> I<br>
  >> D<br>
  >> <br>
  >> C<br>
  >> A<br>
  >> S<br>
  >> <br>
  >> c<br>
  >> o<br>
  >> m<br>
  >> m<br>
  >> e<br>
  >> <br>
  >> c<br>
  >> l<br>
  >> é<br>
  >> <br>
  >> p<br>
  >> r<br>
  >> i<br>
  >> m<br>
  >> a<br>
  >> i<br>
  >> r<br>
  >> e<br>
  >> <br>
  >> p<br>
  >> o<br>
  >> u<br>
  >> r<br>
  >> <br>
  >> l<br>
  >> '<br>
  >> u<br>
  >> t<br>
  >> i<br>
  >> l<br>
  >> i<br>
  >> s<br>
  >> a<br>
  >> t<br>
  >> e<br>
  >> u<br>
  >> r<br>
  >> <br>
  >> c<br>
  >> r<br>
  >> é<br>
  >> é<br>
  >> .<br>
* `CAS_EXTRA_LOGIN_PARAMS`
  > default value: `{}`
  >> P<br>
  >> a<br>
  >> r<br>
  >> a<br>
  >> m<br>
  >> è<br>
  >> t<br>
  >> r<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> s<br>
  >> u<br>
  >> p<br>
  >> p<br>
  >> l<br>
  >> é<br>
  >> m<br>
  >> e<br>
  >> n<br>
  >> t<br>
  >> a<br>
  >> i<br>
  >> r<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> à<br>
  >> <br>
  >> e<br>
  >> n<br>
  >> v<br>
  >> o<br>
  >> y<br>
  >> e<br>
  >> r<br>
  >> <br>
  >> a<br>
  >> u<br>
  >> <br>
  >> s<br>
  >> e<br>
  >> r<br>
  >> v<br>
  >> e<br>
  >> u<br>
  >> r<br>
  >> <br>
  >> C<br>
  >> A<br>
  >> S<br>
  >> <br>
  >> l<br>
  >> o<br>
  >> r<br>
  >> s<br>
  >> <br>
  >> d<br>
  >> e<br>
  >> <br>
  >> l<br>
  >> a<br>
  >> <br>
  >> c<br>
  >> o<br>
  >> n<br>
  >> n<br>
  >> e<br>
  >> x<br>
  >> i<br>
  >> o<br>
  >> n<br>
  >> .<br>
* `CAS_FORCE_CHANGE_USERNAME_CASE`
  > default value: `False`
  >> Forcer la casse (minuscules ou majuscules) du nom d’utilisateur CAS<br>
  >> (permet de prévenir des doubles créations de comptes dans certains cas).<br>
  >> Valeurs possibles : `lower`, `upper`, `False`.<br>
* `CAS_FORCE_LOWERCASE_USERNAME`
  > default value: `False`
  >> Forcer le passage en minuscule du nom d’utilisateur CAS<br>
  >> (permet de prévenir des doubles créations de comptes dans certains cas).<br>
  >> OBSOLÈTE à partir de Pod 4.0. Utilisez `CAS_FORCE_CHANGE_USERNAME_CASE`<br>
* `CAS_FORCE_SSL_SERVICE_URL`
  > default value: `False`
  >> F<br>
  >> o<br>
  >> r<br>
  >> c<br>
  >> e<br>
  >> r<br>
  >> <br>
  >> l<br>
  >> '<br>
  >> U<br>
  >> R<br>
  >> L<br>
  >> <br>
  >> d<br>
  >> e<br>
  >> <br>
  >> s<br>
  >> e<br>
  >> r<br>
  >> v<br>
  >> i<br>
  >> c<br>
  >> e<br>
  >> <br>
  >> e<br>
  >> n<br>
  >> v<br>
  >> o<br>
  >> y<br>
  >> é<br>
  >> e<br>
  >> <br>
  >> a<br>
  >> u<br>
  >> <br>
  >> C<br>
  >> A<br>
  >> S<br>
  >> <br>
  >> à<br>
  >> <br>
  >> u<br>
  >> t<br>
  >> i<br>
  >> l<br>
  >> i<br>
  >> s<br>
  >> e<br>
  >> r<br>
  >> <br>
  >> H<br>
  >> T<br>
  >> T<br>
  >> P<br>
  >> S<br>
  >> .<br>
* `CAS_GATEWAY`
  > default value: `False`
  >> Si True, authentifie automatiquement l’individu<br>
  >> si déjà authentifié sur le serveur CAS<br>
  >> OBSOLÈTE à partir de Pod 4.0<br>
* `CAS_IGNORE_REFERER`
  > default value: `False`
  >> I<br>
  >> g<br>
  >> n<br>
  >> o<br>
  >> r<br>
  >> e<br>
  >> r<br>
  >> <br>
  >> l<br>
  >> '<br>
  >> e<br>
  >> n<br>
  >> -<br>
  >> t<br>
  >> ê<br>
  >> t<br>
  >> e<br>
  >> <br>
  >> R<br>
  >> e<br>
  >> f<br>
  >> e<br>
  >> r<br>
  >> e<br>
  >> r<br>
  >> <br>
  >> l<br>
  >> o<br>
  >> r<br>
  >> s<br>
  >> <br>
  >> d<br>
  >> e<br>
  >> <br>
  >> l<br>
  >> a<br>
  >> <br>
  >> d<br>
  >> é<br>
  >> t<br>
  >> e<br>
  >> r<br>
  >> m<br>
  >> i<br>
  >> n<br>
  >> a<br>
  >> t<br>
  >> i<br>
  >> o<br>
  >> n<br>
  >> <br>
  >> d<br>
  >> e<br>
  >> <br>
  >> l<br>
  >> '<br>
  >> U<br>
  >> R<br>
  >> L<br>
  >> <br>
  >> d<br>
  >> e<br>
  >> <br>
  >> r<br>
  >> e<br>
  >> d<br>
  >> i<br>
  >> r<br>
  >> e<br>
  >> c<br>
  >> t<br>
  >> i<br>
  >> o<br>
  >> n<br>
  >> <br>
  >> '<br>
  >> n<br>
  >> e<br>
  >> x<br>
  >> t<br>
  >> '<br>
  >> .<br>
* `CAS_LOCAL_NAME_FIELD`
  > default value: `username`
  >> C<br>
  >> h<br>
  >> a<br>
  >> m<br>
  >> p<br>
  >> <br>
  >> d<br>
  >> u<br>
  >> <br>
  >> m<br>
  >> o<br>
  >> d<br>
  >> è<br>
  >> l<br>
  >> e<br>
  >> <br>
  >> u<br>
  >> t<br>
  >> i<br>
  >> l<br>
  >> i<br>
  >> s<br>
  >> a<br>
  >> t<br>
  >> e<br>
  >> u<br>
  >> r<br>
  >> <br>
  >> p<br>
  >> o<br>
  >> u<br>
  >> r<br>
  >> <br>
  >> s<br>
  >> t<br>
  >> o<br>
  >> c<br>
  >> k<br>
  >> e<br>
  >> r<br>
  >> <br>
  >> l<br>
  >> e<br>
  >> <br>
  >> n<br>
  >> o<br>
  >> m<br>
  >> <br>
  >> d<br>
  >> '<br>
  >> u<br>
  >> t<br>
  >> i<br>
  >> l<br>
  >> i<br>
  >> s<br>
  >> a<br>
  >> t<br>
  >> e<br>
  >> u<br>
  >> r<br>
  >> <br>
  >> C<br>
  >> A<br>
  >> S<br>
  >> .<br>
* `CAS_LOGGED_MSG`
  > default value: `You are logged in as %s.`
  >> M<br>
  >> e<br>
  >> s<br>
  >> s<br>
  >> a<br>
  >> g<br>
  >> e<br>
  >> <br>
  >> a<br>
  >> f<br>
  >> f<br>
  >> i<br>
  >> c<br>
  >> h<br>
  >> é<br>
  >> <br>
  >> l<br>
  >> o<br>
  >> r<br>
  >> s<br>
  >> q<br>
  >> u<br>
  >> e<br>
  >> <br>
  >> l<br>
  >> '<br>
  >> u<br>
  >> t<br>
  >> i<br>
  >> l<br>
  >> i<br>
  >> s<br>
  >> a<br>
  >> t<br>
  >> e<br>
  >> u<br>
  >> r<br>
  >> <br>
  >> e<br>
  >> s<br>
  >> t<br>
  >> <br>
  >> c<br>
  >> o<br>
  >> n<br>
  >> n<br>
  >> e<br>
  >> c<br>
  >> t<br>
  >> é<br>
  >> <br>
  >> a<br>
  >> v<br>
  >> e<br>
  >> c<br>
  >> <br>
  >> s<br>
  >> u<br>
  >> c<br>
  >> c<br>
  >> è<br>
  >> s<br>
  >> .<br>
* `CAS_LOGIN_MSG`
  > default value: `None`
  >> M<br>
  >> e<br>
  >> s<br>
  >> s<br>
  >> a<br>
  >> g<br>
  >> e<br>
  >> <br>
  >> a<br>
  >> f<br>
  >> f<br>
  >> i<br>
  >> c<br>
  >> h<br>
  >> é<br>
  >> <br>
  >> l<br>
  >> o<br>
  >> r<br>
  >> s<br>
  >> q<br>
  >> u<br>
  >> e<br>
  >> <br>
  >> l<br>
  >> '<br>
  >> u<br>
  >> t<br>
  >> i<br>
  >> l<br>
  >> i<br>
  >> s<br>
  >> a<br>
  >> t<br>
  >> e<br>
  >> u<br>
  >> r<br>
  >> <br>
  >> d<br>
  >> o<br>
  >> i<br>
  >> t<br>
  >> <br>
  >> s<br>
  >> e<br>
  >> <br>
  >> c<br>
  >> o<br>
  >> n<br>
  >> n<br>
  >> e<br>
  >> c<br>
  >> t<br>
  >> e<br>
  >> r<br>
  >> .<br>
* `CAS_LOGIN_NEXT_PAGE`
  > default value: `None`
  >> U<br>
  >> R<br>
  >> L<br>
  >> <br>
  >> v<br>
  >> e<br>
  >> r<br>
  >> s<br>
  >> <br>
  >> l<br>
  >> a<br>
  >> q<br>
  >> u<br>
  >> e<br>
  >> l<br>
  >> l<br>
  >> e<br>
  >> <br>
  >> r<br>
  >> e<br>
  >> d<br>
  >> i<br>
  >> r<br>
  >> i<br>
  >> g<br>
  >> e<br>
  >> r<br>
  >> <br>
  >> a<br>
  >> p<br>
  >> r<br>
  >> è<br>
  >> s<br>
  >> <br>
  >> u<br>
  >> n<br>
  >> e<br>
  >> <br>
  >> c<br>
  >> o<br>
  >> n<br>
  >> n<br>
  >> e<br>
  >> x<br>
  >> i<br>
  >> o<br>
  >> n<br>
  >> <br>
  >> r<br>
  >> é<br>
  >> u<br>
  >> s<br>
  >> s<br>
  >> i<br>
  >> e<br>
  >> <br>
  >> s<br>
  >> i<br>
  >> <br>
  >> a<br>
  >> u<br>
  >> c<br>
  >> u<br>
  >> n<br>
  >> <br>
  >> p<br>
  >> a<br>
  >> r<br>
  >> a<br>
  >> m<br>
  >> è<br>
  >> t<br>
  >> r<br>
  >> e<br>
  >> <br>
  >> '<br>
  >> n<br>
  >> e<br>
  >> x<br>
  >> t<br>
  >> '<br>
  >> <br>
  >> n<br>
  >> '<br>
  >> e<br>
  >> s<br>
  >> t<br>
  >> <br>
  >> f<br>
  >> o<br>
  >> u<br>
  >> r<br>
  >> n<br>
  >> i<br>
  >> .<br>
* `CAS_LOGIN_URL_NAME`
  > default value: `cas_ng_login`
  >> N<br>
  >> o<br>
  >> m<br>
  >> <br>
  >> d<br>
  >> u<br>
  >> <br>
  >> m<br>
  >> o<br>
  >> t<br>
  >> i<br>
  >> f<br>
  >> <br>
  >> d<br>
  >> '<br>
  >> U<br>
  >> R<br>
  >> L<br>
  >> <br>
  >> p<br>
  >> o<br>
  >> u<br>
  >> r<br>
  >> <br>
  >> l<br>
  >> a<br>
  >> <br>
  >> v<br>
  >> u<br>
  >> e<br>
  >> <br>
  >> d<br>
  >> e<br>
  >> <br>
  >> c<br>
  >> o<br>
  >> n<br>
  >> n<br>
  >> e<br>
  >> x<br>
  >> i<br>
  >> o<br>
  >> n<br>
  >> <br>
  >> C<br>
  >> A<br>
  >> S<br>
  >> .<br>
* `CAS_LOGOUT_COMPLETELY`
  > default value: `True`
  >> Voir [kstateome/django-cas](https://github.com/kstateome/django-cas)<br>
* `CAS_LOGOUT_NEXT_PAGE`
  > default value: `None`
  >> U<br>
  >> R<br>
  >> L<br>
  >> <br>
  >> v<br>
  >> e<br>
  >> r<br>
  >> s<br>
  >> <br>
  >> l<br>
  >> a<br>
  >> q<br>
  >> u<br>
  >> e<br>
  >> l<br>
  >> l<br>
  >> e<br>
  >> <br>
  >> r<br>
  >> e<br>
  >> d<br>
  >> i<br>
  >> r<br>
  >> i<br>
  >> g<br>
  >> e<br>
  >> r<br>
  >> <br>
  >> a<br>
  >> p<br>
  >> r<br>
  >> è<br>
  >> s<br>
  >> <br>
  >> l<br>
  >> a<br>
  >> <br>
  >> d<br>
  >> é<br>
  >> c<br>
  >> o<br>
  >> n<br>
  >> n<br>
  >> e<br>
  >> x<br>
  >> i<br>
  >> o<br>
  >> n<br>
  >> .<br>
* `CAS_LOGOUT_URL_NAME`
  > default value: `cas_ng_logout`
  >> N<br>
  >> o<br>
  >> m<br>
  >> <br>
  >> d<br>
  >> u<br>
  >> <br>
  >> m<br>
  >> o<br>
  >> t<br>
  >> i<br>
  >> f<br>
  >> <br>
  >> d<br>
  >> '<br>
  >> U<br>
  >> R<br>
  >> L<br>
  >> <br>
  >> p<br>
  >> o<br>
  >> u<br>
  >> r<br>
  >> <br>
  >> l<br>
  >> a<br>
  >> <br>
  >> v<br>
  >> u<br>
  >> e<br>
  >> <br>
  >> d<br>
  >> e<br>
  >> <br>
  >> d<br>
  >> é<br>
  >> c<br>
  >> o<br>
  >> n<br>
  >> n<br>
  >> e<br>
  >> x<br>
  >> i<br>
  >> o<br>
  >> n<br>
  >> <br>
  >> C<br>
  >> A<br>
  >> S<br>
  >> .<br>
* `CAS_MAP_AFFILIATIONS`
  > default value: `False`
  >> Si True, des `groupes` d’utilisateurs sont créés automatiquement<br>
  >> à partir des affiliations CAS des individus qui se connectent sur la plateforme<br>
  >> et l’individu qui se connecte est ajouté automatiquement à ces groupes.<br>
* `CAS_PROXY_CALLBACK`
  > default value: `None`
  >> L<br>
  >> '<br>
  >> U<br>
  >> R<br>
  >> L<br>
  >> <br>
  >> à<br>
  >> <br>
  >> u<br>
  >> t<br>
  >> i<br>
  >> l<br>
  >> i<br>
  >> s<br>
  >> e<br>
  >> r<br>
  >> <br>
  >> c<br>
  >> o<br>
  >> m<br>
  >> m<br>
  >> e<br>
  >> <br>
  >> r<br>
  >> a<br>
  >> p<br>
  >> p<br>
  >> e<br>
  >> l<br>
  >> <br>
  >> (<br>
  >> c<br>
  >> a<br>
  >> l<br>
  >> l<br>
  >> b<br>
  >> a<br>
  >> c<br>
  >> k<br>
  >> )<br>
  >> <br>
  >> d<br>
  >> e<br>
  >> <br>
  >> p<br>
  >> r<br>
  >> o<br>
  >> x<br>
  >> y<br>
  >> .<br>
* `CAS_REDIRECT_URL`
  > default value: `/`
  >> U<br>
  >> R<br>
  >> L<br>
  >> <br>
  >> d<br>
  >> e<br>
  >> <br>
  >> r<br>
  >> e<br>
  >> d<br>
  >> i<br>
  >> r<br>
  >> e<br>
  >> c<br>
  >> t<br>
  >> i<br>
  >> o<br>
  >> n<br>
  >> <br>
  >> a<br>
  >> p<br>
  >> r<br>
  >> è<br>
  >> s<br>
  >> <br>
  >> u<br>
  >> n<br>
  >> e<br>
  >> <br>
  >> c<br>
  >> o<br>
  >> n<br>
  >> n<br>
  >> e<br>
  >> x<br>
  >> i<br>
  >> o<br>
  >> n<br>
  >> <br>
  >> r<br>
  >> é<br>
  >> u<br>
  >> s<br>
  >> s<br>
  >> i<br>
  >> e<br>
  >> <br>
  >> s<br>
  >> i<br>
  >> <br>
  >> a<br>
  >> u<br>
  >> c<br>
  >> u<br>
  >> n<br>
  >> <br>
  >> p<br>
  >> a<br>
  >> r<br>
  >> a<br>
  >> m<br>
  >> è<br>
  >> t<br>
  >> r<br>
  >> e<br>
  >> <br>
  >> '<br>
  >> n<br>
  >> e<br>
  >> x<br>
  >> t<br>
  >> '<br>
  >> <br>
  >> n<br>
  >> '<br>
  >> e<br>
  >> s<br>
  >> t<br>
  >> <br>
  >> p<br>
  >> r<br>
  >> é<br>
  >> s<br>
  >> e<br>
  >> n<br>
  >> t<br>
  >> .<br>
* `CAS_RENAME_ATTRIBUTES`
  > default value: `{}`
  >> U<br>
  >> n<br>
  >> <br>
  >> d<br>
  >> i<br>
  >> c<br>
  >> t<br>
  >> i<br>
  >> o<br>
  >> n<br>
  >> n<br>
  >> a<br>
  >> i<br>
  >> r<br>
  >> e<br>
  >> <br>
  >> p<br>
  >> o<br>
  >> u<br>
  >> r<br>
  >> <br>
  >> r<br>
  >> e<br>
  >> n<br>
  >> o<br>
  >> m<br>
  >> m<br>
  >> e<br>
  >> r<br>
  >> <br>
  >> l<br>
  >> e<br>
  >> s<br>
  >> <br>
  >> a<br>
  >> t<br>
  >> t<br>
  >> r<br>
  >> i<br>
  >> b<br>
  >> u<br>
  >> t<br>
  >> s<br>
  >> <br>
  >> C<br>
  >> A<br>
  >> S<br>
  >> <br>
  >> d<br>
  >> a<br>
  >> n<br>
  >> s<br>
  >> <br>
  >> l<br>
  >> a<br>
  >> <br>
  >> s<br>
  >> e<br>
  >> s<br>
  >> s<br>
  >> i<br>
  >> o<br>
  >> n<br>
  >> <br>
  >> u<br>
  >> t<br>
  >> i<br>
  >> l<br>
  >> i<br>
  >> s<br>
  >> a<br>
  >> t<br>
  >> e<br>
  >> u<br>
  >> r<br>
  >> .<br>
* `CAS_RENEW`
  > default value: `False`
  >> F<br>
  >> o<br>
  >> r<br>
  >> c<br>
  >> e<br>
  >> r<br>
  >> <br>
  >> l<br>
  >> e<br>
  >> <br>
  >> p<br>
  >> a<br>
  >> r<br>
  >> a<br>
  >> m<br>
  >> è<br>
  >> t<br>
  >> r<br>
  >> e<br>
  >> <br>
  >> r<br>
  >> e<br>
  >> n<br>
  >> e<br>
  >> w<br>
  >> <br>
  >> d<br>
  >> u<br>
  >> <br>
  >> C<br>
  >> A<br>
  >> S<br>
  >> <br>
  >> (<br>
  >> o<br>
  >> b<br>
  >> l<br>
  >> i<br>
  >> g<br>
  >> e<br>
  >> <br>
  >> à<br>
  >> <br>
  >> s<br>
  >> e<br>
  >> <br>
  >> r<br>
  >> e<br>
  >> c<br>
  >> o<br>
  >> n<br>
  >> n<br>
  >> e<br>
  >> c<br>
  >> t<br>
  >> e<br>
  >> r<br>
  >> <br>
  >> m<br>
  >> ê<br>
  >> m<br>
  >> e<br>
  >> <br>
  >> s<br>
  >> i<br>
  >> <br>
  >> u<br>
  >> n<br>
  >> e<br>
  >> <br>
  >> s<br>
  >> e<br>
  >> s<br>
  >> s<br>
  >> i<br>
  >> o<br>
  >> n<br>
  >> <br>
  >> S<br>
  >> S<br>
  >> O<br>
  >> <br>
  >> e<br>
  >> x<br>
  >> i<br>
  >> s<br>
  >> t<br>
  >> e<br>
  >> )<br>
  >> .<br>
* `CAS_RETRY_LOGIN`
  > default value: `False`
  >> R<br>
  >> é<br>
  >> e<br>
  >> s<br>
  >> s<br>
  >> a<br>
  >> y<br>
  >> e<br>
  >> r<br>
  >> <br>
  >> l<br>
  >> a<br>
  >> <br>
  >> c<br>
  >> o<br>
  >> n<br>
  >> n<br>
  >> e<br>
  >> x<br>
  >> i<br>
  >> o<br>
  >> n<br>
  >> <br>
  >> s<br>
  >> i<br>
  >> <br>
  >> l<br>
  >> a<br>
  >> <br>
  >> v<br>
  >> a<br>
  >> l<br>
  >> i<br>
  >> d<br>
  >> a<br>
  >> t<br>
  >> i<br>
  >> o<br>
  >> n<br>
  >> <br>
  >> d<br>
  >> u<br>
  >> <br>
  >> t<br>
  >> i<br>
  >> c<br>
  >> k<br>
  >> e<br>
  >> t<br>
  >> <br>
  >> C<br>
  >> A<br>
  >> S<br>
  >> <br>
  >> é<br>
  >> c<br>
  >> h<br>
  >> o<br>
  >> u<br>
  >> e<br>
  >> .<br>
* `CAS_SERVER_URL`
  > default value: `sso_cas`
  >> Url du serveur CAS de l’établissement. Format `http://url_cas`<br>
* `CAS_SESSION_FACTORY`
  > default value: `None`
  >> U<br>
  >> s<br>
  >> i<br>
  >> n<br>
  >> e<br>
  >> <br>
  >> p<br>
  >> e<br>
  >> r<br>
  >> s<br>
  >> o<br>
  >> n<br>
  >> n<br>
  >> a<br>
  >> l<br>
  >> i<br>
  >> s<br>
  >> é<br>
  >> e<br>
  >> <br>
  >> p<br>
  >> o<br>
  >> u<br>
  >> r<br>
  >> <br>
  >> c<br>
  >> r<br>
  >> é<br>
  >> e<br>
  >> r<br>
  >> <br>
  >> l<br>
  >> a<br>
  >> <br>
  >> s<br>
  >> e<br>
  >> s<br>
  >> s<br>
  >> i<br>
  >> o<br>
  >> n<br>
  >> <br>
  >> u<br>
  >> t<br>
  >> i<br>
  >> l<br>
  >> i<br>
  >> s<br>
  >> a<br>
  >> t<br>
  >> e<br>
  >> u<br>
  >> r<br>
  >> .<br>
* `CAS_STORE_NEXT`
  > default value: `False`
  >> S<br>
  >> t<br>
  >> o<br>
  >> c<br>
  >> k<br>
  >> e<br>
  >> r<br>
  >> <br>
  >> l<br>
  >> '<br>
  >> U<br>
  >> R<br>
  >> L<br>
  >> <br>
  >> '<br>
  >> n<br>
  >> e<br>
  >> x<br>
  >> t<br>
  >> '<br>
  >> <br>
  >> d<br>
  >> a<br>
  >> n<br>
  >> s<br>
  >> <br>
  >> l<br>
  >> a<br>
  >> <br>
  >> s<br>
  >> e<br>
  >> s<br>
  >> s<br>
  >> i<br>
  >> o<br>
  >> n<br>
  >> <br>
  >> a<br>
  >> u<br>
  >> <br>
  >> l<br>
  >> i<br>
  >> e<br>
  >> u<br>
  >> <br>
  >> d<br>
  >> e<br>
  >> <br>
  >> l<br>
  >> a<br>
  >> <br>
  >> p<br>
  >> a<br>
  >> s<br>
  >> s<br>
  >> e<br>
  >> r<br>
  >> <br>
  >> e<br>
  >> n<br>
  >> <br>
  >> p<br>
  >> a<br>
  >> r<br>
  >> a<br>
  >> m<br>
  >> è<br>
  >> t<br>
  >> r<br>
  >> e<br>
  >> <br>
  >> G<br>
  >> E<br>
  >> T<br>
  >> .<br>
* `CAS_USERNAME_ATTRIBUTE`
  > default value: `uid`
  >> L<br>
  >> '<br>
  >> a<br>
  >> t<br>
  >> t<br>
  >> r<br>
  >> i<br>
  >> b<br>
  >> u<br>
  >> t<br>
  >> <br>
  >> d<br>
  >> a<br>
  >> n<br>
  >> s<br>
  >> <br>
  >> l<br>
  >> a<br>
  >> <br>
  >> r<br>
  >> é<br>
  >> p<br>
  >> o<br>
  >> n<br>
  >> s<br>
  >> e<br>
  >> <br>
  >> C<br>
  >> A<br>
  >> S<br>
  >> <br>
  >> q<br>
  >> u<br>
  >> i<br>
  >> <br>
  >> c<br>
  >> o<br>
  >> n<br>
  >> t<br>
  >> i<br>
  >> e<br>
  >> n<br>
  >> t<br>
  >> <br>
  >> l<br>
  >> e<br>
  >> <br>
  >> n<br>
  >> o<br>
  >> m<br>
  >> <br>
  >> d<br>
  >> '<br>
  >> u<br>
  >> t<br>
  >> i<br>
  >> l<br>
  >> i<br>
  >> s<br>
  >> a<br>
  >> t<br>
  >> e<br>
  >> u<br>
  >> r<br>
  >> .<br>
* `CAS_VERIFY_SSL_CERTIFICATE`
  > default value: `True`
  >> V<br>
  >> é<br>
  >> r<br>
  >> i<br>
  >> f<br>
  >> i<br>
  >> e<br>
  >> r<br>
  >> <br>
  >> l<br>
  >> e<br>
  >> <br>
  >> c<br>
  >> e<br>
  >> r<br>
  >> t<br>
  >> i<br>
  >> f<br>
  >> i<br>
  >> c<br>
  >> a<br>
  >> t<br>
  >> <br>
  >> S<br>
  >> S<br>
  >> L<br>
  >> <br>
  >> d<br>
  >> u<br>
  >> <br>
  >> s<br>
  >> e<br>
  >> r<br>
  >> v<br>
  >> e<br>
  >> u<br>
  >> r<br>
  >> <br>
  >> C<br>
  >> A<br>
  >> S<br>
  >> .<br>
* `CAS_VERSION`
  > default value: `3`
  >> Version du protocole CAS.<br>
* `CREATE_GROUP_FROM_AFFILIATION`
  > default value: `False`
  >> Si True, des `groupes d’accès` sont créés automatiquement<br>
  >> à partir des affiliations des individus qui se connectent sur la plateforme<br>
  >> et l’individu qui se connecte est ajouté automatiquement à ces groupes.<br>
* `CREATE_GROUP_FROM_GROUPS`
  > default value: `False`
  >> Si True, des groupes sont créés automatiquement<br>
  >> à partir des groupes (attribut groups à memberOf)<br>
  >> des individus qui se connectent sur la plateforme<br>
  >> et l’individu qui se connecte est ajouté automatiquement à ces groupes<br>
* `DEFAULT_AFFILIATION`
  > default value: ``
  >> Affiliation par défaut d’un utilisateur authentifié par OIDC.<br>
  >> Ce contenu sera comparé à la liste AFFILIATION_STAFF<br>
  >> pour déterminer si l’utilisateur doit être admin Django<br>
* `ESTABLISHMENTS`
  > default value: ``
  >> [TODO] À compléter<br>
* `GROUP_STAFF`
  > default value: `AFFILIATION_STAFF`
  >> utilisé dans populatedCasbackend<br>
* `HIDE_LOCAL_LOGIN`
  > default value: `False`
  >> Si True, masque l’authentification locale<br>
* `HIDE_USERNAME`
  > default value: `False`
  >> Si valeur vaut `True`, le username de l’utilisateur<br>
  >> ne sera pas visible sur la plate-forme Pod<br>
  >> et si la valeur vaut `False` le username sera affiché aux utilisateurs authentifiés.<br>
  >> (pour respecter le RGPD)<br>
* `LDAP`
  > default value: ``
  >> Interroge le serveur LDAP pour renseigner les champs.<br>
* `LDAP_SERVER`
  > default value: ``
  >> Information de connection au serveur LDAP.<br>
  >> Le champ url peut contenir une ou plusieurs url<br>
  >> pour ajouter des hôtes de référence, exemple :<br>
  >> Si un seul host :<br>
  >> `{'url': "ldap.univ.fr'', 'port': 389, 'use_ssl': False}`<br>
  >> Si plusieurs :<br>
  >> `{'url': ("ldap.univ.fr'',"ldap2.univ.fr"), 'port': 389, 'use_ssl': False}`<br>
* `LDAP_SERVER_PORT`
  > default value: `389`
  >> Port du serveur LDAP.<br>
* `LDAP_SERVER_URL`
  > default value: `ldap://ldap.univ.fr`
  >> URL du serveur LDAP.<br>
* `LDAP_SERVER_USE_SSL`
  > default value: `False`
  >> Utiliser SSL pour la connexion LDAP.<br>
* `OIDC_CLAIM_FAMILY_NAME`
  > default value: `family_name`
  >>
* `OIDC_CLAIM_GIVEN_NAME`
  > default value: `given_name`
  >> Noms des Claim permettant de récupérer les attributs nom, prénom, email<br>
* `OIDC_CLAIM_PREFERRED_USERNAME`
  > default value: `preferred_username`
  >> Noms des Claim permettant de récupérer<br>
  >> l’attribut login mais dépendant de l’attribut du client dans l’IDP.<br>
* `OIDC_DEFAULT_ACCESS_GROUP_CODE_NAMES`
  > default value: `[]`
  >> Groupes d’accès attribués par défaut à un nouvel utilisateur authentifié par OIDC<br>
* `OIDC_DEFAULT_AFFILIATION`
  > default value: ``
  >> Affiliation par défaut d’un utilisateur authentifié par OIDC.<br>
  >> Ce contenu sera comparé à la liste AFFILIATION_STAFF<br>
  >> pour déterminer si l’utilisateur doit être admin Django.<br>
* `OIDC_NAME`
  > default value: ``
  >> Nom du Service Provider OIDC<br>
* `OIDC_OP_AUTHORIZATION_ENDPOINT`
  > default value: `https`
  >>
* `OIDC_OP_JWKS_ENDPOINT`
  > default value: `https`
  >> Différents paramètres pour OIDC<br>
  >> tant que `mozilla_django_oidc` n’accepte pas le mécanisme de discovery<br>
  >> _ref : [mozilla/mozilla-django-oidc](https://github.com/mozilla/mozilla-django-oidc/pull/309)_<br>
* `OIDC_OP_LOGOUT_ENDPOINT`
  > default value: ``
  >> Endpoint de déconnexion du fournisseur OIDC.<br>
* `OIDC_OP_TOKEN_ENDPOINT`
  > default value: `https`
  >>
* `OIDC_OP_USER_ENDPOINT`
  > default value: `https`
  >>
* `OIDC_RP_CLIENT_ID`
  > default value: `os.environ`
  >>
* `OIDC_RP_CLIENT_SECRET`
  > default value: `os.environ`
  >> `CLIENT_ID` et `CLIENT_SECRET` de OIDC sont plutôt à positionner<br>
  >> à travers des variables d’environnement.<br>
* `OIDC_RP_SIGN_ALGO`
  > default value: ``
  >>
* `POPULATE_USER`
  > default value: `None`
  >> Si utilisation de la connection CAS, renseigne les champs du compte<br>
  >> de la personne depuis une source externe.<br>
  >> Valeurs possibles :<br>
  >> * None (pas de renseignement),<br>
  >> * CAS (renseigne les champs depuis les informations renvoyées par le CAS),<br>
* `REMOTE_USER_HEADER`
  > default value: `REMOTE_USER`
  >> Nom de l’attribut dans les headers qui sert à identifier<br>
  >> l’utilisateur connecté avec Shibboleth.<br>
* `SHIBBOLETH_ATTRIBUTE_MAP`
  > default value: ``
  >> Mapping des attributs entre Shibboleth et la classe utilisateur<br>
* `SHIBBOLETH_STAFF_ALLOWED_DOMAINS`
  > default value: ``
  >> Permettre à l’utilisateur d’un domaine d’être membre du personnel.<br>
  >> Si vide, tous les domaines seront autorisés.<br>
* `SHIB_LOGOUT_URL`
  > default value: ``
  >> URL de déconnexion à votre instance Shibboleth<br>
* `SHIB_NAME`
  > default value: ``
  >> Nom de la fédération d’identité utilisée.<br>
* `SHIB_URL`
  > default value: ``
  >> URL de connexion à votre instance Shibboleth.<br>
* `SIMPLE_JWT`
  > default value: `{}`
  >> Configuration pour les JSON Web Tokens (JWT).<br>
* `USER_CAS_MAPPING_ATTRIBUTES`
  > default value: ``
  >> Liste de correspondance entre les champs d’un compte de Pod<br>
  >> et les champs renvoyés par le CAS.<br>
  >> OBSOLÈTE. Utilisez désormais `CAS_RENAME_ATTRIBUTES`.<br>
* `USER_LDAP_MAPPING_ATTRIBUTES`
  > default value: ``
  >> Liste de correspondance entre les champs d’un compte de Pod<br>
  >> et les champs renvoyés par le LDAP.<br>
* `USE_CAS`
  > default value: `False`
  >> Activation de l’authentification CAS en plus de l’authentification locale.<br>
* `USE_LDAP`
  > default value: `False`
  >> Activer l'authentification LDAP.<br>
* `USE_LOCAL_AUTH`
  > default value: `True`
  >> Activer l'authentification locale (nom d'utilisateur/mot de passe stockés dans la base de données).<br>
* `USE_OIDC`
  > default value: `False`
  >> Mettre à True pour utiliser l’authentification OpenID Connect.<br>
* `USE_SHIB`
  > default value: `False`
  >> Mettre à True pour utiliser l’authentification Shibboleth.<br>

### Configuration de l’application chapter


### Configuration de l’application completion

* `ACTIVE_MODEL_ENRICH`
  > default value: `False`
  >> Définissez à True pour activer la case à cocher dans l’édition des sous-titres.<br>
* `ALL_LANG_CHOICES`
  > default value: ``
  >> liste toutes les langues pour l’ajout de fichier de sous-titre<br>
  >> voir le fichier `pod/main/lang_settings.py`.<br>
* `DEFAULT_LANG_TRACK`
  > default value: `fr`
  >> langue par défaut pour l’ajout de piste à une vidéo.<br>
* `KIND_CHOICES`
  > default value: ``
  >> Liste de types de piste possibles pour une vidéo (sous-titre, légende etc.)<br>
* `LANG_CHOICES`
  > default value: ``
  >> Liste des langues proposées lors de l’ajout des vidéos.<br>
  >> Affichés en dessous d’une vidéo, les choix sont aussi utilisés pour affiner la recherche.<br>
* `LINK_SUPERPOSITION`
  > default value: `False`
  >> Si valeur vaut 'True', les URLs contenues dans le texte de superposition<br>
  >> seront transformées, à la lecture de la vidéo, en liens cliquables.<br>
* `MODEL_COMPILE_DIR`
  > default value: `/path/of/project/Esup-Pod/compile-model`
  >> Paramétrage des chemins du modèle pour la compilation<br>
  >> Pour télécharger les modèles : [alphacephei.com/vosk](https://alphacephei.com/vosk/lm#update-process)<br>
  >> Ajouter le modèle dans les sous-dossier de la langue correspondante<br>
  >> Exemple pour le français : `/path/of/project/Esup-Pod/compile-model/fr/`<br>
* `PREF_LANG_CHOICES`
  > default value: ``
  >> liste des langues à afficher en premier dans la liste des toutes les langues<br>
  >> voir le fichier `pod/main/lang_settings.py`<br>
* `ROLE_CHOICES`
  > default value: ``
  >> Liste de rôles possibles pour un contributeur.<br>
* `USE_ENRICH_READY`
  > default value: `False`
  >> voir `ACTIVE_MODEL_ENRICH`<br>

### Configuration de l’application Cut

Application Cut permettant de découper des vidéos.<br>
Mettre `USE_CUT` à True pour activer cette application.<br>

* `USE_CUT`
  > default value: `False`
  >> Activation de l’application Cut<br>

### Configuration de l’application dressing

Application Dressing pour customiser une vidéo avec un filigrane et des crédits.<br>
Mettre `USE_DRESSING` à True pour activer cette application.<br>

* `USE_DRESSING`
  > default value: `False`
  >> Activation des habillages.<br>
  >> Permet aux utilisateurs de customiser une vidéo avec un filigrane et des crédits.<br>

### Configuration de l’application duplicate

Application Duplicate pour créer une copie du formulaire d’une vidéo existante<br>
Mettre `USE_DUPLICATE` à True pour activer cette application.<br>

* `USE_DUPLICATE`
  > default value: `False`
  >> Activation de duplicate.<br>
  >> Permet aux utilisateurs de dupliquer une vidéo<br>

### Configuration de l’application enrichment


### Configuration de l’application Liens

Application Liens permettant d'ajouter des liens à la vidéo.<br>
Mettre `USE_HYPERLINKS` à True pour activer cette application.<br>

* `USE_HYPERLINKS`
  > default value: `False`
  >> Activation de l’application Liens<br>

### Configuration de l’application d’import vidéo

Application Import_video permettant d’importer des vidéos externes dans Pod.<br>
Mettre `USE_IMPORT_VIDEO` à True pour activer cette application.<br>

* `IMPORT_VIDEO_BBB_RECORDER_PATH`
  > default value: `/data/bbb-recorder/media/`
  >> Répertoire qui contiendra les fichiers vidéo générés par bbb-recorder.<br>
* `IMPORT_VIDEO_BBB_RECORDER_PLUGIN`
  > default value: `/home/pod/bbb-recorder/`
  >> Répertoire du plugin bbb-recorder (voir la documentation [jibon57/bbb-recorder](https://github.com/jibon57/bbb-recorder)).<br>
  >> bbb-recorder doit être installé dans ce répertoire, sur tous les serveurs d’encodage.<br>
  >> bbb-recorder crée un répertoire Downloads, au même niveau, qui nécessite de l’espace disque.<br>
* `MAX_UPLOAD_SIZE_ON_IMPORT`
  > default value: `4`
  >> Taille maximum en Go des fichiers vidéos qui peuvent être importés sur la plateforme<br>
  >> via l’application import_video (0 = pas de taille maximum).<br>
* `RESTRICT_EDIT_IMPORT_VIDEO_ACCESS_TO_STAFF_ONLY`
  > default value: `True`
  >> Seuls les utilisateurs "staff" pourront importer des vidéos<br>
* `USE_IMPORT_VIDEO`
  > default value: `False`
  >> Activation de l’application d’import des vidéos<br>
* `USE_IMPORT_VIDEO_BBB_RECORDER`
  > default value: `False`
  >> Utilisation du plugin bbb-recorder pour le module import-vidéo;<br>
  >> utile pour convertir une présentation BigBlueButton en fichier vidéo.<br>

### Configuration de l’application live

* `AFFILIATION_EVENT`
  > default value: `['faculty', 'employee', 'staff']`
  >> Groupes ou affiliations des personnes autorisées à créer un évènement.<br>
* `BROADCASTER_PILOTING_SOFTWARE`
  > default value: `[]`
  >> Types de logiciel de serveur de streaming utilisés.<br>
  >> Actuellement disponible Wowza et SMP.<br>
  >> Il faut préciser cette valeur pour l’activer `['Wowza', 'SMP']`<br>
  >> Si vous utilisez une autre logiciel,<br>
  >> il faut développer une interface dans `pod/live/pilotingInterface.py`<br>
* `DEFAULT_EVENT_PATH`
  > default value: ``
  >> Chemin racine du répertoire où sont déposés temporairement<br>
  >> les enregistrements des évènements éffectués depuis POD<br>
  >> pour convertion en ressource vidéo (VOD)<br>
* `DEFAULT_EVENT_THUMBNAIL`
  > default value: `/img/default-event.svg`
  >> Image par défaut affichée comme poster ou vignette, utilisée pour présenter l’évènement.<br>
  >> Cette image doit se situer dans le répertoire `static`.<br>
* `DEFAULT_EVENT_TYPE_ID`
  > default value: `1`
  >> Type par défaut affecté à un évènement direct<br>
  >> (en général, le type ayant pour identifiant '1' est 'Other')<br>
* `DEFAULT_THUMBNAIL`
  > default value: `img/default.svg`
  >> Image par défaut affichée comme poster ou vignette, utilisée pour présenter la vidéo.<br>
  >> Cette image doit se situer dans le répertoire static.<br>
* `EMAIL_ON_EVENT_SCHEDULING`
  > default value: `True`
  >> Si True, un courriel est envoyé aux managers et à l’auteur<br>
  >> (si DEBUG est à False) à la création/modification d’un event.<br>
* `EVENT_ACTIVE_AUTO_START`
  > default value: `False`
  >> Permet de lancer automatiquement l’enregistrement sur l’interface utilisée<br>
  >> (wowza, ) sur le broadcaster et spécifié par `BROADCASTER_PILOTING_SOFTWARE`.<br>
* `EVENT_CHECK_MAX_ATTEMPT`
  > default value: `10`
  >> Nombre de tentatives maximum pour vérifier la présence / taille d’un fichier sur le filesystem<br>
* `EVENT_GROUP_ADMIN`
  > default value: `event admin`
  >> Permet de préciser le nom du groupe dans lequel les utilisateurs<br>
  >> peuvent planifier un évènement sur plusieurs jours.<br>
* `HEARTBEAT_DELAY`
  > default value: `45`
  >> Temps (en secondes) entre deux envois d’un signal au serveur,<br>
  >> pour signaler la présence sur un live.<br>
  >> Peut être augmenté en cas de perte de performance,<br>
  >> mais au détriment de la qualité du comptage des valeurs.<br>
* `LIVE_CELERY_TRANSCRIPTION`
  > default value: `False`
  >>
  >> Activer la transcription déportée sur une machine distante.<br>
* `LIVE_TRANSCRIPTIONS_FOLDER`
  > default value: ``
  >>
  >> Dossier contenat les fichiers de sous-titre au format vtt pour les directs<br>
* `LIVE_VOSK_MODEL`
  > default value: `{}`
  >>
  >> Paramétrage des modèles pour la transcription des directs<br>
  >> La documentation sera présente prochaînement<br>
  >> Pour télécharger les Modèles Vosk : [alphacephei.com/vosk/models](https://alphacephei.com/vosk/models)<br>
  >>
  >> ```python
  >> LIVE_VOSK_MODEL = {
  >>    'fr': {
  >>        'model': "/path/of/project/django_projects/transcription/live/fr/vosk-model-small-fr-0.22",
  >>     }
  >> }
  >> ```
  >>
* `USE_BBB`
  > default value: `False`
  >> Utilisation de BigBlueButton<br>
  >> Retiré à partir de la version 3.8.2 de Pod (remplacé par le module des réunions)<br>
* `USE_BBB_LIVE`
  > default value: `False`
  >> Utilisation du système de diffusion de Webinaires en lien avec BigBlueButton<br>
  >> Retiré à partir de la version 3.8.2 de Pod (remplacé par le module des réunions)<br>
* `USE_LIVE_TRANSCRIPTION`
  > default value: `False`
  >> Activer l’auto-transcription pour les directs<br>
  >>
* `VIEW_EXPIRATION_DELAY`
  > default value: `60`
  >> Délai (en seconde) selon lequel une vue est considérée comme expirée<br>
  >> si elle n’a pas renvoyé de signal depuis.<br>

### Configuration de l’application LTI

* `LTI_ENABLED`
  > default value: `False`
  >> Configuration / Activation du LTI voir pod/main/settings.py L.224<br>
* `PYLTI_CONFIG`
  > default value: `{}`
  >> Cette variable permet de configurer l’application cliente et le secret partagé<br>
  >>
  >> ```python
  >> PYLTI_CONFIG = {
  >>     'consumers': {
  >>         '<random number string>': {
  >>             'secret': '<random number string>'
  >>         }
  >>     }
  >> }
  >> ```
  >>

### Configuration de l’application main

* `HOMEPAGE_VIEW_VIDEOS_FROM_NON_VISIBLE_CHANNELS`
  > default value: `False`
  >> Affiche les vidéos de chaines non visibles sur la page d’accueil<br>
* `SOCIAL_SHARE`
  > default value: `['X', 'FACEBOOK', 'LINKEDIN', 'BLUESKY', 'MASTODON']`
  >> Choix d'affichage des liens de partage des réseaux sociaux<br>
* `USE_BBB`
  > default value: `True`
  >> Utilisation de BigBlueButton<br>
  >> Module obsolète.<br>
* `USE_BBB_LIVE`
  > default value: `False`
  >> Utilisation du système de diffusion de Webinaires en lien avec BigBlueButton<br>
  >> [TODO] À retirer dans les futures versions de Pod<br>
* `USE_IMPORT_VIDEO`
  > default value: `False`
  >> Activation de l’application d’import des vidéos<br>
* `USE_MEETING`
  > default value: `False`
  >> Activation de l’application meeting<br>
* `USE_OPENCAST_STUDIO`
  > default value: `False`
  >> Activation du studio [Opencast](https://opencast.org/)<br>
* `VERSION`
  > default value: ``
  >> Version courante du projet<br>
* `WEBTV_MODE`
  > default value: `False`
  >> Mode webtv permet de basculer POD en une application webtv ensupprimant les boutons de connexions par exemple<br>

### Configuration de l’application meeting

Application Meeting pour la gestion de reunion avec BBB.<br>
Mettre `USE_MEETING` à True pour activer cette application.<br>
`BBB_API_URL` et `BBB_SECRET_KEY` sont obligatoires pour faire fonctionner l’application<br>

* `BBB_API_URL`
  > default value: ``
  >> Indiquer l’URL API de BBB par ex `https://webconf.univ.fr/bigbluebutton/api`.<br>
* `BBB_LOGOUT_URL`
  > default value: ``
  >> Indiquer l’URL de retour au moment où vous quittez la réunion BBB. Ce champ est optionnel.<br>
* `BBB_MEETING_INFO`
  > default value: `{}`
  >> Dictionnaire de `clé:valeur` permettant d’afficher les informations<br>
  >> d’une session de réunion dans BBB<br>
  >> Voici la liste par défaut<br>
  >>
  >> ```python
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
  >> ```
  >>
* `BBB_SECRET_KEY`
  > default value: ``
  >> Clé de votre serveur BBB.<br>
  >> Vous pouvez récupérer cette clé à l’aide de la commande<br>
  >> `bbb-conf --secret` sur le serveur BBB.<br>
* `DEFAULT_MEETING_THUMBNAIL`
  > default value: `/img/default-meeting.svg`
  >> Image par défaut affichée comme poster ou vignette, utilisée pour présenter la réunion.<br>
  >> Cette image doit se situer dans le répertoire `static`.<br>
* `MEETING_DATE_FIELDS`
  > default value: `()`
  >> liste des champs du formulaire de creation d’une reunion<br>
  >> les champs sont regroupés dans un ensemble de champs<br>
  >>
  >> ```python
  >> MEETING_DATE_FIELDS:
  >> (
  >>     "start",
  >>     "start_time",
  >>     "expected_duration",
  >> )
  >> ```
  >>
* `MEETING_DISABLE_RECORD`
  > default value: `True`
  >> Mettre à True pour désactiver les enregistrements de réunion<br>
  >> Configuration de l’enregistrement des réunions.<br>
  >> Ce champ n’est pas pris en compte si `MEETING_DISABLE_RECORD = True`.<br>
* `MEETING_MAIN_FIELDS`
  > default value: `()`
  >> Permet de définir les champs principaux du formulaire de création d’une réunion<br>
  >> les champs principaux sont affichés directement dans la page de formulaire d’une réunion<br>
  >>
  >> ```python
  >> MEETING_MAIN_FIELDS:
  >> (
  >>     "name",
  >>     "owner",
  >>     "additional_owners",
  >>     "attendee_password",
  >>     "is_restricted",
  >>     "restrict_access_to_groups",
  >> )
  >> ```
  >>
* `MEETING_MAX_DURATION`
  > default value: `5`
  >> permet de définir la durée maximum pour une reunion<br>
  >> (en heure)<br>
* `MEETING_PRE_UPLOAD_SLIDES`
  > default value: ``
  >>
  >> Diaporama préchargé pour les réunions virtuelles.<br>
  >> Un utilisateur peut remplacer cette valeur en choisissant un diaporama<br>
  >> lors de la création d’une réunion virtuelle.<br>
  >> Doit se trouver dans le répertoire statique.<br>
* `MEETING_RECORD_FIELDS`
  > default value: `()`
  >> ensemble des champs qui seront cachés si `MEETING_DISABLE_RECORD` est défini à true.<br>
  >>
  >> ```python
  >> MEETING_RECORD_FIELDS: ("record", "auto_start_recording", "allow_start_stop_recording")
  >> ```
  >>
* `MEETING_RECURRING_FIELDS`
  > default value: `()`
  >> Liste de tous les champs permettant de définir la récurrence d’une reunion<br>
  >> tous ces champs sont regroupés dans un ensemble de champs affichés dans une modale<br>
  >>
  >> ```python
  >> MEETING_RECURRING_FIELDS:
  >> (
  >>     "recurrence",
  >>     "frequency",
  >>     "recurring_until",
  >>     "nb_occurrences",
  >>     "weekdays",
  >>     "monthly_type",
  >> )
  >> ```
  >>
* `MEETING_WEBINAR_AFFILIATION`
  > default value: `['faculty', 'employee', 'staff']`
  >> Groupes d’accès ou affiliations des personnes autorisées à créer un webinaire<br>
* `MEETING_WEBINAR_FIELDS`
  > default value: `("is_webinar", "enable_chat")`
  >> Permet de définir les champs complémentaires du formulaire de création d’un webinaire<br>
  >> ces champs complémentaires sont affichés directement dans la page de formulaire d’un webinaire<br>
  >>
  >> ```python
  >> MEETING_WEBINAR_FIELDS:
  >> (
  >>     "is_webinar",
  >>     "enable_chat",
  >> )
  >> ```
  >>
* `MEETING_WEBINAR_GROUP_ADMIN`
  > default value: `webinar admin`
  >> Groupe des personnes autorisées à créer un webinaire<br>
* `MEETING_WEBINAR_SIPMEDIAGW_TOKEN`
  > default value: ``
  >> Jeton bearer du serveur SIPMediaGW qui gère les webinaires<br>
  >> Retiré à partir de la version 3.8.2 de Pod (cf. passerelle de live)<br>
* `MEETING_WEBINAR_SIPMEDIAGW_URL`
  > default value: ``
  >> URL du serveur SIPMediaGW qui gère les webinaires (Ex: `https://sipmediagw.univ.fr`)<br>
  >> Retiré à partir de la version 3.8.2 de Pod (remplacé par le module des réunions, cf. passerelle de live)<br>
* `RESTRICT_EDIT_MEETING_ACCESS_TO_STAFF_ONLY`
  > default value: `False`
  >> Seuls les utilisateurs "staff" pourront éditer les réunions<br>
* `USE_MEETING`
  > default value: `False`
  >> Activer l’application meeting<br>
* `USE_MEETING_WEBINAR`
  > default value: `False`
  >> Activation du mode Webinaire pour le module des réunions<br>

### Configuration de l’application playlist

Application Playlist pour la gestion des playlists.<br>
Mettre `USE_PLAYLIST` à True pour activer cette application.<br>

* `COUNTDOWN_PLAYLIST_PLAYER`
  > default value: `0`
  >> Compte à rebours utilisé entre chaque vidéo lors de<br>
  >> la lecture d’une playlist en lecture automatique.<br>
  >> Le compte à rebours n’est pas présent s’il est à 0.<br>
* `DEFAULT_PLAYLIST_THUMBNAIL`
  > default value: `/static/playlist/img/default-playlist.svg`
  >> Image par défaut affichée comme poster ou vignette, utilisée pour présenter la playlist.<br>
  >> Cette image doit se situer dans le répertoire `static`.<br>
* `RESTRICT_PROMOTED_PLAYLIST_ACCESS_TO_STAFF_ONLY`
  > default value: `True`
  >> Restreindre l’accès à la création de listes de lecture promues<br>
  >> au staff uniquement.<br>
* `USE_FAVORITES`
  > default value: `False`
  >> Activation des vidéos favorites.<br>
  >> Permet aux utilisateurs d’ajouter des vidéos dans leurs favoris.<br>
* `USE_PLAYLIST`
  > default value: `False`
  >> Activation des playlist. Permet aux utilisateurs d’ajouter des vidéos dans une playlist.<br>
* `USE_PROMOTED_PLAYLIST`
  > default value: `False`
  >> Activation des playlist promues.<br>
  >> Permet aux utilisateurs d'utiliser les listes de lecture promues.<br>

### Configuration de l’application podfile

* `FILES_DIR`
  > default value: `files`
  >> Nom du répertoire racine où les fichiers "complémentaires"<br>
  >> (hors vidéos etc.) sont téléversés. Notament utilisé par PODFILE<br>
  >> À modifier principalement pour indiquer dans LOCATION votre serveur<br>
  >> de cache si elle n’est pas sur la même machine que votre POD.<br>
* `FILE_ALLOWED_EXTENSIONS`
  > default value: `('doc', 'docx', 'odt', 'pdf', 'xls', 'xlsx', 'ods', 'ppt', 'pptx', 'txt', 'html', 'htm', 'vtt', 'srt')`
  >> Extensions autorisées pour les documents téléversés<br>
  >> dans le gestionnaire de fichier (en minuscules).<br>
* `FILE_MAX_UPLOAD_SIZE`
  > default value: `10`
  >> Poids maximum en Mo par fichier téléversé dans le gestionnaire de fichier<br>
* `IMAGE_ALLOWED_EXTENSIONS`
  > default value: `('jpg', 'jpeg', 'bmp', 'png', 'gif', 'tiff', 'webp')`
  >> Extensions autorisées pour les images téléversées<br>
  >> dans le gestionnaire de fichier. (en minuscules)<br>

### Configuration de l’application progressive_web_app

* `USE_NOTIFICATIONS`
  > default value: `False`
  >> Activation des notifications, attention, elles sont actives par défaut.<br>
* `WEBPUSH_SETTINGS`
  > default value:

  ```python
  {
      'VAPID_PUBLIC_KEY': '',
      'VAPID_PRIVATE_KEY': '',
      'VAPID_ADMIN_EMAIL': 'contact@esup-portail.org'
  }
  ```

  >> Les clés VAPID sont nécessaires à la lib [django-webpush](https://github.com/safwanrahman/django-webpush).<br>
  >> Elles peuvent être générées avec [web-push-codelab.glitch.me](https://web-push-codelab.glitch.me/).<br>

### Configuration de l'application quiz

Application Quiz pour ajouter des questions sur les vidéos.<br>
Mettre `USE_QUIZ` à True pour activer cette application.<br>

* `USE_QUIZ`
  > default value: `False`
  >> Activation des quiz. Permet aux utilisateurs de créer, répondre et utiliser des quiz dans les vidéos.<br>

### Configuration de l’application recorder

* `ALLOW_MANUAL_RECORDING_CLAIMING`
  > default value: `False`
  >> Si True, active un lien dans le menu de l’utilisateur permettant de réclamer un enregistrement.<br>
* `ALLOW_RECORDER_MANAGER_CHOICE_VID_OWNER`
  > default value: `True`
  >> Si True, le manager de l’enregistreur pourra choisir un propriétaire de l’enregistrement.<br>
* `DEFAULT_RECORDER_ID`
  > default value: `1`
  >> Ajoute un enregistreur par défaut à un enregistrement non identifiable<br>
  >> (mauvais chemin dans le dépôt FTP).<br>
* `DEFAULT_RECORDER_PATH`
  > default value: `/data/ftp-pod/ftp/`
  >> Chemin racine du répertoire où sont déposés les enregistrements<br>
  >> (chemin du serveur FTP).<br>
* `DEFAULT_RECORDER_TYPE_ID`
  > default value: `1`
  >> Identifiant du type de vidéo par défaut (si non spécifié).<br>
  >> (Exemple : 3 pour Colloque/conférence, 4 pour Cours…)<br>
* `DEFAULT_RECORDER_USER_ID`
  > default value: `1`
  >> Identifiant du propriétaire par défaut (si non spécifié) des enregistrements déposés.<br>
* `OPENCAST_DEFAULT_PRESENTER`
  > default value: `mid`
  >> Permet de spécifier la valeur par défaut du placement de la vidéo du<br>
  >> presenteur par rapport à la vidéo de présentation (écran)<br>
  >> les valeurs possibles sont :<br>
  >> * "mid" (écran et caméra ont la même taille)<br>
  >> * "piph" (le presenteur est incrusté dans la vidéo en haut à droite)<br>
  >> * "pipb" (le presenteur est incrusté dans la vidéo en bas à droite)<br>
  >> Contenu par défaut du fichier xml pour créer le mediapackage pour le studio.<br>
  >> Ce fichier va contenir toutes les spécificités de l’enregistrement<br>
  >> (source, cutting, title, presenter etc.)<br>
* `OPENCAST_FILES_DIR`
  > default value: `opencast-files`
  >> Permet de spécifier le dossier de stockage des enregistrements du studio avant traitement.<br>
* `OPENCAST_MEDIAPACKAGE`
  > default value: `-> see xml content`
  >> Contenu par défaut du fichier xml pour créer le mediapackage pour le studio.<br>
  >> Ce fichier va contenir toutes les spécificités de l’enregistrement<br>
  >> (source, cutting, title, presenter etc.)<br>
  >>
  >> ```python
  >> OPENCAST_MEDIAPACKAGE = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
  >>     <mediapackage xmlns="http://mediapackage.opencastproject.org" id="" start="">
  >>     <media/>
  >>     <metadata/>
  >>     <attachments/>
  >>     <publications/>
  >>     </mediapackage>"""
  >> ```
  >>
* `PUBLIC_RECORD_DIR`
  > default value: `records`
  >> Chemin d’accès web (public) au répertoire de dépot des enregistrements (`DEFAULT_RECORDER_PATH`).<br>
  >> Attention : penser à modifier la conf de NGINX.<br>
* `RECORDER_ADDITIONAL_FIELDS`
  > default value: `()`
  >> Liste des champs supplémentaires pour le formulaire des enregistreurs.<br>
  >> Cette liste reprend le nom des champs correspondants aux paramètres d’édition d’une vidéo<br>
  >> (Discipline, Chaine, Theme, mots clés...).<br>
  >> L’exemple suivant comporte l’ensemble des champs possibles,<br>
  >> mais peut être allégée en fonction des besoins.<br>
  >> Les vidéos seront alors générées avec les valeurs des champs supplémentaires<br>
  >> telles que définies dans leur enregistreur.<br>
* `RECORDER_ALLOW_INSECURE_REQUESTS`
  > default value: `False`
  >> Autorise la requête sur l’application en elle-même sans vérifier le certificat SSL<br>
* `RECORDER_BASE_URL`
  > default value: `https://pod.univ.fr`
  >> url racine de l’instance permettant l’envoi de notification lors de la réception d’enregistrement.<br>
* `RECORDER_SELF_REQUESTS_PROXIES`
  > default value: `{"http": None, "https": None}`
  >> Précise les proxy à utiliser pour une requête vers l’application elle même<br>
  >> dans le cadre d’enregistrement par défaut force la non utilisation de proxy.<br>
* `RECORDER_SKIP_FIRST_IMAGE`
  > default value: `False`
  >> Si True, permet de ne pas prendre en compte la 1ère image lors du traitement<br>
  >> d’un fichier d’enregistrement de type AudioVideoCast.<br>
* `RECORDER_TYPE`
  > default value: `(('video', _('Video')), ('audiovideocast', _('Audiovideocast')), ('studio', _('Studio')))`
  >> Type d’enregistrement géré par la plateforme.<br>
  >> Un enregistreur ne peut déposer que des fichiers de type proposé par la plateforme.<br>
  >> Le traitement se fait en fonction du type de fichier déposé.<br>
* `USE_OPENCAST_STUDIO`
  > default value: `False`
  >> Activer l’utilisation du studio Opencast.<br>
* `USE_RECORD_PREVIEW`
  > default value: `False`
  >> Si True, affiche l’icone de prévisualisation des vidéos dans la page "Revendiquer un enregistrement".<br>

### Configuration de l’application Intervenant

Application Intervenant permettant d'ajouter des intervenants à la vidéo.<br>
Mettre `USE_SPEAKER` à True pour activer cette application.<br>

* `REQUIRED_SPEAKER_FIRSTNAME`
  > default value: `True`
  >> Prénom obligatoire dans le formulaire d'ajout intervenant<br>
* `USE_SPEAKER`
  > default value: `False`
  >> Activation de l’application Intervenant<br>

### Configuration de l’application vidéo

* `ACTIVE_VIDEO_COMMENT`
  > default value: `False`
  >> Activer les commentaires au niveau de la plateforme<br>
* `CACHE_VIDEO_DEFAULT_TIMEOUT`
  > default value: `600`
  >>
  >> Temps en seconde de conservation des données de l’application video<br>
* `CHANNEL_FORM_FIELDS_HELP_TEXT`
  > default value: ``
  >> Ensemble des textes d’aide affichés avec le formulaire d’édition de chaine.<br>
  >> voir pod/video/forms.py<br>
* `CHUNK_SIZE`
  > default value: `1000000`
  >> Taille d’un fragment lors de l’envoi d’une vidéo<br>
  >> le fichier sera mis en ligne par fragment de cette taille.<br>
* `CURSUS_CODES`
  > default value: `()`
  >> Liste des cursus proposés lors de l’ajout des vidéos.<br>
  >> Affichés en dessous d’une vidéos, ils sont aussi utilisés pour affiner la recherche.<br>
  >>
  >> ```python
  >> CURSUS_CODES = (
  >>     ('0', _("None / All")),
  >>     ('L', _("Bachelor’s Degree")),
  >>     ('M', _("Master’s Degree")),
  >>     ('D', _("Doctorate")),
  >>     ('1', _("Other"))
  >> )
  >> ```
  >>
* `DEFAULT_DC_COVERAGE`
  > default value: `TITLE_ETB + " - Town - Country"`
  >> couverture du droit pour chaque vidéo<br>
* `DEFAULT_DC_RIGHTS`
  > default value: `BY-NC-SA`
  >> droit par défaut affichés dans le flux RSS si non renseigné<br>
* `DEFAULT_THUMBNAIL`
  > default value: `img/default.svg`
  >> Image par défaut affichée comme poster ou vignette, utilisée pour présenter la vidéo.<br>
  >> Cette image doit se situer dans le répertoire static.<br>
* `DEFAULT_TYPE_ID`
  > default value: `1`
  >> Les vidéos créées sans type (par importation par exemple)<br>
  >> seront affectées au type par défaut<br>
  >> (en général, le type ayant pour identifiant '1' est 'Other')<br>
* `DEFAULT_YEAR_DATE_DELETE`
  > default value: `2`
  >> Durée d’obsolescence par défaut (en années après la date d’ajout).<br>
* `FORCE_LOWERCASE_TAGS`
  > default value: `True`
  >> Les mots clés saisis lors de l’ajout de vidéo sont convertis automatiquement en minuscule.<br>
* `LANG_CHOICES`
  > default value: ``
  >> Liste des langues proposées lors de l’ajout des vidéos.<br>
  >> Affichés en dessous d’une vidéos, les choix sont aussi utilisés pour affiner la recherche.<br>
* `LICENCE_CHOICES`
  > default value: `()`
  >> Licence proposées pour les vidéos en creative commons :<br>
  >>
  >> ```python
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
  >> ```
  >>
* `MAX_DURATION_DATE_DELETE`
  > default value: `10`
  >> Fixe une durée maximale que la date de suppression d’une vidéo ne peut dépasser.<br>
  >> Par défaut : 10 (Année courante + 10 ans).<br>
* `MAX_TAG_LENGTH`
  > default value: `50`
  >> Les mots-clés saisis lors de l’ajout de vidéo ne peuvent dépasser cette longueur.<br>
* `NOTES_STATUS`
  > default value: `()`
  >> Valeurs possible pour l’accès à une note.<br>
  >>
  >> ```python
  >> NOTES_STATUS = (
  >>     ("0", _("Private (me only)")),
  >>     ("1", _("Shared with video owner")),
  >>     ("2", _("Public")),
  >> )
  >> ```
  >>
* `NUMBER_TAGS_CLOUD`
  > default value: `20`
  >> Nombre de mots-clés les plus importants affichés dans le nuage de la page d'accueil.<br>
  >> Les paramètres TAGULOUS_WEIGHT_MIN et TAGULOUS_WEIGHT_MAX ne sont pas utilisés.<br>
* `OEMBED`
  > default value: `False`
  >> Permettre l’usage du oembed, partage dans Moodle, Facebook, Twitter etc.<br>
* `ORGANIZE_BY_THEME`
  > default value: `False`
  >> Affichage uniquement des vidéos de la chaîne ou du thème actuel(le).<br>
  >> Affichage des sous-thèmes directs de la chaîne ou du thème actuel(le)<br>
* `RESTRICT_EDIT_VIDEO_ACCESS_TO_STAFF_ONLY`
  > default value: `False`
  >> Si True, seule les personnes "Staff" peuvent déposer des vidéos<br>
* `THEME_FORM_FIELDS_HELP_TEXT`
  > default value: `""`
  >> Ensemble des textes d’aide affichés avec le formulaire d’édition de theme.<br>
  >> voir pod/video/forms.py<br>
  >>
  >> ```python
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
  >> ```
  >>
* `USER_VIDEO_CATEGORY`
  > default value: `False`
  >> Permet d’activer le fonctionnement de categorie au niveau de ses vidéos.<br>
  >> Vous pouvez créer des catégories pour pouvoir ranger vos propres vidéos.<br>
  >> Les catégories sont liées à l’utilisateur.<br>
* `USE_OBSOLESCENCE`
  > default value: `False`
  >> Activation de l’obsolescence des video.<br>
  >> Permet d’afficher la date de suppression de la video<br>
  >> dans le formulaire d’edition et dans la partie admin.<br>
* `USE_STATS_VIEW`
  > default value: `False`
  >> Permet d’activer la possibilité de voir en details le nombre de visualisation<br>
  >> d’une vidéo durant un jour donné ou mois,<br>
  >> année ou encore le nombre de vue total depuis la création de la vidéo.<br>
  >> Un lien est rajouté dans la partie info lors de la lecture d’une vidéo,<br>
  >> un lien est rajouté dans la page de visualisation d’une chaîne ou un theme<br>
  >> ou encore toutes les vidéos présentes sur la plateforme.<br>
* `USE_VIDEO_EVENT_TRACKING`
  > default value: `False`
  >> Ce paramètre permet d’activer l’envoi d’évènements sur le lecteur vidéo à Matomo.<br>
  >> N’est utile que si le code piwik / matomo est présent dans l’instance de Esup-Pod.<br>
  >> Les évènements envoyés sont :<br>
  >> play, pause, seeked, ended, ratechange, fullscreen, error, loadmetadata<br>
  >> Pour rajouter le code Piwik/Matomo dans votre instance de Pod,<br>
  >> il suffit de créer un fichier `pod/custom/templates/custom/tracking.html`<br>
  >> Il faut ensuite y insérer le code javascript puis dans votre fichier `settings_local.py`,<br>
  >> de préciser dans la variable `TEMPLATE_VISIBLE_SETTINGS`:<br>
  >> `'TRACKING_TEMPLATE': 'custom/tracking.html'`<br>
* `USE_XAPI_VIDEO`
  > default value: `False`
  >>
  >> Active l‘envoi d’instructions xAPI pour le lecteur vidéo.<br>
  >> Attention, il faut mettre USE_XAPI à True pour que les instructions soient envoyées.<br>
* `VIDEO_ALLOWED_EXTENSIONS`
  > default value: `()`
  >> Extensions autorisées pour le téléversement vidéo sur la plateforme (en minuscules).<br>
  >>
  >> ```python
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
  >> ```
  >>
* `VIDEO_FEED_NB_ITEMS`
  > default value: `100`
  >>
  >> nombre d’item renvoyé par le flux rss<br>
* `VIDEO_FORM_FIELDS`
  > default value: `__all__`
  >> Liste des champs du formulaire d’édition de vidéos affichées.<br>
* `VIDEO_FORM_FIELDS_HELP_TEXT`
  > default value: ``
  >> Ensemble des textes d’aide affichés avec le formulaire d’envoi de vidéo.<br>
  >>
  >> ```python
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
  >>                     "you except that they can’t delete this media."
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
  >>                     "If you don’t select “Draft mode”, you can restrict "
  >>                     "the content access to only people who can log in"
  >>                 )
  >>             ],
  >>         ),
  >>         (
  >>             "{0}".format(_("Password")),
  >>             [
  >>                 _(
  >>                     "If you don’t select “Draft mode”, you can add a password "
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
  >> ```
  >>
* `VIDEO_MAX_UPLOAD_SIZE`
  > default value: `1`
  >> Taille maximum en Go des fichiers téléversés sur la plateforme.<br>
* `VIDEO_PLAYBACKRATES`
  > default value: `[0.5, 1, 1.5, 2]`
  >> Configuration des choix de vitesse de lecture pour le lecteur vidéo.<br>
* `VIDEO_RECENT_VIEWCOUNT`
  > default value: `180`
  >> Durée (en nombre de jours) sur laquelle on souhaite compter le nombre de vues récentes.<br>
* `VIDEO_REQUIRED_FIELDS`
  > default value: `[]`
  >> Permet d’ajouter l’attribut obligatoire dans<br>
  >> le formulaire d’edition et d’ajout d’une video :<br>
  >> Exemple de valeur : `["discipline", "tags"]`<br>
  >> NB : les champs cachés et suivant ne sont pas pris en compte :<br>
  >> `(video, title, type, owner, date_added, cursus, main_lang)`<br>
* `VIEW_STATS_AUTH`
  > default value: `False`
  >> Réserve l’accès aux statistiques des vidéos aux personnes authentifiées.<br>

### Configuration de l’application encodage et transcription de vidéo

Application pour l’encodage et la transcription de vidéo.<br>
Il est possible d’encoder en local ou en distant.<br>
Attention, il faut configurer Celery pour l’envoi des instructions pour l’encodage distant.<br>

* `CAPTIONS_STRICT_ACCESSIBILITY`
  > default value: `False`
  >> Si True, les sous-titres seront générés en respectant strictement les normes<br>
  >> d’accessibilité. L'apparition d'un message d’avertissement sera affiché si les<br>
  >> sous-titres ne respectent pas ces normes, même si la valeur est à False.<br>
* `CELERY_BROKER_URL`
  > default value: `redis://redis.localhost:6379/5`
  >> URL du courtier de messages où Celery stocke les ordres d’encodage et de transcription.<br>
* `CELERY_TO_ENCODE`
  > default value: `False`
  >> Utilisation de Celery pour la gestion des taches d’encodage<br>
* `DEFAULT_LANG_TRACK`
  > default value: `fr`
  >> langue par défaut pour l’ajout de piste à une vidéo.<br>
* `EMAIL_ON_ENCODING_COMPLETION`
  > default value: `True`
  >> Si True, un courriel est envoyé aux managers<br>
  >> et à l’auteur (si DEBUG est à False) à la fin de l’encodage.<br>
* `EMAIL_ON_TRANSCRIPTING_COMPLETION`
  > default value: `True`
  >> Si True, un courriel est envoyé aux managers<br>
  >> et à l’auteur (si DEBUG est à False) à la fin de la transcription.<br>
* `ENCODE_STUDIO`
  > default value: `start_encode_studio`
  >> Fonction appelée pour lancer l’encodage du studio (merge and cut).<br>
* `ENCODE_VIDEO`
  > default value: `start_encode`
  >> Fonction appelée pour lancer l’encodage des vidéos direct par thread ou distant par celery<br>
* `ENCODING_CHOICES`
  > default value: `()`
  >> Encodage possible sur la plateforme. Associé à un rendu dans le cas d’une vidéo.<br>
  >>
  >> ```python
  >> ENCODING_CHOICES = (
  >>     ("audio", "audio"),
  >>     ("360p", "360p"),
  >>     ("480p", "480p"),
  >>     ("720p", "720p"),
  >>     ("1080p", "1080p"),
  >>     ("playlist", "playlist")
  >> )
  >> ```
  >>
* `ENCODING_TRANSCODING_CELERY_BROKER_URL`
  > default value: `False`
  >>
  >> Il faut renseigner l’url du redis sur lequel Celery<br>
  >> va chercher les ordres d’encodage et de transcription<br>
  >> par exemple : "redis://redis.localhost:6379/7"<br>
* `FORMAT_CHOICES`
  > default value: `()`
  >> Format d’encodage réalisé sur la plateforme.<br>
  >>
  >> ```python
  >> FORMAT_CHOICES = (
  >>     ("video/mp4", "video/mp4"),
  >>     ("video/mp2t", "video/mp2t"),
  >>     ("video/webm", "video/webm"),
  >>     ("audio/mp3", "audio/mp3"),
  >>     ("audio/wav", "audio/wav"),
  >>     ("application/x-mpegURL", "application/x-mpegURL"),
  >> )
  >> ```
  >>
* `POD_API_TOKEN`
  > default value: ``
  >> Token d’authentification utilisé pour l’appel<br>
  >> en fin d’encodage distant ou de transcription à distance.<br>
  >> Pour le créer, il faut aller dans la partie Admin > Jeton d’authentification > token.<br>
* `POD_API_URL`
  > default value: ``
  >> Adresse de l’API rest à appeler en fin d’encodage<br>
  >> distant ou de transcription à distance.<br>
  >> Exemple : `https://pod.univ.fr/rest/`<br>
* `USE_REMOTE_ENCODING_TRANSCODING`
  > default value: `False`
  >>
  >> Si True, active l’encodage et la transcription sur un environnement distant via redis+celery<br>
* `VIDEO_RENDITIONS`
  > default value: `[]`
  >> Rendu serializé pour l’encodage des videos.<br>
  >> Cela permet de pouvoir encoder les vidéos sans l’environnement de Pod.<br>
  >>
  >> ```python
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
  >> ```
  >>

### Configuration de l’application search

* `ES_INDEX`
  > default value: `pod`
  >> Valeur pour l’index de ElasticSearch<br>
* `ES_MAX_RETRIES`
  > default value: `10`
  >> Valeur max de tentatives pour ElasticSearch.<br>
* `ES_OPTIONS`
  > default value: `{}`
  >> Options d’ElasticSearch, notamment utilisées pour ES8 en SSL et avec un user en paramètre<br>
  >> Voir [www.elastic.co](https://www.elastic.co/guide/en/elasticsearch/client/python-api/current/config.html)<br>
  >> pour plus d’informations.<br>
* `ES_TIMEOUT`
  > default value: `30`
  >> Valeur de timeout pour ElasticSearch.<br>
* `ES_URL`
  > default value: `["http://elasticsearch.localhost:9200/"]`
  >> Adresse du ou des instances d’Elasticsearch utilisées pour<br>
  >> l’indexation et la recherche de vidéo.<br>
* `ES_VERSION`
  > default value: `8`
  >> Version d’ElasticSearch.<br>
  >> valeurs possibles : `8`, correspondant à la version du serveur Elasticsearch utilisé.<br>
  >> Attention, le paquet elasticsearch-py doit correspondre à la version du serveur.<br>
  >> pour la 8, `pip3 install elasticsearch==8.17.2`.<br>
  >> Voir [elasticsearch-py.readthedocs.io](https://elasticsearch-py.readthedocs.io/)<br>
  >> pour plus d’information.<br>

### Configuration de l’application xapi

Application pour l’envoi d‘instructions xAPI à un LRS.<br>
Aucune instruction ne persiste dans Pod, elles sont toutes envoyées au LRS paramétré.<br>
Attention, il faut configurer Celery pour l’envoi des instructions.<br>

* `USE_XAPI`
  > default value: `False`
  >>
  >> Activation de l’application xAPI<br>
* `XAPI_ANONYMIZE_ACTOR`
  > default value: `True`
  >>
  >> Si False, le nom de l’utilisateur sera stocké en clair dans les statements xAPI,<br>
  >> si True, son nom d’utilisateur sera anonymisé<br>
* `XAPI_LRS_LOGIN`
  > default value: ``
  >>
  >> identifiant de connexion du LRS pour l’envoi des statements<br>
* `XAPI_LRS_PWD`
  > default value: ``
  >>
  >> mot de passe de connexion du LRS pour l’envoi des statements<br>
* `XAPI_LRS_URL`
  > default value: ``
  >>
  >> URL de destination pour l’envoi des statements. I.E. : `https://ralph.univ.fr/xAPI/statements`<br>
