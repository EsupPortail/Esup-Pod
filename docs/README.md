# Pod V5 Documentation

Welcome to the Pod V5 Project Documentation. This guide is intended for developers, administrators, and contributors.

## Table of Contents

### [Authentication](authentication/README.md)
Understand and configure security.
*   [Overview](authentication/README.md): Supported methods (Local, CAS, LDAP).
*   [Technical Details](authentication/details.md): Advanced configuration, attribute mapping, and internal workings.

### [API & Swagger](api/README.md)
Interact with the backend via the REST API.
*   [Swagger Access](api/README.md): Links to interactive documentation.
*   [Developer Guide](api/guide.md): How to document new endpoints.

### [Deployment](deployment/README.md)
Architecture and production setup.
*   [Deployment Guide](deployment/README.md): System overview.

### [AI & LLM Helpers](LLM_HELPERS.md)
Tools and configurations for AI agents.
*   [Overview](LLM_HELPERS.md): `llms.txt`, MCP config, and Schema automation.

## Project Structure

```bash
Pod_V5/
├── src/            # Application Source Code
├── deployment/     # Docker Configuration
├── docs/           # Documentation (You are here)
└── manage.py       # Django CLI
```
