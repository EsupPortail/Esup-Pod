# Configuration Guide

This guide describes how to configure **Esup-Pod V5**.
The project adheres to the [Twelve-Factor App](https://12factor.net/config) methodology, storing configuration in the **environment**.

## Configuration Hierarchy

1.  **Environment Variables (`.env`)**: The source of truth.
2.  **`src/config/env.py`**: Loads the `.env` file using the `django-environ` library.
3.  **Django Settings (`src/config/django/`)**:
    - `base.py`: Core settings shared by all environments.
    - `dev/docker.py`: Development overrides (consumes `.env` defaults).
    - `test/docker.py`: Test-specific overrides (forces feature flags).

## 1. Hiérarchie de Configuration

Le projet suit une logique modulaire :

1.  **Valeurs par défaut** : Définies dans `src/config/defaults/{app_name}.py`. **Ne jamais modifier ces fichiers.**
2.  **Infrastructure & Secrets (`.env`)** : Variables d'environnement pour les services (DB, Host, Keys).
3.  **Surcharges Applicatives (`src/config/settings/{app_name}.py`)** : C'est ici que se passe la personnalisation fonctionnelle (ex: `video.py`, `authentication.py`).

---

## 2. Comment Personnaliser mon Instance ?

Pour modifier un comportement (limites d'upload, couleurs, activations de modules) :

1.  **Identifiez l'application** concernée dans `docs/` (ex: `docs/authentication/`).
2.  **Créez le fichier de surcharge** dans `src/config/settings/` s'il n'existe pas (ex: `src/config/settings/video.py`).
    - Vous pouvez vous inspirer des fichiers `.example` présents dans ce dossier.
3.  **Ajoutez vos variables** en MAJUSCULES. Elles écraseront les valeurs par défaut au démarrage de l'application.

> [!TIP]
> Pour voir la liste complète des variables disponibles pour une application, consultez le fichier `src/config/defaults/{app_name}.py` correspondant.

