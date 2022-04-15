from django.http import JsonResponse
from django.db.models import Q, Value as V
from django.db.models.functions import Concat

from .models import User

import sys
from urllib.request import parse_http_list as _parse_list_header

def get_owners(search, limit, offset):
    """Return owners filtered by GET parameters 'q'.

        With limit and offset

    Args:
        request (Request): Http Request

    Returns:
        list[dict]: Owners found
    """
    users = list(
        User.objects.annotate(full_name=Concat("first_name", V(" "), "last_name"))
        .annotate(full_name2=Concat("last_name", V(" "), "first_name"))
        .filter(
            Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
            | Q(full_name__icontains=search)
            | Q(full_name2__icontains=search)
        )
        .values(
            "id",
            "first_name",
            "last_name",
        )
    )[offset : limit + offset]

    return JsonResponse(users, safe=False)


def parse_dict_header(value):
    """Parse lists of key, value pairs as described by RFC 2068 Section 2 and
    convert them into a python dict:

    >>> d = parse_dict_header('foo="is a fish", bar="as well"')
    >>> type(d) is dict
    True
    >>> sorted(d.items())
    [('bar', 'as well'), ('foo', 'is a fish')]

    If there is no value for a key it will be `None`:

    >>> parse_dict_header('key_without_value')
    {'key_without_value': None}

    To create a header from the :class:`dict` again, use the
    :func:`dump_header` function.

    :param value: a string with a dict header.
    :return: :class:`dict`
    """
    result = {}
    for item in _parse_list_header(value):
        if '=' not in item:
            result[item] = None
            continue
        name, value = item.split('=', 1)
        if value[:1] == value[-1:] == '"':
            value = unquote_header_value(value[1:-1])
        result[name] = value
    return result


# From mitsuhiko/werkzeug (used with permission).
def unquote_header_value(value, is_filename=False):
    r"""Unquotes a header value.  (Reversal of :func:`quote_header_value`).
    This does not use the real unquoting but what browsers are actually
    using for quoting.

    :param value: the header value to unquote.
    """
    if value and value[0] == value[-1] == '"':
        # this is not the real unquoting, but fixing this so that the
        # RFC is met will result in bugs with internet explorer and
        # probably some other browsers as well.  IE for example is
        # uploading files with "C:\foo\bar.txt" as filename
        value = value[1:-1]

        # if this is a filename and the starting characters look like
        # a UNC path, then just return the value without quotes.  Using the
        # replace sequence below on a UNC path has the effect of turning
        # the leading double slash into a single slash and then
        # _fix_ie_filename() doesn't work correctly.  See #458.
        if not is_filename or value[:2] != '\\\\':
            return value.replace('\\\\', '\\').replace('\\"', '"')
    return value