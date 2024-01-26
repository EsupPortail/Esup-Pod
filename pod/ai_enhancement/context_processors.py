from django.conf import settings as django_settings

AI_ENRICHMENT_DIR = getattr(django_settings, "AI_ENRICHMENT_DIR", "ai-enrichments")


def context_settings(request):
    """Return all context settings for ai_enhancement app"""
    new_settings = {"AI_ENRICHMENT_DIR": AI_ENRICHMENT_DIR}
    return new_settings
