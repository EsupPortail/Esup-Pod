
## Configuration des applications Esup_Pod

### Configuration de l’authentification

Configuration de l’application authentification<br>

* `AFFILIATION_STAFF`
  > default value: `['faculty', 'employee', 'staff']`
  >> Les personnes ayant pour affiliation ces valeurs ont automatiquement le statut staff à True.<br>
* `ALLOWED_SUPERUSER_IPS`
  > default value: `['127.0.0.1', '10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16']`
  >> Liste d’IP et/ou de plages depuis lesquelles le statut 'superuser' est autorisé.<br>
* `CAS_ADMIN_REDIRECT`
  > default value: `False`
  >> Rediriger vers la connexion CAS pour l'interface d'administration.<br>
* `CAS_APPLY_ATTRIBUTES_TO_USER`
  > default value: `True`
  >> Appliquer automatiquement les attributs renvoyés par le CAS au profil de l'utilisateur.<br>
* `CAS_FORCE_CHANGE_USERNAME_CASE`
  > default value: `lower`
  >> Forcer la casse (minuscules ou majuscules) du nom d’utilisateur CAS.<br>
* `CAS_SERVER_URL`
  > default value: `https://cas.univ-lille.fr`
  >> Url du serveur CAS de l’établissement.<br>
* `CAS_VERSION`
  > default value: `3`
  >> Version du protocole CAS utilisée.<br>
* `CREATE_GROUP_FROM_AFFILIATION`
  > default value: `True`
  >> Si True, des groupes d’accès sont créés automatiquement à partir des affiliations.<br>
* `CREATE_GROUP_FROM_GROUPS`
  > default value: `True`
  >> Si True, des groupes sont créés automatiquement à partir des groupes distants (memberOf).<br>
* `HIDE_USERNAME`
  > default value: `False`
  >> Si valeur vaut `True`, le username de l’utilisateur ne sera pas visible sur la plate-forme Pod (RGPD).<br>
* `LDAP_BIND_DN`
  > default value: `cn=pod,ou=app,dc=univ,dc=fr`
  >> Identifiant (DN) du compte pour se connecter au serveur LDAP.<br>
* `LDAP_BIND_PASSWORD`
  > default value: ``
  >> Mot de passe du compte pour se connecter au serveur LDAP.<br>
* `LDAP_MAPPING_ATTRIBUTES`
  > default value: `{'uid': 'uid', 'mail': 'mail', 'last_name': 'sn', 'first_name': 'givenname', 'primaryAffiliation': 'eduPersonPrimaryAffiliation', 'affiliations': 'eduPersonAffiliation', 'groups': 'memberOf', 'establishment': 'establishment'}`
  >> Liste de correspondance entre les champs d’un compte de Pod et les champs renvoyés par le LDAP.<br>
* `LDAP_SERVER_PORT`
  > default value: `389`
  >> Port du serveur LDAP.<br>
* `LDAP_SERVER_URL`
  > default value: `ldap://ldap.univ.fr`
  >> URL du serveur LDAP.<br>
* `LDAP_SERVER_USE_SSL`
  > default value: `False`
  >> Utiliser SSL pour la connexion LDAP.<br>
* `LDAP_USER_SEARCH_BASE`
  > default value: `ou=people,dc=univ,dc=fr`
  >> Base de recherche LDAP pour les utilisateurs.<br>
* `LDAP_USER_SEARCH_FILTER`
  > default value: `(uid=%(uid)s)`
  >> Filtre LDAP permettant la recherche de l’individu dans le serveur LDAP.<br>
* `OIDC_CLAIM_FAMILY_NAME`
  > default value: `family_name`
  >> Nom du Claim pour récupérer le nom de famille.<br>
* `OIDC_CLAIM_GIVEN_NAME`
  > default value: `given_name`
  >> Nom du Claim pour récupérer le prénom.<br>
* `OIDC_CLAIM_PREFERRED_USERNAME`
  > default value: `preferred_username`
  >> Nom du Claim pour récupérer l’identifiant (login).<br>
* `OIDC_DEFAULT_ACCESS_GROUP_CODE_NAMES`
  > default value: `[]`
  >> Groupes d’accès attribués par défaut à un nouvel utilisateur OIDC.<br>
