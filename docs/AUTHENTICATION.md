# Authentication Documentation

This document describes the authentication mechanisms available in the Pod application.

## Overview

The application supports multiple authentication methods:
- **Local**: Standard username/password (Django Auth).
- **CAS**: Central Authentication Service.
- **Shibboleth**: Federation based authentication (via headers).
- **OIDC**: OpenID Connect.

All methods eventually resolve to a local `User` and `Owner` profile, issue JWT tokens (Access & Refresh) for API access.

## Architecture

### Models

- **User**: Standard Django User.
- **Owner**: One-to-One extension of User, storing Pod-specific attributes (`affiliation`, `establishment`, `auth_type`).
- **AccessGroup**: Groups that manage permissions/access, often mapped from external attributes (affiliations, LDAP groups).

### Services

The `src.apps.authentication.services` module contains the core logic for user population:

- **UserPopulator**: Central class responsible for mapping external attributes (CAS, LDAP, Shibboleth, OIDC) to local User/Owner fields.
  - Handles creation/update of `Owner` profile.
  - Syncs `AccessGroup` based on affiliations or group codes.
  - Determines `is_staff` status based on affiliation.

### Endpoints

Base path: `/api/auth` (see `urls.py`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/token/` | Local login (username/password). Returns JWT pair. |
| POST | `/token/refresh/` | Refresh access token. |
| GET | `/users/me/` | Get current user profile. |
| POST | `/token/cas/` | Exchange CAS ticket for JWT. |
| GET | `/token/shibboleth/` | JWT from Shibboleth headers (`REMOTE_USER`). |
| POST | `/token/oidc/` | Exchange OIDC code for JWT. |

## Configuration

Settings are controlled via `settings.py` (and environment variables).

### Shibboleth
- `USE_SHIB`: Enable/Disable.
- `SHIB_SECURE_HEADER` / `SHIB_SECURE_VALUE`: Optional security check to ensure request comes from SP.
- `SHIBBOLETH_ATTRIBUTE_MAP`: Maps headers to user fields.

### OIDC
- `USE_OIDC`: Enable/Disable.
- `OIDC_OP_*`: Provider endpoints.
- `OIDC_RP_*`: Client credentials.

## Security Notes

- **Shibboleth**: Ensure the `/api/auth/token/shibboleth/` endpoint is **protected** by the web server (Apache/Nginx) so it cannot be spoofed. Only the SP should be able to set `REMOTE_USER`.
- **JWT**: Tokens have a limited lifetime. Refresh tokens should be stored securely.

## Development

To run authentication tests:
```bash
python manage.py test src.apps.authentication
```
