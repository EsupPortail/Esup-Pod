Voici une version **professionnelle, claire et structurée** de votre documentation.

J'ai intégré la commande de lien symbolique (`ln -s`) et, surtout, j'ai **clarifié la distinction cruciale** entre l'arrêt simple et la réinitialisation complète (avec suppression des volumes), car c'est ce qui a résolu votre problème de base de données.

-----

# Guide de Déploiement — POD V5

## 1\. Infrastructure & Configuration

La configuration d’infrastructure est entièrement gérée via les **variables d’environnement** définies dans le fichier `.env` à la racine du projet.

> **Note importante :** Le fichier `local_settings.py` ne doit contenir **que les réglages métier** (ex : profils d’encodage, paramètres internes POD). Aucune configuration d’infrastructure (DB, Hosts, Secrets) ne doit y apparaître.

-----

## 2\. Déploiement Développement (Dev)

### Initialisation de l'environnement

Placez-vous dans le dossier de déploiement de développement :

```bash
(pod_v5) benjaminsere@ul63122:/usr/local/django_projects/Pod_V5_Back$ cd deployment/dev/
```

**Première installation uniquement :**
Créez un lien symbolique pour que Docker puisse lire le fichier `.env` situé à la racine :

```bash
(pod_v5) benjaminsere@ul63122:/usr/local/django_projects/Pod_V5_Back/deployment/dev$ ln -s ../../.env .env
```

### Lancer les conteneurs

Construire et démarrer les conteneurs en arrière-plan :

```bash
(pod_v5) benjaminsere@ul63122:/usr/local/django_projects/Pod_V5_Back/deployment/dev$ sudo docker-compose up -d --build
```

### Workflow de développement

Une fois les conteneurs lancés, voici les étapes pour travailler sur l'API :

1.  **Entrer dans le conteneur API :**

    ```bash
    (pod_v5) benjaminsere@ul63122:/usr/local/django_projects/Pod_V5_Back/deployment/dev$ sudo docker-compose exec api bash
    ```

2.  **Appliquer les migrations (si nécessaire) :**

    ```bash
    root@74dfe514ff53:/app#  python manage.py migrate
    ```

3.  **Créer un superuser (si nécessaire) :**

    ```bash
    root@74dfe514ff53:/app#  python manage.py createsuperuser
    ```

4.  **Collecter les fichiers statiques (si nécessaire) :**

    ```bash
    root@74dfe514ff53:/app#  python manage.py collectstatic
    ```

5.  **Lancer le serveur de développement :**

    ```bash
    root@74dfe514ff53:/app#  python manage.py runserver
    ```

    *L'API est accessible sur `http://localhost:8000`.*

Voici une version **claire et professionnelle en anglais** de la section qui explique comment se connecter à la base de données :

---

### Connecting to the Database

Once your development environment is up and running, you can access the MariaDB database directly from the container.

1. **Enter the database container:**

```bash
(pod_v5) benjaminsere@ul63122:/usr/local/django_projects/Pod_V5_Back/deployment/dev$ sudo docker-compose exec db bash
```

2. **Connect to the database using the credentials defined in your `.env` file:**

```bash
root@62d310619d28:/# mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE"
```

* `$MYSQL_USER` → your database username
* `$MYSQL_PASSWORD` → your database password
* `$MYSQL_DATABASE` → the database name

> **Note:** These environment variables are automatically loaded from your `.env` file and passed to the container. If you prefer, you can replace them with the actual values for direct login:

```bash
mysql -uroot -proot_password pod_v5
```

3. **Once connected, you can run standard SQL commands**, for example:

```sql
SHOW TABLES;
SELECT * FROM your_table LIMIT 10;
```

## 3\. Gestion et Arrêt (Dev)

Il existe deux manières d'arrêter l'environnement, selon vos besoins.

### Option A : Arrêt standard (Conservation des données)

Utilisez cette commande pour éteindre les conteneurs tout en **conservant** le contenu de la base de données (utilisateurs, vidéos, etc.).

```bash
sudo docker-compose down
```

### Option B : Réinitialisation complète (Suppression des données)

Utilisez cette commande pour tout effacer et repartir de zéro.
**Indispensable si vous modifiez les mots de passe BDD dans le `.env` ou en cas d'erreur "Access Denied".**

```bash
sudo docker-compose down -v
```

*(L'option `-v` supprime les volumes de base de données).*

-----

## 4\. Déploiement Production (Prod)

Déploiement d'une instance optimisée, sécurisée et autonome.

```bash
cd deployment/prod/
```

```bash
sudo docker-compose up --build -d
```

Ce mode lance :

  * L’API Django via **uWSGI** (mode production).
  * La base MariaDB (persistance sur disque hôte).
  * Nginx (gestion des statiques, médias et proxy).
  * Le chargement automatique des variables d'environnement.

-----

## 5\. Maintenance Docker (Nettoyage)

Si vous avez besoin de libérer de l'espace disque ou de nettoyer des conteneurs/images orphelins :

**Supprimer tous les conteneurs arrêtés :**

```bash
sudo docker container prune -f
```

**Nettoyage complet du système (Images inutilisées, cache, conteneurs stoppés) :**

```bash
sudo docker system prune -af
```