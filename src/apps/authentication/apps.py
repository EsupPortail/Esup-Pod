from django.apps import AppConfig

class AuthenticationConfig(AppConfig):
    name = 'src.apps.authentication'
    label = 'authentication'
    verbose_name = "Authentication"
    default_auto_field = 'django.db.models.AutoField'