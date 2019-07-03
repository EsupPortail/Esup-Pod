from django import template
from django.conf import settings

register = template.Library()
USE_RGPD = getattr(settings, 'USE_RGPD', False)


@register.simple_tag(takes_context=True)
def authenticated_require(context):
    request = context['request']
    success_operation = True
    if USE_RGPD:
        if not request.user.is_authenticated:
            success_operation = False
    return success_operation
