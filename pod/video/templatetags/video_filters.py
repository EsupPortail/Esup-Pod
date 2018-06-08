from django import template
#from HTMLParser import HTMLParser
from html.parser import HTMLParser

import re

register = template.Library()
parser = HTMLParser()

@register.filter(name='metaformat')
def metaformat(content):
    """
        Meta tag content text formatter
    Tries to make meta tag content more usable, by removing HTML entities and
    control chars. Works in conjunction with [striptags] and maybe [safe]
    this way:
        someHTMLContent|metaformat|safe|striptags
    Args:
        content (str):  the string to process
    Returns:
        content (str):  the cleaned string
    """
    content = re.sub('\s\s+', " ", parser.unescape(content))
    toReplace = {
        '&#39;': "'",
        '"': "'",
    }
    for bad, good in toReplace.items():
        content = content.replace(bad, good)
    return content