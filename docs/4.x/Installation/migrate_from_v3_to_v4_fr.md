---
layout: default
version: 4.x
lang: fr
---

# Système de migration des données entre la version 3 et la version 4

Ce document décrit le processus de migration des données de l'application Pod depuis la version 3.8.x vers la version 4.0.x.
Le système repose sur deux scripts principaux :

- l'un pour exporter les données de Pod v3 vers un fichier JSON,
- l'autre pour importer ce fichier JSON dans Pod v4.

## Prérequis

- Une version de Pod en 3.8.x (de 3.8.1 à 3.8.4 à ce jour)
- Une version de Pod en 4.0.x (4.0.beta à ce jour)
- Assurez-vous d'avoir accès à la base de données de Pod, en version 3.8.x (MariaDB/MySQL ou PostgreSQL).
- Assurez-vous d'avoir accès à la base de données de Pod, en version 4.0.x (MariaDB/MySQL ou PostgreSQL).

---

## Exportation des données de Pod v3

### Description de l’export

Ce premier script exporte les données de la base de données Pod v3.8.x vers un fichier JSON. Il prend en charge les bases de données MariaDB/MySQL et PostgreSQL et adapte les requêtes SQL en conséquence.

*Attention, ce script doit être exécuté depuis un serveur de Pod v3.*

La dernière version de ce script `export_data_from_v3_to_v4.py` est accessible ici : [https://github.com/EsupPortail/Esup-Pod/tree/main/pod/video/management/commands](https://github.com/EsupPortail/Esup-Pod/tree/main/pod/video/management/commands)

Il est nécessaire de récupérer ce script et de le positionner dans le répertoire `pod/video/management/commands`, avec les bons droits.
{: .alert .alert-warning}

### Fonctionnalités clés de l’export

- Exporte les tables spécifiées de la base de données Pod v3 vers un fichier JSON.
- Prend en charge les bases de données MariaDB/MySQL et PostgreSQL.
- Crée un répertoire pour stocker les données exportées s'il n'existe pas déjà.
- Fournit des messages détaillés de succès et d'erreur.

### Remarques importantes pour l’export

- Le fichier JSON sera généré à ce niveau : `BASE_DIR/data_from_v3_to_v4/v3_exported_tables.json`.
  - Exemple : `/usr/local/django_projects/data_from_v3_to_v4/v3_exported_tables.json`.

Vérifier votre `custom/settings_local.py` pour trouver le répertoire configuré dans `BASE_DIR`.
{: .alert .alert-warning}

- Ce script peut être exécuté autant de fois que nécessaire ; le fichier JSON est régénéré à chaque exécution.

### Exportation

Exécutez le script depuis un serveur Pod v3 en utilisant la commande suivante :

```bash
python manage.py export_data_from_v3_to_v4
```

---

## Importation des données dans Pod v4

### Description de l’import

Ce script importe les données du fichier JSON généré précédemment dans une base de données de Pod v4. Il prend en charge les bases de données MariaDB/MySQL et PostgreSQL, lit les données du fichier JSON spécifié, les traite et les insère dans les tables appropriées de la base de données de Pod v4.

### Fonctionnalités clés de l’import

- Importe un fichier JSON généré avec les tables spécifiées de la base de données Pod v3.
- Prend en charge les bases de données MariaDB/MySQL et PostgreSQL.
- Crée un répertoire pour stocker les données exportées s'il n'existe pas déjà (généralement inutile).
- Fournit des messages détaillés de succès et d'erreur.
- Prend en charge la gestion des mots-clés pour les vidéos et les enregistreurs via la bibliothèque Tagulous.
- Peut exécuter une commande Bash pour créer la base de données et initialiser les données.
- Prend en charge une gestion sécurisée des erreurs et un mode de simulation.

### Remarques importantes pour l’import

- Le fichier JSON doit être trouvé à `BASE_DIR/data_from_v3_to_v4/v3_exported_tables.json`.
  - Exemple : `/usr/local/django_projects/data_from_v3_to_v4/v3_exported_tables.json`.

Vérifier votre `custom/settings_local.py` pour trouver le répertoire configuré dans `BASE_DIR`.
{: .alert .alert-warning}

- Définissez `DEBUG = False` dans `settings_local.py` pour éviter les avertissements/debug/info.

- Peut être exécuté avec une base de données MariaDB/MySQL ou PostgreSQL.

- Si vous rencontrez une erreur de type "Too many connections", vous pouvez augmenter la valeur de la variable `time_sleep`.
  Le traitement prendra plus de temps, mais pourra se terminer sans erreur.

- Ce script peut être exécuté autant de fois que nécessaire ; les données sont supprimées avant l'insertion.

- Selon vos données, ce script peut prendre beaucoup de temps. Typiquement, l'importation de la table `video_viewcount` est longue.
  De plus, comme la librairie pour la gestion des mots-clés a changé entre la v3 et la v4, le traitement est spécifique et nécessite du temps pour éviter les erreurs de type "Too many connections".

- Après l'importation, n'oubliez pas de rendre le `MEDIA_ROOT` de Pod v3 accessible aux serveurs Pod v4.

- Après l'importation, n'oubliez pas de **réindexer toutes les vidéos** pour Elasticsearch avec :

```bash
python manage.py index_videos --all
```

### Importation

Exécutez le script en utilisant la commande de gestion :

```bash
python manage.py import_data_from_v3_to_v4
```

#### Arguments

- `--dry` : Simule ce qui sera réalisé (par défaut=False).
- `--createDB` : Exécute des commandes Bash pour créer des tables dans la base de données et ajouter des données initiales (voir `make createDB`). La base de données doit être vide (par défaut=False).
- `--onlytags` : Traite uniquement les mots-clés (par défaut=False). Utile si vous rencontrez le problème 'Too many connections' pour la gestion des mots-clés.

#### Exemples

Mode simulation :

```bash
python manage.py import_data_from_v3_to_v4 --dry
```

Si la base de données est totalement vide (sans tables), il est possible d'exécuter cette commande qui réalise un `make createDB` avant l'importation des données :

```bash
python manage.py import_data_from_v3_to_v4 --createDB
```

Si vous avez rencontré une erreur de type "Too many connections" lors de l'importation des mots-clés, n'hésitez pas à augmenter la valeur de la variable `time_sleep` (genre 0.4 ou 0.5, en secondes) et relancer le traitement, mais seulement pour les mots-clés :

```bash
python manage.py import_data_from_v3_to_v4 --onlytags
```

Bien entendu, il est possible de mixer les différents arguments.

---

En suivant ces instructions, vous devriez pouvoir migrer avec succès
 votre base de données de Pod v3.8.x vers Pod v4.0.x.
