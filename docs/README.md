# Pod Documentation

Welcome to the Pod Project Documentation. This guide is intended for developers, administrators, and contributors.

## Table of Contents

### Configuration

- **[Configuration & Customization](configuration.md)**: Central hub for configuring your instance, managing environment variables, and local overrides.

### Application Documentation (One Doc Per App)

Each application has its own dedicated documentation with overview and technical details.

- **[Authentication](authentication/README.md)**: Local login, CAS, LDAP, OIDC, and user management.
- **[Video](video/README.md)**: Video lifecycle, upload, access control, streaming, and subtitle management.
- **[Search](search/README.md)**: Full-text search with Redis Search, cache strategy, and index management.
- **[Completion](completion/README.md)**: Additional metadata, documents, contributors, overlays, and model enrichment.
- **[Collection](collection/README.md)**: Organize videos into Channels, Themes, and Playlists.
- **[Notes](notes/README.md)**: Timestamped and global user notes attached to videos.
- **[Import Video](import_video/README.md)**: Import external videos from YouTube, PeerTube, BigBlueButton, Mediacad, and direct URLs.
- **[Encoding](encoding/README.md)**: Video transcoding with Celery, Redis, and external Runner Manager.
- **[Dressing](dressing/README.md)**: Automated video branding with watermarks and intros/outros.
- **[API & Swagger](api/README.md)**: REST API usage and documentation guide.
- **[Core & Management](core/README.md)**: CLI commands for audit and maintenance.
- **[Maintenance & Commands](core/details.md)**: All `manage.py` commands for maintaining a Pod instance (search reindex, cache, migration, config).
- **[Info](info/README.md)**: System status and public dynamic configuration flags.
- **[Utils](utils/README.md)**: Core utilities, internal paths, and base models.

### Infrastructure & Deployment

- **[Deployment Guide](deployment/README.md)**: Docker architecture, Redis infrastructure, environment setup, and deployment strategies.
- **[Data Migration (V4 to V5)](deployment/migration_v4_to_v5.md)**: Instructions and SQL verification queries for migrating data from Pod V4 to V5.
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
│   │   ├── collection/
│   │   ├── notes/
│   │   ├── import_video/
│   │   ├── encoding/
│   │   ├── dressing/
│   │   ├── info/
│   │   ├── utils/
│   │   └── core/
│   └── config/         # Configuration & Settings
│       ├── django/     # Django Settings (Base, Dev, Test, Prod)
│       └── settings/   # Feature-specific settings (Auth, API, etc.)
├── deployment/         # Docker Configuration
├── docs/               # Documentation (You are here)
│   ├── authentication/
│   ├── video/
│   ├── completion/
│   ├── collection/
│   ├── notes/
│   ├── encoding/
│   ├── dressing/
│   ├── info/
│   ├── utils/
│   ├── api/
│   ├── core/
│   └── deployment/
└── manage.py           # Django CLI
```
