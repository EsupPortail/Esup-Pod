from django.http import JsonResponse
from django.db.models import Q, Value as V
from django.db.models.functions import Concat

from .models import User


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
