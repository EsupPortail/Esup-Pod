from django.template import Library

from pod.stats.utils import number_themes

register = Library()


@register.simple_tag(takes_context=False, name="get_number_themes")
def get_number_themes(channel=None) -> int:
    """
    Get the number of themes.

    Returns:
        int: The number of themes in the current site.
    """
    return number_themes(channel)
