# Authentication: Overview

The Pod application authentication module secures access to the API and manages users. It is designed to work in a hybrid mode, accepting both local logins and those from external Identity Providers (SSO).

## Supported Methods

The choice of authentication method is configured via the project settings (`settings.py`).

| Method | Type | Description |
| :--- | :--- | :--- |
| **Local** | Internal | Uses the standard Django database. Ideal for superusers and development. |
| **CAS** | External | **Central Authentication Service**. Commonly used in universities (e.g., University of Lille). |
| **LDAP** | Directory | Direct connection to an LDAP directory to retrieve user attributes. |
| **Shibboleth** | Federation | Authentication based on HTTP headers (REMOTE_USER), managed by the web server (Apache/Nginx). |
| **OIDC** | Federation | **OpenID Connect**. The modern standard for delegated authentication. |

## How it Works

Regardless of the method used to log in, the backend always eventually:

1.  **Validates** credentials with the source (Local DB, CAS, LDAP...).
2.  **Synchronizes** user information (First Name, Last Name, Affiliation) in the local `Owner` table.
3.  **Issues** a pair of **JWT** tokens (Access + Refresh) that the frontend will use for its requests.

## Further Reading

*   ➡️ **[Technical Details & Configuration](details.md)**: Environment variables, detailed flows, and attribute mapping.
*   ⬅️ **[Back to Index](../README.md)**