* `OIDC_DEFAULT_AFFILIATION`
  > default value: `member`
  >> Affiliation par défaut d’un utilisateur authentifié par OIDC.<br>
* `OIDC_OP_TOKEN_ENDPOINT`
  > default value: `https://auth.example.com/oidc/token`
  >> Endpoint de récupération du jeton (Token) OIDC.<br>
* `OIDC_OP_USER_ENDPOINT`
  > default value: `https://auth.example.com/oidc/userinfo`
  >> Endpoint d'informations utilisateur du fournisseur OIDC.<br>
* `OIDC_RP_CLIENT_ID`
  > default value: `mon-client-id`
  >> Identifiant client (Client ID) OIDC.<br>
* `OIDC_RP_CLIENT_SECRET`
  > default value: `mon-secret`
  >> Secret client (Client Secret) OIDC.<br>
* `REMOTE_USER_HEADER`
  > default value: `REMOTE_USER`
  >> Nom de l’attribut dans les headers qui sert à identifier l’utilisateur Shibboleth.<br>
* `SHIBBOLETH_ATTRIBUTE_MAP`
  > default value: `{'REMOTE_USER': [True, 'username'], 'Shibboleth-givenName': [True, 'first_name'], 'Shibboleth-sn': [False, 'last_name'], 'Shibboleth-mail': [False, 'email'], 'Shibboleth-primary-affiliation': [False, 'affiliation'], 'Shibboleth-unscoped-affiliation': [False, 'affiliations']}`
  >> Mapping des attributs entre Shibboleth et la classe utilisateur.<br>
* `SHIBBOLETH_STAFF_ALLOWED_DOMAINS`
  > default value: `[]`
  >> Permettre à l’utilisateur d’un domaine d’être membre du personnel (Shibboleth).<br>
* `SHIB_SECURE_HEADER`
  > default value: `None`
  >> En-tête sécurisé pour Shibboleth.<br>
* `SHIB_SECURE_VALUE`
  > default value: `secure`
  >> Valeur attendue pour l'en-tête sécurisé Shibboleth.<br>
* `USE_CAS`
  > default value: `False`
  >> Activation de l’authentification CAS en plus de l’authentification locale.<br>
* `USE_ESTABLISHMENT_FIELD`
  > default value: `False`
  >> Si valeur vaut 'True', rajoute un attribut 'establishment' à l’utilisateur Pod.<br>
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

### Configuration Vidéo

Configuration de l’application vidéo<br>

* `ALLOWED_EXTENSIONS`
  > default value: `['3gp', 'avi', 'divx', 'flv', 'm2p', 'm4v', 'mkv', 'mov', 'mp4', 'mpeg', 'mpg', 'mts', 'wmv', 'mp3', 'ogg', 'wav', 'wma', 'webm', 'ts']`
  >> Extensions de fichiers autorisées pour le téléversement.<br>
* `ALLOW_AUTHENTICATED_UPLOAD`
  > default value: `True`
  >> Autoriser tous les utilisateurs authentifiés à téléverser des vidéos.<br>
* `CACHE_TIMEOUT`
  > default value: `600`
  >> Temps en secondes de conservation des données en cache.<br>
* `CHANNEL_MODE`
  > default value: `False`
  >> Activer le mode d'affichage par chaînes.<br>
* `CHUNK_SIZE`
  > default value: `100000`
  >> Taille d’un fragment lors de l’envoi d’une vidéo.<br>
* `DEFAULT_LICENSE`
  > default value: ``
  >> Licence par défaut appliquée aux nouvelles vidéos.<br>
* `FFMPEG_CMD`
  > default value: `ffmpeg`
  >> Commande système pour FFmpeg.<br>
* `FFMPEG_CRF`
  > default value: `20`
  >> Valeur CRF pour l'encodage FFmpeg (Qualité).<br>
* `FFMPEG_NB_THREADS`
  > default value: `slow`
  >> Preset de vitesse/qualité FFmpeg.<br>
* `FFPROBE_CMD`
  > default value: `ffprobe`
  >> Commande système pour FFprobe.<br>
* `FFPROBE_GET_INFO`
  > default value: `high`
  >> Niveau de détail pour l'extraction des métadonnées.<br>
