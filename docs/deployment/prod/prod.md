TODO

.env.prod : 

```bash
# Django will load the production settings module
DJANGO_SETTINGS_MODULE=config.django.prod.prod

# Add only the exact production domains.
ALLOWED_HOSTS=api.your-domain.com

# CORS: required ONLY if your frontend is hosted on a different origin
# (different domain, subdomain, port, or protocol)
# If your frontend is on another domain, uncomment and set:
# CORS_ALLOWED_ORIGINS=https://front.your-domain.com

# If frontend and API share the same origin (same domain + protocol + port),
# you do NOT need CORS_ALLOWED_ORIGINS.

```