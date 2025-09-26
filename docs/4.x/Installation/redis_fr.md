---
layout: default
version: 4.x
lang: fr
---

# Configuration et usage de REDIS

## Présentation de REDIS

Redis (REmote DIctionary Server) est une base de données NoSQL **clé-valeur** extrêmement rapide, principalement utilisée comme **cache**, **file d’attente** et **moteur de messages**.
Elle fonctionne en mémoire (RAM), ce qui lui permet d’offrir des performances bien supérieures aux bases de données traditionnelles pour certaines tâches.

Dans le cadre de Pod, REDIS est utilisé comme :

- gestionnaire de caches pour les **serveurs Web**,
- gestionnaire de files des tâches d’encodage/transcription/xAPI pour les **serveurs d’encodages**, en complément de **Celery**. _Seulement dans le cas d’encodage déporté sur d’autres serveurs (notion de Celery Broker)_.

À l’heure actuelle, c’est une brique indispensable au fonctionnement de Pod.

## Configuration de REDIS pour Pod

### Liste des bases utiles

| Identifiant de la base | Commentaires                        |
|------------------------|-------------------------------------|
| 2                      | Base pour le plugin select2 (utile pour les listes de sélection) |
| 3                      | Base pour le backend |
| 4                      | Base pour les sessions |
| 5                      | Base pour les encodages et transcodages |
| 6                      | Base pour le xAPI |
{: .table .table-striped}

### Configuration effective

La configuration se réalise dans votre ```custom/settings_local.py``` :

```sh
# Pour utiliser l’encodage traditionnel déporté
CELERY_TO_ENCODE = True
# URL du broker REDIS
CELERY_BROKER_URL = "redis://127.0.0.1:6379/5"
# Permet de ne traiter qu’une tâche à la fois
CELERY_TASK_ACKS_LATE = True
# Gestion des caches
CACHES = {
  'default': {
    'BACKEND': 'django_redis.cache.RedisCache',
    'LOCATION': 'redis://127.0.0.1:6379/3',
    'OPTIONS': {
      'CLIENT_CLASS': 'django_redis.client.DefaultClient',
    },
  },
  'select2': {
    'BACKEND': 'django_redis.cache.RedisCache',
    'LOCATION': 'redis://127.0.0.1:6379/2',
    'OPTIONS': {
      'CLIENT_CLASS': 'django_redis.client.DefaultClient',
    },
  },
}
SESSION_ENGINE = 'redis_sessions.session'
SESSION_REDIS = {
  'host': '127.0.0.1',
  'port': 6379,
  'db': 4,
  'prefix': 'session',
  'socket_timeout': 1,
  'retry_on_timeout': False
}
# Indiquer à select2 la configuration de cache à utiliser
SELECT2_CACHE_BACKEND = "select2"
```

> ⚠️ Selon votre architecture, pensez à remplacer _127.0.0.1_ par l’**adresse IP du serveur REDIS**, cf. [la documentation d’installation](install_standalone_fr#redis).
