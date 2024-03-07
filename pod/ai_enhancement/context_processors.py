from django.conf import settings as django_settings

USE_AI_ENRICHMENT = getattr(
    django_settings,
    "USE_AI_ENRICHMENT",
    True
)
AI_ENHANCEMENT_CLIENT_ID = getattr(
    django_settings,
    "AI_ENHANCEMENT_CLIENT_ID",
    "mocked_id",
)
AI_ENHANCEMENT_CLIENT_SECRET = getattr(
    django_settings,
    "AI_ENHANCEMENT_CLIENT_SECRET",
    "mocked_secret",
)
API_URL = getattr(
    django_settings,
    "AI_ENRICHMENT_API_URL",
    "",
)
API_VERSION = getattr(
    django_settings,
    "AI_ENRICHMENT_API_VERSION",
    "",
)


def context_settings(request):
    """Return all context settings for ai_enhancement app"""
    new_settings = {
        "USE_AI_ENRICHMENT": USE_AI_ENRICHMENT,
        "AI_ENHANCEMENT_CLIENT_ID": AI_ENHANCEMENT_CLIENT_ID,
        "AI_ENHANCEMENT_CLIENT_SECRET": AI_ENHANCEMENT_CLIENT_SECRET,
        "API_URL": API_URL,
        "API_VERSION": API_VERSION,
    }
    return new_settings
