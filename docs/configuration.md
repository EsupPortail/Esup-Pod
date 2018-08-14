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
| **`FORCE_LOWERCASE_TAGS`**           | Les mots clés saisis lors de l'ajout de vidéo sont convertis automatiquement en minuscule | True |
| **`MAX_TAG_LENGTH`**           | Les mots clés saisis lors de l'ajout de vidéo ne peuvent dépassé la longueur saisie | 50 |
| **`USE_PODFILE`**           | Utiliser l'application de gestion de fichier fourni avec le projet. Si False, chaque fichier envoyé ne pourra être utilisé qu'une seule fois. | False |
| **`THIRD_PARTY_APPS`**           | Liste des applications tierces accessibles. |[] |
| **`FILE_DIR`**           | Nom du répertoire racine ou les fichiers "complémentaires" (hors videos etc.) sont téléversés. | files |

