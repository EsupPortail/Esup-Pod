# ⚙️ Authentication: Technical Details

This document details the configuration and internal workings of the authentication system.

## 1. Authentication Flows

### A. CAS (SSO)

1.  The Frontend redirects the user to the CAS server (e.g., `https://cas.univ-lille.fr`).
2.  Once authenticated, the user returns with a `ticket`.
3.  The Frontend sends this ticket to the Backend via **POST** `/api/auth/token/cas/`.
4.  The Backend validates the ticket, retrieves attributes (and optionally completes via LDAP), updates the local user, and returns a JWT.

### B. Local

1.  The Frontend sends `username` and `password` via **POST** `/api/auth/token/`.
2.  Django verifies the password hash.
3.  If valid, a JWT is returned.

## 2. Configuration (`settings.py`)

The following variables in `src/config/settings/authentication.py` control behavior:

### Module Activation
*   `USE_CAS = True/False`
*   `USE_LDAP = True/False`
*   `USE_SHIB = True/False`
*   `USE_OIDC = True/False`
*   `USE_LOCAL_AUTH = True` (Default)

### CAS Configuration
*   `CAS_SERVER_URL`: Server URL (e.g., `https://cas.univ-lille.fr`)
*   `CAS_VERSION`: Protocol version (e.g., `'3'`)
*   `CAS_APPLY_ATTRIBUTES_TO_USER`: If `True`, updates local data with data from CAS.

### LDAP Configuration
Used if `USE_LDAP = True`.
*   `LDAP_SERVER`: Dictionary containing `url` (e.g., `ldap://ldap.univ.fr`) and `port`.
*   `AUTH_LDAP_BIND_DN`: Connection user (Bind DN).
*   `USER_LDAP_MAPPING_ATTRIBUTES`: Maps LDAP fields to Django.
    *   `uid` -> `username`
    *   `mail` -> `email`
    *   `sn` -> `last_name`
    *   `givenname` -> `first_name`
    *   `eduPersonPrimaryAffiliation` -> `affiliation`

### JWT Configuration (`SIMPLE_JWT`)
*   `ACCESS_TOKEN_LIFETIME`: **60 minutes**.
*   `REFRESH_TOKEN_LIFETIME`: **1 day**.

## 3. Models & Services

### UserPopulator
This is the central service (`src.apps.authentication.services`). It is responsible for:
*   Creating or updating the `User` and their `Owner` profile.
*   Synchronizing **AccessGroups** based on affiliations or LDAP groups (`memberOf`).
*   Determining Staff status (`is_staff`) if the user belongs to a privileged affiliation (`faculty`, `employee`, `staff`).

## 4. API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| **POST** | `/api/auth/token/` | Local login (username/password). |
| **POST** | `/api/auth/token/refresh/` | Refresh expired token. |
| **POST** | `/api/auth/token/cas/` | CAS ticket exchange. |
| **GET** | `/api/auth/token/shibboleth/` | Auth via headers (REMOTE_USER). |
| **POST** | `/api/auth/token/oidc/` | OpenID Connect auth (Code exchange). |
| **GET** | `/api/auth/users/me/` | Connected user info. |
