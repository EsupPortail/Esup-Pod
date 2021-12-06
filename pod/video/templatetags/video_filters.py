"""Esup-Pod video custom filters."""
from django import template
from html.parser import HTMLParser
import html
import re

register = template.Library()
parser = HTMLParser()
html_parser = html


@register.filter(name="metaformat")
def metaformat(content):
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
    try:
        content = re.sub(r"\s\s+", " ", parser.unescape(content))
    except AttributeError:
        content = re.sub(r"\s\s+", " ", html_parser.unescape(content))
    toReplace = {
        "&#39;": "'",
        '"': "'",
    }
    for bad, good in toReplace.items():
        content = content.replace(bad, good)
    return content
