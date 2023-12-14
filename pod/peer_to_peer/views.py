from django.http import JsonResponse
from django.http import HttpResponseForbidden
from django.core.cache import cache
from django.middleware.csrf import get_token
from django.shortcuts import render
from django.views.decorators.csrf import (
    csrf_exempt,
    csrf_protect,
    ensure_csrf_cookie,
)
from django.utils.translation import ugettext_lazy as _

import json
# ou cache dedié ?
# from django.core.cache import caches
# cache  = caches['video_p2p']
# keys format : <url>_ID_<id>

@csrf_exempt   # TODO Add csrf cookie
def store_urls_id(request, id): # TODO Add documentation
    cache.delete_pattern("*_ID_%s" % id)
    if request.body:
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        cache.set_many(body)
        return JsonResponse(body)
    return HttpResponseForbidden(_("You must provide data to store"))


# @csrf_protect
# @ensure_csrf_cookie
@csrf_exempt # TODO Add csrf cookie
def get_ids_by_urls(request): # TODO Add documentation
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
