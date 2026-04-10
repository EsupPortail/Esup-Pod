# Pod V5 Documentation

Welcome to the Pod V5 Project Documentation. This guide is intended for developers, administrators, and contributors.

## Table of Contents

### Configuration

- **[Configuration & Customization](configuration.md)**: Central hub for configuring your instance, managing environment variables, and local overrides.

### Application Documentation (One Doc Per App)

Each application has its own dedicated documentation with overview and technical details.

- **[Authentication](authentication/README.md)**: Local login, CAS, LDAP, OIDC, and user management.
- **[Video](video/README.md)**: Video lifecycle, upload, access control, streaming, and subtitle management.
- **[Encoding](encoding/README.md)**: Video transcoding with Celery, Redis, and external Runner Manager.
- **[API & Swagger](api/README.md)**: REST API usage and documentation guide.
- **[Core & Management](core/README.md)**: CLI commands for audit and maintenance.

### Infrastructure & Deployment

- **[Deployment Guide](deployment/README.md)**: Docker architecture, environment setup, and deployment strategies.
- **[CI/CD & Testing](CI_CD.md)**: GitHub Actions pipelines, local testing, and quality checks.

---

### Rules & Contributions

To maintain project quality, please refer to the following guides (single sources of truth):

- **[Contribution Guide](../CONTRIBUTING.md)**: Coding rules, commit messages, and PR workflow.
- **[Code of Conduct](../CODE_OF_CONDUCT.md)**: Community commitment.
- **[License](../COPYING.LESSER)**: LGPL 3.0 legal notices.

---

## Project Structure

```text
Pod_V5_Back/
├── src/
│   ├── apps/           # Django Apps (Business Logic)
│   │   ├── authentication/
│   │   ├── video/
│   │   ├── encoding/
│   │   └── core/
│   └── config/         # Configuration & Settings
│       ├── django/     # Django Settings (Base, Dev, Test, Prod)
│       └── settings/   # Feature-specific settings (Auth, API, etc.)
├── deployment/         # Docker Configuration
├── docs/               # Documentation (You are here)
│   ├── authentication/
│   ├── video/
│   ├── encoding/
│   ├── api/
│   ├── core/
│   └── deployment/
└── manage.py           # Django CLI
```