* `FORCE_LOWERCASE_TAGS`
  > default value: `True`
  >> Les mots clés sont convertis automatiquement en minuscule.<br>
* `HIDE_CURSUS`
  > default value: `False`
  >> Si True, masque les cursus dans la colonne de droite.<br>
* `HIDE_DISCIPLINES`
  > default value: `False`
  >> Si True, masque les disciplines dans la colonne de droite.<br>
* `HIDE_SHARE`
  > default value: `False`
  >> Si True, masque les liens de partage sur les réseaux sociaux.<br>
* `HIDE_TAGS`
  > default value: `False`
  >> Si True, permet de ne pas afficher le nuage de mots clés.<br>
* `HIDE_TYPES`
  > default value: `False`
  >> Si True, masque les types de vidéos dans la colonne de droite.<br>
* `HIDE_USER_FILTER`
  > default value: `False`
  >> Si True, le filtre des vidéos par utilisateur ne sera plus visible (RGPD).<br>
* `HOMEPAGE_SHOWS_PASSWORDED`
  > default value: `False`
  >> Afficher les vidéos protégées par mot de passe sur la page d’accueil.<br>
* `MAX_TAG_LENGTH`
  > default value: `50`
  >> Longueur maximale autorisée pour un mot-clé.<br>
* `MAX_UPLOAD_SIZE_GB`
  > default value: `1`
  >> Taille maximum en Go des fichiers téléversés sur la plateforme.<br>
* `NUMBER_TAGS_CLOUD`
  > default value: `20`
  >> Nombre de mots-clés affichés dans le nuage.<br>
* `RESTRICT_EDIT_TO_STAFF`
  > default value: `False`
  >> Si True, seule les personnes 'Staff' peuvent déposer des vidéos.<br>
* `THUMBNAILS_DIR`
  > default value: `thumbnails`
  >> Répertoire pour le stockage des vignettes (thumbnails).<br>
* `USER_QUOTA_SIZE_GB`
  > default value: `5`
  >> Quota de stockage par utilisateur en Go.<br>
* `USER_VIDEO_CATEGORY`
  > default value: `False`
  >> Permet d’activer la gestion de catégories par les utilisateurs.<br>
* `USE_CUT`
  > default value: `False`
  >> Activation de l’application de découpage (Cut).<br>
* `USE_DUPLICATE`
  > default value: `False`
  >> Permet aux utilisateurs de dupliquer une vidéo.<br>
* `USE_STATS_VIEW`
  > default value: `False`
  >> Permet d’activer la visualisation détaillée des statistiques de vue.<br>
* `VIDEOS_DIR`
  > default value: `videos`
  >> Répertoire racine pour le stockage des vidéos.<br>
* `VIDEO_REQUIRED_FIELDS`
  > default value: `[]`
  >> Permet de définir les champs obligatoires dans le formulaire d’édition d’une vidéo.<br>
* `VIEW_STATS_AUTH`
  > default value: `False`
  >> Réserve l’accès aux statistiques aux personnes authentifiées.<br>
* `WEBTV_MODE`
  > default value: `False`
  >> Mode webtv : bascule POD en application webtv (masque les boutons de connexion).<br>

### Configuration API

Réglages de la documentation de l'API.<br>

* `SPECTACULAR_SETTINGS`
  > default value: `{'TITLE': 'Pod REST API', 'DESCRIPTION': 'Video management API (Local Authentication)', 'SERVE_INCLUDE_SCHEMA': False, 'COMPONENT_SPLIT_REQUEST': True}`
  >> Configuration pour la génération du schéma OpenAPI.<br>

### Configuration Core

Configuration de l’application Core<br>

* `MEDIA_ROOT`
  > default value: `media`
  >> Chemin absolu du système de fichiers vers le répertoire qui contiendra les fichiers téléchargés par les utilisateurs.<br>
* `MEDIA_URL`
  > default value: `/media/`
  >> URL qui gère les médias servis depuis MEDIA_ROOT.<br>
* `STATIC_ROOT`
  > default value: `staticfiles`
  >> Le chemin absolu vers le répertoire où collectstatic rassemblera les fichiers statiques pour le déploiement.<br>
* `STATIC_URL`
  > default value: `/static/`
  >> URL à utiliser pour faire référence aux fichiers statiques situés dans STATIC_ROOT.<br>
