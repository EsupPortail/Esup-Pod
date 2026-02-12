# Pod V5 Documentation

Welcome to the Pod V5 Project Documentation. This guide is intended for developers, administrators, and contributors.

## Table of Contents

### Application Documentation (One Doc Per App)

Welcome to the official Pod V5 documentation. Each application has its own dedicated documentation.

- **[Configuration & Customization](configuration.md)**: Central hub for configuring your instance, managing environment variables, and local overrides.
- **[Authentication](authentication/README.md)**: Local login, CAS, LDAP, OIDC, and user management.
- **[API & Swagger](api/README.md)**: REST API usage and documentation guide.
- **[Core & Management](core/MANAGEMENT_COMMANDS.md)**: CLI commands for audit and maintenance.
- **[Deployment & CI/CD](deployment/README.md)**: Docker architecture, production, and GitHub Actions automation.
- **[AI & LLM Helpers](LLM_HELPERS.md)**: Context for AI agents and LLMs.

---

### Rules & Contributions

To maintain project quality, please refer to the following guides (single sources of truth):

- **[Contribution Guide](../CONTRIBUTING.md)**: Coding rules, commit messages, and PR workflow.
- **[Code of Conduct](../CODE_OF_CONDUCT.md)**: Community commitment.
- **[License](../COPYING.LESSER)**: LGPL 3.0 legal notices.

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