from django.conf import settings as django_settings

AI_ENRICHMENT_DIR = getattr(
    django_settings,
    "AI_ENRICHMENT_DIR",
    "ai-enrichments"
)
USE_AI_ENRICHMENT = getattr(
    django_settings,
    "USE_AI_ENRICHMENT",
    True
)
AI_ENRICHMENT_CLIENT_ID = getattr(
    django_settings,
    "AI_ENRICHMENT_CLIENT_ID",
    "mocked_id"
)
AI_ENRICHMENT_CLIENT_SECRET = getattr(
    django_settings,
    "AI_ENRICHMENT_CLIENT_SECRET",
    "mocked_secret"
)


def context_settings(request):
    """Return all context settings for ai_enhancement app"""
    new_settings = {
        "AI_ENRICHMENT_DIR": AI_ENRICHMENT_DIR,
        "USE_AI_ENRICHMENT": USE_AI_ENRICHMENT,
        "AI_ENRICHMENT_CLIENT_ID": AI_ENRICHMENT_CLIENT_ID,
        "AI_ENRICHMENT_CLIENT_SECRET": AI_ENRICHMENT_CLIENT_SECRET,
    }
    return new_settings
