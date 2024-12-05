"""Esup-Pod video custom filters."""

from django import template
import html
import re

register = template.Library()


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
