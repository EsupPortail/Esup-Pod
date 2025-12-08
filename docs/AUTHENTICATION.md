# Documentation du Module d'Authentification (API Pod)

## 1. Vue d'ensemble

-   Système basé sur **DRF** et **JWT (simplejwt)**
-   Mode hybride via `settings.py` :
    -   Authentification locale
    -   Authentification CAS (SSO)

## 2. Architecture Technique

### Structure des dossiers

  Dossier/Fichier             | Rôle
  ----------------------------| ----------------------------------------
  models/                     | Définition Owner, AccessGroup
  services.py                 | Logique métier CAS/LDAP + droits
  serializers/                | Validation tickets CAS + formatage JWT
  views.py                    | Endpoints API
  urls.py                     | Routage dynamique
  IPRestrictionMiddleware.py  | Sécurité superusers / IP

## 3. Flux d'Authentification

### A. CAS (SSO)

1.  Front → redirection CAS\
2.  CAS → retourne ticket\
3.  Front → POST `/api/auth/token/cas/`\
4.  Backend → validation ticket, synchro LDAP, génération JWT

### B. Local

-   POST `/api/auth/token/`
-   Vérification mot de passe + génération JWT

## 4. Configuration & Déploiement

  Variable            | Description         | Exemple
  --------------------| --------------------| -----------------------------
  SITE_ID             | ID site par défaut  | 1
  DEFAULT_AUTO_FIELD  | Type ID en base     | django.db.models.AutoField
  USE_CAS             | Active CAS          | True
  CAS_SERVER_URL      | URL CAS             | https://cas.univ-lille.fr
  CAS_VERSION         | Version CAS         | 3
  POPULATE_USER       | Stratégie           | CAS / LDAP
  LDAP_SERVER         | Config LDAP         | {"url": "...", "port": 389}

## 5. Logique Métier

### Groupes (AccessGroup)

-   Vérifie affiliations + groupes LDAP\
-   Nettoie anciens groupes auto_sync=True\
-   Ajoute nouveaux groupes

### Statut *is_staff*

-   Recalcul à chaque connexion
-   True si affiliation ∈ AFFILIATION_STAFF (sauf superuser)

## 6. Endpoints API

  Méthode  | URL                       | Description        | Auth
  ---------| --------------------------| -------------------| ------
  POST     | /api/auth/token/          | Login local        | Non
  POST     | /api/auth/token/cas/      | Login CAS          | Non
  POST     | /api/auth/token/refresh/  | Refresh token      | Non
  GET      | /api/auth/users/me/       | Infos utilisateur  | Oui

## 7. Sécurité

### Middleware IP

-   Rétrograde superuser si IP non autorisée

### JWT

-   Durée courte + gestion refresh côté frontend
