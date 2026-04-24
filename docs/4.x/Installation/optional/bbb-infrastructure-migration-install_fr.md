---
layout: default
version: 4.x
lang: fr
---

# Migration d’infrastructure BigBlueButton, avec l’appui de Pod

## Contexte

Dans le cadre du plan de relance, une solution de classe virtuelle du ministère de l’Enseignement Supérieur et de la Recherche (ESR), s’appuyant sur le logiciel libre et open source BigBlueButton (BBB), a été déployée à l’échelle nationale.

Plus d’informations peuvent être retrouvées sur les sites suivants :

- [Documentation Numérique ESR](https://doc.numerique-esr.fr/)
- [Classes virtuelles et webinaires pour l’enseignement supérieur](https://www.enseignementsup-recherche.gouv.fr/fr/classes-virtuelles-et-webinaires-pour-l-enseignement-superieur-90257)

Pour les établissements n’ayant jamais eu d’infrastructure locale BigBlueButton, l’utilisation de cette solution de classe virtuelle (BBB ESR) est simple à mettre en œuvre.

Cependant, pour les établissements ayant auparavant une infrastructure locale BBB,
 l’utilisation du BBB de l’ESR présente des impacts pour les usagers.
Cette documentation peut alors être utile pour ces établissements.

### Impacts

Changer d’infrastructure est extrêmement simple, que cela soit pour n’importe quelle plateforme :

- **Pod** : changer le paramétrage du module des Réunions dans le fichier `custom/settings_local.py`, à savoir `BBB_API_URL` et `BBB_SECRET_KEY`.
- **Moodle (v4)** : changer le paramétrage, accessible via le module d’Administration du site, à savoir l’URL du serveur BigBlueButton et le Secret partagé BigBlueButton.
- **Greenlight** : changer le paramétrage dans le fichier `.env`, à savoir `BIGBLUEBUTTON_ENDPOINT` et `BIGBLUEBUTTON_SECRET`.

En modifiant ces paramètres, la plateforme pointe alors sur la nouvelle architecture BBB.

Pour les usagers, les impacts concernent les enregistrements, qui ne seront alors plus visibles.
En effet, les sessions/réunions sont toujours accessibles aux usagers,
 car elles sont sauvegardées dans la plateforme concernée, mais pas les enregistrements.
Ces enregistrements sont sauvegardés directement sur l’infrastructure BBB (soit sur le serveur BBB soit sur le serveur Scalelite).
Dans les plateformes, les liens vers ces enregistrements sont alors affichés au moment de la consultation de la session/réunion.

Au final, lors d’un changement d’infrastructure, les anciens enregistrements ne s’affichent plus aux usagers ;
 et lorsque l’ancienne architecture BBB sera arrêtée,
 les anciens enregistrements ne seront même plus disponibles, si rien n’a été réalisé avant.

### Contraintes

Voici un rappel des contraintes à prendre en compte et qui explique la solution proposée :

- **Contrainte vis-à-vis de Pod** : nous ne souhaitons plus utiliser l’ancien module BBB de Pod, qui est amené à disparaître rapidement.
- **Contrainte de l’API BBB** : les participants et modérateurs ne sont disponibles que lorsque la session BBB est en cours. Une fois arrêtée, l’information n’y est plus dans BBB. Nous n’avons alors ces informations que dans le client BBB, à savoir Pod ou Moodle (ou Greenlight...).
- **Contrainte BBB** : par défaut, il est possible de reconstruire un enregistrement BBB (typiquement pour avoir l’enregistrement au format vidéo) que si les fichiers raw sont encore présents. Par défaut, ces fichiers raw sont supprimés au bout de 14 jours. On ne peut alors baser la solution sur la reconstruction des enregistrements.

### Solution apportée

L’idée est de se baser sur :

- Le système de revendication des enregistrements de Pod (cf. [Documentation ESUP-Portail](https://www.esup-portail.org/wiki/x/DgB8Lw)).
- Le système d’import des vidéos externes pour y ajouter la possibilité de convertir des enregistrements BBB, de type présentation, en vidéo (via le plugin `bbb-recorder`, cf. ci-dessous).
- Un script de migration, qui offre plusieurs possibilités.

Cette solution repose totalement sur Pod et n’impacte en rien BigBlueButton. Aucune modification n’est à réaliser côté BigBlueButton.
{: .alert .alert-info}

💡 Si besoin, le script de migration permet également de réaliser une sauvegarde - en local - des enregistrements.
{: .alert .alert-info}

Ce script de migration est configurable et offre plusieurs possibilités :

1. **Pour ceux qui ont peu d’enregistrements à récupérer** :
   - Ce script va convertir les présentations, de l’ancienne architecture BBB, en fichiers vidéo (via le plugin `bbb-recorder`) et positionner ces fichiers dans le répertoire pour la Revendication des enregistrements.
   - Bien sûr, s’il y a déjà des présentations en vidéo, le fichier vidéo sera directement copié.
   - Une fois que toutes les vidéos ont été encodées, l’architecture BBB locale peut être arrêtée. Les usagers devront aller chercher leurs vidéos dans l’onglet Revendication des enregistrements dans Pod.

2. **Pour ceux qui ont beaucoup d’enregistrements à récupérer** :
   - L’idée est de laisser le temps aux usagers de choisir par eux-mêmes les enregistrements qu’ils souhaitent conserver (il n’est pas possible et utile de tout convertir).
   - Pour cela, il faudra laisser l’ancien serveur BBB/Scalelite ouvert au moins pendant quelques mois (juste pour accéder aux enregistrements).
   - Côté script, si besoin, il faudra un accès à la base de données de Moodle pour savoir qui a réalisé quoi.
   - Ainsi, pour chaque enregistrement BBB, le script va créer une ligne dans "Mes vidéos externes", de type BigBlueButton, pour les modérateurs (qui seront créés si besoin dans la base de Pod). Ils pourront alors par eux-mêmes importer ces enregistrements dans Pod.
   - Au cas où, si des enregistrements ne sont pas identifiables, ils seront associés à un administrateur (à paramétrer dans le script).
   - De plus, si l’accès à la base de Moodle le permet, un message d’information sera positionné directement dans Moodle, au niveau des sessions BBB concernées.

![Migration d’infrastructure BigBlueButton](bbb-infrastructure-migration_screens/external_videos.webp)

Le script est prévu pour être paramétrable, avec possibilité de gérer un certain nombre d’enregistrements et de pouvoir le tester avant (utilisation d’un mode dry).

## Architecture de la solution

### Plugin `bbb-recorder`

Pour convertir les playback présentation de BBB, je me suis basé sur le projet GitHub `bbb-recorder` : un plugin, indépendant de BigBlueButton, qui permet de convertir - via un script - une présentation Web BigBlueButton en fichier vidéo.

Si besoin, ce plugin permet également une diffusion en direct (flux RTMP) d’un cours BigBlueButton.

Ce plugin `bbb-recorder` avait déjà été utilisé pour l’ancien système,
 dans Pod v2 (cf. [Documentation ESUP-Portail](https://www.esup-portail.org/wiki/x/AgCBNg))
 et a été utilisé à de nombreuses reprises avec succès.

> ⚠️ A compter de Juillet 2025, il semble y avoir une incompatibilité entre bbb-recorder et les dernières versions de google-chrome-stable :
pour convertir des vidéos issues d’une instance BBB 2.2, il a fallu downgrader `google-chrome-stable` de la version 139 à 128, pour arriver à télécharger les enregistrements.

#### Fonctionnement de `bbb-recorder`

Le fait d’exécuter le script `bbb-recorder` réalise les étapes suivantes :

1. Lance un navigateur Chrome en arrière-plan.
2. Chrome visite le lien - correspondant à la présentation Web BigBlueButton - fourni.
3. Il effectue l’enregistrement d’écran sous la forme d’un fichier vidéo.

#### Installation de `bbb-recorder` sur les serveurs d’encodage

La documentation de référence est accessible [ici](https://github.com/jibon57/bbb-recorder).

Pour ma part, sur les serveurs Debian 11, voici ce qui a été réalisé.

##### Installation de Chrome et des pré-requis

```sh
sudo -i
apt install xvfb
curl -sS -o - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list
apt-get -y update
apt-get -y install google-chrome-stable
```

(info) Étant un serveur d’encodage, je considère que `ffmpeg` est déjà installé. Si besoin, il est nécessaire d’installer `ffmpeg`.

##### Installation effective

Voici l’installation pour un utilisateur `pod`.

```sh
cd ~
git clone https://github.com/jibon57/bbb-recorder
cd bbb-recorder
npm install --ignore-scripts
cp .env.example .env
```

Gestion du répertoire contenant les vidéos :
 dans mon cas `/data/www/pod/bbb-recorder` et du répertoire de logs `/data/www/pod/bbb-recorder/logs`.

```sh
mkdir /data/www/pod/bbb-recorder
mkdir /data/www/pod/bbb-recorder/logs
```

Si `bbb-recorder` n’a pas été installé avec le bon utilisateur (`pod`),
les fichiers vidéos générés ne seront sûrement pas accessibles par l’utilisateur Pod
et ne pourront alors être encodés par les serveurs d’encodage.

Dans les faits, cela se traduit par un 1° encodage réussi :
 la présentation Web de BBB sera convertie en fichier vidéo,
 mais ce fichier vidéo ne sera pas accessible à Pod et ne pourra être converti en vidéo Pod.

#### Paramétrage de `bbb-recorder`

- Édition du fichier de configuration `~/bbb-recorder/.env` pour paramétrer le RTMP (inutile ici) et surtout le répertoire des vidéos.

```json
{
  "rtmpUrl": "rtmp://xxxxxxxx:xxxxxxxxxx@xxxxx.univ.fr:1935/live/stream",
  "ffmpegServer": "ws://localhost",
  "ffmpegServerPort": 4000,
  "auth": "xxxx",
  "copyToPath": "/data/www/pod/bbb-recorder"
}
```

- Si besoin, réaliser le paramétrage dans le fichier `examples/index.js` (pour réaliser un live ou enregistrer en direct une Web conférence) :

```javascript
const BBBUrl = "https://xxxx.univ.fr/bigbluebutton/";
BBBSalt = "xxxxxxxxxxxxxxxxxxxx";
joinName = "recorder";
```

- Si vous le souhaitez, vous pouvez configurer le bitrate pour contrôler la qualité de la vidéo exportée en ajustant la propriété `videoBitsPerSecond` dans `background.js`.

Il faut bien penser que `bbb-recorder` utilise un répertoire temporaire pour générer une vidéo, avant que celle-ci ne soit copiée dans le répertoire configuré (cf. `copyToPath`). Ce répertoire temporaire correspond à `../Downloads`.

Ainsi, dans le cas d’une installation dans le home directory de l’utilisateur `pod`, le répertoire temporaire créé et utilisé par `bbb-recorder` est `/home/pod/Downloads`.

Il est nécessaire qu’un espace de stockage suffisant soit alors prévu.

### Paramétrage

#### Configuration dans Pod

Une fois `bbb-recorder` installé sur les différents serveurs d’encodage, il reste à configurer le plugin `bbb` directement dans Pod, via l’édition de fichier `custom/settings_local.py` (sur les encodeurs et sur le frontal) :

```py
# Use import-video module
USE_IMPORT_VIDEO = True

# Use plugin bbb-recorder for import-video module
# Useful to convert presentation playback to video file
USE_IMPORT_VIDEO_BBB_RECORDER = True

# Directory of bbb-recorder plugin (see documentation https://github.com/jibon57/bbb-recorder)
# bbb-recorder must be installed in this directory, on all encoding servers
# bbb-recorder create a directory Downloads, at the same level, that needs disk space
IMPORT_VIDEO_BBB_RECORDER_PLUGIN = "/home/pod/bbb-recorder/"

# Directory that will contain the video files generated by bbb-recorder
IMPORT_VIDEO_BBB_RECORDER_PATH = "/data/www/pod/bbb-recorder/"
```

Les éléments de paramétrage sont les suivants :

- `USE_IMPORT_VIDEO` : utilisation (True/False) du module d’import des vidéos pour Pod.
- `USE_IMPORT_VIDEO_BBB_RECORDER` : utilisation (True/False) du plugin `bbb-recorder` pour le module import-vidéo; utile pour convertir une présentation BigBlueButton en fichier vidéo.
- `IMPORT_VIDEO_BBB_RECORDER_PLUGIN` : Répertoire du plugin `bbb-recorder` (voir la documentation [bbb-recorder](https://github.com/jibon57/bbb-recorder)). `bbb-recorder` doit être installé dans ce répertoire, sur tous les serveurs d’encodage. `bbb-recorder` crée un répertoire `Downloads`, au même niveau, qui nécessite de l’espace disque.
- `IMPORT_VIDEO_BBB_RECORDER_PATH` : Répertoire qui contiendra les fichiers vidéo générés par `bbb-recorder`.

Si vous utilisez la 1° option du script, à savoir le système de revendication des enregistrements, il vous est possible de ne pas donner la fonctionnalité de conversion des présentations BBB en fichier vidéo aux usagers. Ainsi, il vous est possible de mettre `USE_IMPORT_VIDEO_BBB_RECORDER = False` dans ce cas de figure.

Les autres paramètres sont nécessaires, à minima, lors de l’exécution du script.

Concernant le répertoire contenant les fichiers vidéos générés par `bbb-recorder` (`IMPORT_VIDEO_BBB_RECORDER_PATH`), il est à créer manuellement - en même temps que son sous-répertoire des logs - avec les lignes de commande suivantes; n’hésitez pas à les modifier à votre convenance selon votre architecture système et vos droits :

```sh
mkdir /data/www/pod/bbb-recorder/logs -p
chown pod:nginx /data/www/pod/bbb-recorder/logs
```

Il est vrai qu’une création automatique de ces répertoires aurait pu être possible,
 mais aux vues des problèmes que cela aurait pu engendrer, en lien avec l’architecture et les droits,
 il m’a paru préférable que l’administrateur de Pod crée ces 2 répertoires à la main.
Il sait ce qu’il fait et pourra ainsi choisir son emplacement, ses droits ou autres.

#### Script `migrate_bbb_recordings`

Ce script est accessible dans Pod, dans le répertoire `pod/video/management/commands/migrate_bbb_recordings`.

Ce script ne peut être exécuté comme cela, il est indispensable de réaliser un paramétrage, indépendant de la configuration de Pod, supplémentaire directement dans ce fichier.

Si vous avez un grand nombre d’enregistrements sur une ancienne version de BBB (testé en 2.2),
 il se peut que vous rencontriez une erreur 404 lors de l’exécution du script,
 lié au timeout de nginx sur le serveur BBB.
Il faudra dans ce cas augmenter sa valeur dans le fichier `/etc/bigbluebutton/nginx/web.nginx` du serveur BBB.

Voir [github.com/bigbluebutton/bigbluebutton/issues/10570](https://github.com/bigbluebutton/bigbluebutton/issues/10570)

##### Fonctionnement du script

Comme évoqué ci-dessus, ce script offre 2 possibilités :

1. **Pour ceux qui ont peu d’enregistrements à récupérer** :
   - Ce script va convertir les présentations, de l’ancienne architecture BBB, en fichiers vidéo (via le plugin `bbb-recorder`) et positionner ces fichiers dans le répertoire d’un enregistreur pour la Revendication des enregistrements (cf. [Documentation ESUP-Portail](https://www.esup-portail.org/wiki/x/DgB8Lw)).
   - Bien sûr, s’il y a déjà des présentations en vidéo, le fichier vidéo sera directement copié.
   - Une fois que toutes les vidéos ont été encodées, l’architecture BBB locale peut être arrêtée. Les usagers devront aller chercher leurs vidéos dans l’onglet Revendication des enregistrements dans Pod.
   - Ceci est possible en utilisant le paramètre `--use-manual-claim` et la configuration directement dans ce fichier.
   - Veuillez noter qu’en fonction de l’architecture de votre Pod, l’encodage sera effectué soit via des tâches Celery, soit directement, l’un après l’autre.
   - N’hésitez pas à tester sur quelques enregistrements et de lancer ce script en arrière-plan (en utilisant `&`).

2. **Pour ceux qui ont beaucoup d’enregistrements à récupérer** :
   - L’idée est de laisser le temps aux usagers de choisir par eux-mêmes les enregistrements qu’ils souhaitent conserver (il n’est pas possible et utile de tout convertir).
   - Pour cela, il faudra laisser l’ancien serveur BBB/Scalelite ouvert au moins pendant quelques mois (juste pour accéder aux enregistrements).
   - Côté script, si besoin, il faudra un accès à la base de données de Moodle pour savoir qui a réalisé quoi.
   - Ainsi, pour chaque enregistrement BBB, le script va créer une ligne dans "Mes vidéos externes", de type BigBlueButton, pour les modérateurs (qui seront créés si besoin dans la base de Pod). Ils pourront alors par eux-mêmes importer ces enregistrements dans Pod. Au cas où, si des enregistrements ne sont pas identifiables (par exemple en provenance d’autres sources que Pod ou Moodle), ils seront associés à un administrateur (à paramétrer dans le script).
   - De plus, si l’accès à la base de Moodle le permet, un message d’information sera positionné directement dans Moodle, au niveau des sessions BBB concernées.
   - Ceci est possible en utilisant le paramètre `--use-import-video`, le paramètre `--use-database-moodle` (optionnel) et la configuration directement dans ce fichier.

3. **Vous pouvez aussi faire uniquement un export au format CSV de la liste des enregistrements BBB** (ce qui vous permet de traiter ensuite ces derniers par ailleurs).
   - Ceci est possible en utilisant le paramètre `--use-export-csv`, le paramètre `--use-database-moodle` (optionnel) et la configuration directement dans ce fichier.

Ce script vous permet également de :

- Simuler ce qui sera fait via le paramètre `--dry`.
- Ne traiter que certaines lignes via les paramètres `--min-value-record-process` et `--max-value-record-process`.

Ce script a été testé avec Moodle 4.

##### Paramétrage interne au script

| Paramètre                 | Description               | Valeur par défaut / Format      |
|---------------------------|---------------------------|---------------------------------|
| `SCRIPT_BBB_SERVER_URL`  | Ancienne URL du serveur BigBlueButton/Scalelite      | `'https://bbb.univ.fr/'`|
| `SCRIPT_BBB_SECRET_KEY`  | Clé BigBlueButton ou Scalelite `LOADBALANCER_SECRET` | `'xxxxxxxxxx'`          |
| `SCRIPT_PLAYBACK_URL_23` | Est-ce que la version de BBB est supérieure à 2.3, vis-à-vis des URLs de playback ? Utile pour lecture de présentations au format 2.0 (<=2.2) ou 2.3 (>=2.3)   | `True` |
| `SCRIPT_RECORDER_ID`     | Enregistreur utilisé pour obtenir les enregistrements BBB (utile avec `--use-manual-claim`)  | `1` |
| `SCRIPT_ADMIN_ID`        | Administrateur auquel les enregistrements seront ajoutés si les modérateurs ne sont pas identifiés (utile avec `--use-import-video`) | `1` |
| `DB_PARAMS`              | Paramètres de connexion à la base Moodle (utile avec `--use-import-video` et `--use-database-moodle`) | Voir détails ci-dessous |
| `SCRIPT_INFORM`          | Message d’information qui sera défini dans Moodle (`mdl_bigbluebuttonbn.intro`)  | *Message prévisionnel pour l’université de Montpellier* |
| `IGNORED_SERVERS`        | Liste de serveurs à ignorer | `["not-a-moodle.univ.fr"]` |
| `USE_CACHE`              | Utilise la dernière réponse BBB stockée dans un fichier XML au lieu de relancer la requête  | `False` |
{: .table .table-striped}

##### Format des `DB_PARAMS`

```json
{
    "default": {
        "host": "bddmoodle.univ.fr",
        "database": "moodle",
        "user": "moodle",
        "password": "",
        "port": null,
        "connect_timeout": 10
    },
    "server2": {
        "host": "bddmoodle.univ.fr",
        "database": "moodle2",
        "user": "moodle2",
        "password": "",
        "port": null,
        "connect_timeout": 10
    }
}
```

##### Arguments du script

| Argument                    | Description                             | Valeur par défaut / Format |
|-----------------------------|-----------------------------------------|----------------------------|
| `--use-manual-claim`        | Utiliser la revendication manuelle             | `False`   |
| `--use-import-video`        | Utiliser le module d’importation vidéo         | `False`   |
| `--use-database-moodle`     | Utiliser la base Moodle pour rechercher les modérateurs (nécessite `--use-import-video` ou `--use-export-csv`) | `False` |
| `--min-value-record-process`| Valeur minimale des enregistrements à traiter  | `1`       |
| `--max-value-record-process`| Valeur maximale des enregistrements à traiter  | `10000`   |
| `--dry`                     | Simuler ce qui sera réalisé                    | `False` |
| `--use-export-csv`          | Exporter les enregistrements au format CSV (avec `--use-database-moodle` pour inclure les modérateurs) | `False` |
{: .table .table-striped}

##### Exemples et cas d’utilisation

⚠️ Avant d’exécuter ce script sans simulation, **pensez à réaliser les sauvegardes nécessaires** (base Pod, base Moodle si accès en écriture).

###### Initialisation

```sh
cd /usr/local/django_projects/podv3
workon django_pod3
```

###### 1. Revendication de tous les enregistrements (simulation)

```sh
python -W ignore manage.py migrate_bbb_recordings --use-manual-claim --dry
```

###### 2. Revendication des 2 derniers enregistrements (simulation)

```sh
python -W ignore manage.py migrate_bbb_recordings --min-value-record-process=1 --max-value-record-process=2 --use-manual-claim --dry &
```

###### 3. Import vidéo externe avec base Moodle (simulation)

```sh
python -W ignore manage.py migrate_bbb_recordings --use-import-video --use-database-moodle --dry
```

###### 4. Import vidéo externe sans base Moodle (10 derniers, simulation)

```sh
python -W ignore manage.py migrate_bbb_recordings --min-value-record-process=1 --max-value-record-process=10 --use-import-video --dry
```

###### 5. Export CSV avec base Moodle (10 derniers, simulation)

```sh
python3 manage.py migrate_bbb_recordings --use_export_csv --use-database-moodle --max-value-record-process=10 --dry
```

### Exploitation

#### Sortie du script

Le script affiche un ensemble d’informations pour chaque ligne traitée; il ne faut pas hésiter à le lancer en mode dry.
![Script](bbb-infrastructure-migration_screens/script.webp)

> 💡 Il est possible de relancer le script plusieurs fois, cela ne va pas créé de doublons. Par contre, cela peut ré-encoder des enregistrements qui avaient déjà été encodés lors de la 1° passe.

#### Interface d’administration

##### Enregistreur

![Enregistreur](bbb-infrastructure-migration_screens/administration_recorder.webp)

##### Liste des enregistrements

![Liste](bbb-infrastructure-migration_screens/administration_recordings.webp)

##### Import des vidéos externes

![Import](bbb-infrastructure-migration_screens/administration_import.webp)

#### Logs de la solution

Selon votre environnement, les logs de Pod peuvent se retrouver dans le fichier /var/log/syslog.

##### Tâches asynchrones (CELERY_TO_ENCODE = True)

Sur les serveurs d’encodage, les logs celery se trouvent dans **/var/log/celery/worker1.log** (selon votre configuration, si vous utilisez plusieurs workers, vous pouvez avoir plusieurs fichiers).

##### RabbitMQ-Server

Si vous utilisez RabbitMQ-Server, sur ce serveur, vous pouvez avoir des informations dans **/var/log/rabbitmq/rabbit@xxxxx.log**.

##### bbb-recorder

Les logs des traitements de bbb-recorder sont accessibles dans le répertoire configuré via **IMPORT_VIDEO_BBB_RECORDER_PATH/logs**.

##### Suppression des enregistrements externes du module d’import des vidéos

Si vous avez opté pour la 2° possibilité, et l’utilisation du module d’import des vidéos : le jour de l’**arrêt complet de votre ancienne infrastructure**, les anciens liens ne fonctionneront plus.
Si vous souhaitez supprimer les enregistrements externes qui concernaient votre ancienne infrastructure, il vous est possible de le faire directement via une requête SQL à exécuter dans la base de données de Pod, à savoir :

```sql
# Remplacer SCRIPT_BBB_SERVER_URL par la bonne valeur, selon votre environnement
DELETE FROM import_video_externalrecording WHERE source_url like 'SCRIPT_BBB_SERVER_URL%'
```

> 💡 Je préfère ne pas mettre cette requête dans le script ; à vous de voir quand vous souhaitez réaliser cette suppression. Bien entendu, pensez à réaliser une sauvegarde avant.
