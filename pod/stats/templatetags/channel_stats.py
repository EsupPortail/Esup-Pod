from django.template import Library

from pod.stats.utils import number_themes
from pod.video.models import Channel

register = Library()


@register.simple_tag(takes_context=False, name="get_number_themes")
def get_number_themes(channel: Channel = None) -> int:
    """
    Get the total number of themes associated with a channel.

    Args:
        channel (Channel, optional): The channel for which to retrieve the number of themes. Defaults to None.

    Returns:
        int: The total number of themes associated with the channel.
    """
    return number_themes(channel)
