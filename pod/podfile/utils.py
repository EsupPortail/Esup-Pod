"""Esup-Pod podfile utils."""

from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from .models import UserFolder
from django.contrib.auth.models import User


def update_shared_user(request, action):
    """Update shared user for a folder based on the specified action."""
    foldid = request.GET.get("foldid", 0)
    userid = request.GET.get("userid", 0)
    if foldid == 0 or userid == 0:
        return HttpResponseBadRequest()
    folder = UserFolder.objects.get(id=foldid)
    user = User.objects.get(id=userid)
    if folder.owner == request.user or request.user.is_superuser:
        if action == "add":
            folder.users.add(user)
        elif action == "remove":
            folder.users.remove(user)
        folder.save()
        return HttpResponse(status=201)
    else:
        return HttpResponseBadRequest()
