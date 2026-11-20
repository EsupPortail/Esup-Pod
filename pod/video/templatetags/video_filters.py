"""Esup-Pod video custom filters."""

from django import template
from django.utils.translation import gettext as _
import html
import re

register = template.Library()


@register.filter
def runner_warning_messages(warnings: list[str]) -> list[str]:
    """Translate Runner warnings and keep each displayed message once.

    Args:
        warnings: Technical diagnostics read from the existing encoding log.

    Returns:
        Distinct user-facing messages in their original order. Raw diagnostics
        remain unchanged in the task and encoding logs.
    """
    incomplete_message = _(
        "Part of the video is missing: the resulting video is shorter than expected. "
        "Please check the source file and re-upload a valid, complete video file."
    )
    messages = (
        incomplete_message if "encoding incomplete:" in warning.lower() else warning
        for warning in warnings
    )
    return list(dict.fromkeys(messages))


@register.filter(name="metaformat")
def metaformat(content) -> str:
    """
        Meta tag content text formatter.

    Tries to make meta tag content more usable, by removing HTML entities and
    control chars. Works in conjunction with [striptags] and maybe [safe]
    this way:
        someHTMLContent|metaformat|safe|striptags
    Args:
        content (str):  the string to process
    Returns:
        content (str):  the cleaned string
    """
    content = re.sub(r"\s\s+", " ", html.unescape(str(content)))
    toReplace = {
        "&#39;": "'",
        '"': "'",
    }
    for bad, good in toReplace.items():
        content = content.replace(bad, good)
    return content
