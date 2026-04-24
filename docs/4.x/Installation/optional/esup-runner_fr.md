---
layout: default
version: 4.x
lang: fr
---

# Externalisation des encodages et transcriptions via Esup-Runner

> 💡 Cette documentation ne concerne que les versions de ESUP-Pod 4.2.0 et suivantes.

## Objectif

Quand `USE_RUNNER_MANAGER = True`, Esup-Pod délègue les traitements d'encodage et de transcription à un ou plusieurs services Esup-Runner, nommés Runner Manager.

## Prérequis

- Installer/configurer un service Runner Manager: [Esup-Runner](https://github.com/EsupPortail/esup-runner).
- Cette fonctionnalité nécessite **Pod 4.2 minimum**.

Ce document explique:

- le flux fonctionnel de bout en bout;
- le paramétrage `settings_local.py`;
- la configuration à faire dans l'administration (Runner managers);
- l'exploitation quotidienne dans l'administration des tâches;
- l'importance de la commande `process_tasks` lancée régulièrement en CRON.

## Vue d'ensemble du flux

1. Un utilisateur (ou un traitement interne) déclenche un encodage, une transcription ou un encodage studio.
2. Pod crée/positionne une tâche locale `Task` en `pending`.
3. Pod tente d'envoyer la tâche à un Runner Manager (`/task/execute`) avec authentification Bearer.
4. Si aucun runner n'est joignable, la tâche reste `pending` (elle sera reprise par `process_tasks`).
5. Le runner exécute la tâche, puis appelle le webhook Pod `POST /runner/notify_task_end/`.
6. Pod met à jour le statut de la tâche, puis, si `completed`, télécharge les résultats (`/task/result/<task_id>`) et importe les artefacts.
7. Pod finalise la tâche en `completed` et met à jour les objets métiers (fichiers encodés, sous-titres, vidéo studio, etc.).

## Paramétrage `settings_local.py`

Configuration minimale recommandée, en production:

```py
USE_RUNNER_MANAGER = True
RM_TASKS_DELETED_AFTER_DAYS = 60
SECURE_SSL_REDIRECT = True
ENCODE_VIDEO = "start_encode"
```

### `USE_RUNNER_MANAGER = True`

- Active le mode d'externalisation.
- Les fonctions `start_encode` et `start_transcript` passent alors par `pod.video_encode_transcript.runner_manager`.
- Active également la route webhook `/runner/notify_task_end/` dans `pod/urls.py`.

### `RM_TASKS_DELETED_AFTER_DAYS = 60`

- Utilisé par la commande `process_tasks`.
- Supprime les tâches `completed` âgées de plus de 60 jours.
- Si absent, invalide, ou `<= 0`, le nettoyage est ignoré.

### `SECURE_SSL_REDIRECT = True`

- Paramètre utilisé en production pour forcer la redirection HTTP vers HTTPS.
- Ce réglage devrait déjà être présent; vérifiez que sa valeur est bien `True`.
- S'il est absent, le site reste accessible en HTTP.

### `ENCODE_VIDEO = "start_encode"`

- Fonction appelée pour lancer l’encodage des vidéos.
- Il s'agit de la valeur par défaut, donc ce paramètre peut être absent de votre `settings_local.py`.

## Configuration via l'administration

### 1. Administration des Runner Managers

Dans l'administration, créez au moins un Runner Manager:

- `name`: nom lisible (ex: `um-rm-gpu01`);
- `priority`: plus la valeur est faible, plus le runner est prioritaire;
- `url`: URL de base du runner manager;
- `token`: token Bearer partagé avec ce runner;
- `site`: site Django concerné.

Bonnes pratiques:

- configurer au moins 2 runners pour la tolérance aux pannes;
- utiliser les priorités pour piloter le routage;
- en cas de même priorité, Pod applique une rotation (round-robin) entre runners de ce groupe.

### 2. Tester la connectivité

Sur la fiche d'un Runner Manager, après avoir réalisé la saisie et sauvegarder, utilisez le bouton **Test connection**:

- Pod appelle l'endpoint `manager/health`;
- vérifie réseau, URL et token;
- affiche un retour explicite (`200/204`, `401/403`, `404`, etc.).

## Exploitation via l'administration des tâches

L'admin `Task` permet de piloter la file:

- visualiser le `type` (`encoding`, `transcription`, `studio`);
- suivre le `status` (`pending`, `running`, `completed`, `failed`, `timeout`);
- voir les informations associées aux tâches;
- lire le champ `script_output` pour diagnostic.

Action utile:

- **Redémarrer les tâches sélectionnées**: remet les tâches sélectionnées en `pending`, vide les champs techniques (`task_id`, runner, sortie script, rang), puis relance immédiatement l'envoi vers les runners.

En parallèle, l'interface vidéo affiche aussi le rang en file d'attente (`rank`) et le total des tâches `pending`.

## Rôle de `process_tasks` en exploitation

La commande:

```sh
python manage.py process_tasks
```

est le moteur opérationnel à exécuter périodiquement. Elle:

1. contrôle les tâches `running` bloquées depuis plus de 2h et tente une réconciliation avec le runner;
2. soumet les tâches `pending` (encodage, transcription, studio) aux runners disponibles;
3. applique l'ordonnancement des priorités (notamment non-étudiants avant étudiants);
4. met à jour les rangs de file;
5. purge les tâches terminées selon `RM_TASKS_DELETED_AFTER_DAYS`.

Sans cette commande en récurrence:

- des tâches peuvent rester bloquées en `pending`;
- la reprise/failover vers un autre runner ne se fait pas;
- la purge automatique n'est pas exécutée.

## Planification CRON recommandée

Exemple toutes les 3 minutes:

```cron
# Job pour les tâches Esup-Runner
*/3 * * * * /usr/bin/bash -c 'export WORKON_HOME=/home/pod/.virtualenvs; export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3; cd /usr/local/django_projects/podv4; source /usr/local/bin/virtualenvwrapper.sh; workon django_pod4; python manage.py process_tasks >> /usr/local/django_projects/podv4/pod/log/process_tasks.log 2>&1'
```

Conseils:

- surveillez régulièrement le fichier de log;
- ajustez la fréquence selon votre volumétrie.

## Checklist de mise en service

1. Activer `USE_RUNNER_MANAGER = True`.
2. Régler `RM_TASKS_DELETED_AFTER_DAYS` (ex: `60`).
3. Créer les Runner Managers dans l'administration (URL/token/priorité/site).
4. Valider chaque manager via **Test connection**.
5. Déployer le CRON `process_tasks`.
6. Vérifier dans l'admin `Task` la transition des statuts `pending -> running -> completed`.
