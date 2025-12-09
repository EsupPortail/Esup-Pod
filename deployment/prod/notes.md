# Production Deployment Configuration

**Work in Progress**

This directory contains production deployment configurations for Pod_V5_Back. These files are currently under development.

## Status

- `docker-compose.yml` - **TO DO**: Will contain Nginx + uWSGI + MariaDB orchestration
- `Dockerfile` - **TO DO**: Will contain multi-stage build for production image with Nginx reverse proxy

## Expected Configuration

The production setup will include:

1. **Reverse Proxy (Nginx)** - Serves static files and proxies API requests to application server
2. **Application Server (uWSGI)** - Runs Django application
3. **Database (MariaDB)** - Persistent database (optionally managed separately)
4. **SSL/TLS** - HTTPS configuration (Let's Encrypt or similar)
5. **Security Hardening**:
   - `DEBUG=False`
   - Proper `ALLOWED_HOSTS` configuration
   - Secret management via environment variables or external vault
   - No automatic superuser creation

## Next Steps

- [ ] Create production-ready Dockerfile with multi-stage build
- [ ] Create production docker-compose.yml with Nginx + uWSGI
- [ ] Add entrypoint.sh for production (without dev-only features)
- [ ] Configure Nginx configuration file template
- [ ] Document environment variables for production
- [ ] Add deployment guide in `docs/deployment/prod.md`

## For Now

If you need to deploy this application, please refer to:
- Django deployment documentation: https://docs.djangoproject.com/en/5.2/howto/deployment/
- Docker deployment best practices: https://docs.docker.com/engine/reference/builder/

The development setup in `../dev/` can be used as a reference for understanding the application requirements.
