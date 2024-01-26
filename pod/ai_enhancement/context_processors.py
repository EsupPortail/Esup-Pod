from django.conf import settings as django_settings

AI_ENRICHMENT_DIR = getattr(django_settings, "AI_ENRICHMENT_DIR", "ai-enrichments")
USE_AI_ENRICHMENT = getattr(django_settings, "USE_AI_ENRICHMENT", True)


def context_settings(request):
    """Return all context settings for ai_enhancement app"""
    new_settings = {
        "AI_ENRICHMENT_DIR": AI_ENRICHMENT_DIR,
        "USE_AI_ENRICHMENT": USE_AI_ENRICHMENT,
    }
    return new_settings
