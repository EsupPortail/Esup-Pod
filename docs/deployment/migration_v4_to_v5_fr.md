# Système de migration des données Esup-Pod entre la version 4 et la version 5

Ce document décrit le processus de migration des données de l'application Esup-Pod depuis la version 4.x vers la version 5.x.

Le système de migration repose sur deux scripts principaux :

1. **L'exportateur** (`export_data_from_v4.py`) : à exécuter sur l'instance Pod V4 pour exporter ses données dans un fichier JSON.
2. **L'importateur** (`import_data_from_v4_to_v5.py`) : à exécuter sur l'instance Pod V5 pour lire ce fichier JSON et insérer les données dans la nouvelle structure.

---

## Prérequis

- Une instance **Pod en version 4.x** (v4.x fonctionnelle).
- Une instance **Pod en version 5.x** installée et configurée.
- Un accès aux bases de données respectives (MariaDB/MySQL ou PostgreSQL pour la V4, MariaDB/MySQL pour la V5).
- Les volumes ou répertoires contenant les fichiers médias (`MEDIA_ROOT`) doivent être accessibles/transférables d'un serveur à l'autre.

---

## 1. Exportation des données depuis Pod V4

Le script d'export extrait les données des tables de la base de données Pod V4.x et applique des corrections automatiques pour s'assurer que les données exportées respectent les contraintes d'intégrité de la V5.

### Fonctionnalités de l'export

- **Compatibilité SGBD** : Prend en charge les bases de données MariaDB/MySQL et PostgreSQL (en adaptant les requêtes SQL si nécessaire).
- **Nettoyage automatique** : Corrige certains problèmes de cohérence (par exemple, dans la table `meeting`, si la date de fin récurrente `recurring_until` est antérieure ou égale à la date de début `start_at` à cause des décalages de fuseaux horaires, elle est mise à `NULL` pour éviter les violations de contraintes en V5).
- **Génération automatique du dossier** : Crée le répertoire cible s'il n'existe pas.

### Exécution de l'export

> [!IMPORTANT]
> Ce script doit impérativement être exécuté depuis le serveur hébergeant la version **Pod V4**.

Le script `export_data_from_v4.py` doit être placé dans le répertoire `pod/video/management/commands/` de l'instance V4 (si ce n'est pas déjà le cas).

Lancez la commande suivante sur le serveur Pod V4 :

```bash
python manage.py export_data_from_v4
```

### Emplacement du fichier généré

Le fichier JSON sera généré à l'emplacement suivant (relativement à votre `BASE_DIR`) :
`BASE_DIR/../../data_from_v4_to_v5/v4_exported_to_v5.json`

> [!TIP]
> Ce script peut être exécuté autant de fois que nécessaire. Le fichier JSON est entièrement régénéré à chaque exécution.

---

## 2. Importation des données dans Pod V5

Le script d'importation lit le fichier JSON généré et insère les enregistrements dans la base de données Pod V5 en adaptant la structure des données aux nouvelles applications (notamment l'application `collection` qui centralise les chaînes, thèmes, playlists et favoris).

### Fonctionnalités de l'import

- **Reprise sur erreur (Resiliency)** : L'import utilise une table de mapping (`core_migrationmapping`) pour suivre l'état de chaque enregistrement migré. Si le script s'arrête ou échoue, vous pouvez le relancer : il reprendra là où il s'est arrêté en ignorant les éléments déjà importés avec succès.
- **Gestion des signaux** : Désactive temporairement les signaux Django (pre-save, post-save, etc.) lors de l'import pour maximiser les performances et éviter les boucles d'effets de bord, puis les réactive à la fin du traitement.
- **Mode simulation** : Permet de tester la migration de bout en bout sans modifier la base de données.
- **Super-utilisateur automatique** : Si aucun super-utilisateur n'est trouvé à la fin de l'import, le script en crée un par défaut (en se basant sur les variables d'environnement).

### Exécution de l'import

> [!IMPORTANT]
> Avant de lancer l'import, assurez-vous d'avoir transféré le fichier JSON généré par l'étape d'export vers l'instance Pod V5. Par défaut, le script cherche le fichier dans `.tmp/v4_exported_to_v5.json`.

Exécutez la commande d'import depuis votre instance Pod V5 :

```bash
python manage.py import_data_from_v4_to_v5
```

### Arguments de la commande

Le script d'import supporte plusieurs arguments pour personnaliser son comportement :

| Argument                | Description                                                                                       | Valeur par défaut             |
| :---------------------- | :------------------------------------------------------------------------------------------------ | :---------------------------- |
| `--file <chemin>`       | Spécifie le chemin d'accès au fichier JSON d'export.                                              | `.tmp/v4_exported_to_v5.json` |
| `--verify-files`        | Vérifie l'existence physique de chaque fichier média référencé dans le dossier `/media/`.         | `False`                       |
| `--dry-run`             | Lance l'importation dans une transaction simulée qui est entièrement annulée (rollback) à la fin. | `False`                       |
| `--batch-size <nombre>` | Définit la taille des lots d'écriture en base de données pour optimiser les transactions.         | `1000`                        |

### Exemples d'utilisation

**Mode simulation (recommandé en premier essai) :**

```bash
python manage.py import_data_from_v4_to_v5 --dry-run
```

**Importation avec un fichier spécifique et vérification de la présence des fichiers médias :**

```bash
python manage.py import_data_from_v4_to_v5 --file /chemin/vers/v4_exported_to_v5.json --verify-files
```

---

## 3. Actions Post-Migration

1. **Fichiers médias** : N'oubliez pas de copier ou de rendre accessible le contenu du répertoire `MEDIA_ROOT` de votre ancienne instance Pod V4 dans le répertoire de stockage de votre instance Pod V5.
2. **Super-utilisateur** : Si vous n'avez pas défini de variables d'environnement spécifiques, un super-utilisateur par défaut a été créé s'il n'en existait aucun :
   - **Username** : `admin` (ou valeur de `DJANGO_SUPERUSER_USERNAME`)
   - **Password** : `admin` (ou valeur de `DJANGO_SUPERUSER_PASSWORD`)
   - _N'oubliez pas de modifier ce mot de passe dès votre première connexion en production._

---
