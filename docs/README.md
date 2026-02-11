# Pod V5 Documentation

Welcome to the Pod V5 Project Documentation. This guide is intended for developers, administrators, and contributors.

## Table of Contents

### Navigation par Application (One Doc Per App)

Bienvenue dans la documentation officielle de Pod V5. Chaque application dispose de sa propre documentation dédiée.

- **[Configuration & Personnalisation](configuration.md)** : Le hub central pour paramétrer votre instance, gérer les variables d'environnement et les surcharges locales.
- **[Authentication](authentication/README.md)** : Connexion locale, CAS, LDAP, OIDC et gestion des utilisateurs.
- **[API & Swagger](api/README.md)** : Guide d'utilisation et de documentation de l'API REST.
- **[Core & Management](core/MANAGEMENT_COMMANDS.md)** : Commandes CLI pour l'audit et la maintenance.
- **[Déploiement & CI/CD](deployment/README.md)** : Architecture Docker, production et automatisation GitHub Actions.
- **[AI & LLM Helpers](LLM_HELPERS.md)** : Contexte pour les agents IA et LLM.

---

### Règles & Contributions

Pour maintenir la qualité du projet, merci de vous référer aux guides suivants (sources uniques de vérité) :

- **[Guide des Contributions](../CONTRIBUTING.md)** : Règles de codage, messages de commit et workflow de PR.
- **[Code de Conduite](../CODE_OF_CONDUCT.md)** : Engagement de la communauté.
- **[Licence](../COPYING.LESSER)** : Mentions légales LGPL 3.0.


---

## Project Structure

```bash
Pod_V5/
├── src/
│   ├── apps/           # Django Apps (Business Logic)
│   └── config/         # Configuration & Settings
│       ├── django/     # Django Settings (Base, Dev, Test, Prod)
│       └── settings/   # Feature-specific settings (Auth, API, etc.)
├── deployment/         # Docker Configuration
├── docs/               # Documentation (You are here)
└── manage.py           # Django CLI
```

## Configuration Hierarchy

The project uses a **Environment Variable Driven** configuration:

1.  **Docker / System**: Environment variables are set in `.env` (or CI secrets).
2.  **`src/config/env.py`**: Loads variables using `django-environ`.
3.  **`src/config/django/*.py`**: Settings files consume these variables.
    - **Features Flags**: `USE_LDAP`, `USE_CAS`, etc. are toggled via env vars.
    - **No `settings_local.py`**: We do not use local python override files. Use `.env` for everything.
