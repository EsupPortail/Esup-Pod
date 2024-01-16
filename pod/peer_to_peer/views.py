from django.http import JsonResponse
from django.http import HttpResponseForbidden
from django.core.cache import cache
from django.middleware.csrf import get_token
from django.shortcuts import render
from django.views.decorators.csrf import (
    csrf_exempt,
)
from django.utils.translation import ugettext_lazy as _

import json
# ou cache dedié ?
# from django.core.cache import caches
# cache  = caches['video_p2p']
# keys format : <url>_ID_<id>


@csrf_exempt   # TODO Add csrf cookie
def store_urls_id(request, id):  # TODO Add documentation
    uuid = id.split("_ID_")[-1]
    cache.delete_pattern("*_ID_%s" % uuid)
    if request.body:
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        expiration_time = 12 * 60 * 60 # 12 hours
        cache.set_many(body, timeout=expiration_time)
        return JsonResponse(body)
    return HttpResponseForbidden(_("You must provide data to store"))


# @csrf_protect
# @ensure_csrf_cookie
@csrf_exempt  # TODO Add csrf cookie
def get_ids_by_urls(request):  # TODO Add documentation
    if request.body:
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        all_keys = cache.keys("*")

        # Afficher le contenu associé à chaque clé
        for key in all_keys:
            value = cache.get(key)
            print(f"Key: {key}, Value: {value}")

        all_keys = cache.keys("%s*" % body["url"])
        print("all_keys : ", all_keys)
        response = JsonResponse(all_keys, safe=False)
        return response
    return HttpResponseForbidden(_("You must provide url to get keys"))


def get_csrf_token(request):
    print(get_token(request))
    return JsonResponse({"csrf_token": get_token(request)})


def test(request):
    return render(request, "peer_to_peer/test.html")


@csrf_exempt
def clear_invalid_peer_in_caches(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            peer_id = data["peer_id"]

            if peer_id:
                cache.delete(peer_id)
                return JsonResponse({"message": "Peer deleted from cache", "deleted_peer": peer_id}, status=200)
            else:
                return JsonResponse({"message": "No peer_id provided"}, status=400)
        except Exception as e:
            return JsonResponse({"message": "Error while deleting peer from cache"}, status=500)
    else:
        return JsonResponse({"message": "Only POST method is allowed"}, status=405)
