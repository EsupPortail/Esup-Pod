from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.csrf import csrf_protect
from django.conf import settings
from django.core.exceptions import SuspiciousOperation
import requests
from requests.auth import HTTPBasicAuth
import json
import uuid

XAPI_LRS_URL = getattr(settings, "XAPI_LRS_URL", "")
XAPI_LRS_LOGIN = getattr(settings, "XAPI_LRS_LOGIN", "")
XAPI_LRS_PWD = getattr(settings, "XAPI_LRS_PWD", "")

XAPI_ANONYMIZE_ACTOR = getattr(settings, "XAPI_ANONYMIZE_ACTOR", True)


@csrf_protect
@ensure_csrf_cookie
def statement(request, app: str = None):
    if request.body:
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        statement = {
            "actor": get_actor(request),
            "id": str(uuid.uuid4())
        }
        for key, value in body.items():
            statement[key] = value
        
        x = requests.post(
            XAPI_LRS_URL,
            json=statement,
            auth=HTTPBasicAuth(XAPI_LRS_LOGIN, XAPI_LRS_PWD)
        )
        json_object = json.dumps(statement, indent=2)
        return JsonResponse(json_object, safe=False)
    
    raise SuspiciousOperation("Invalid video id")

def get_actor(request):
    if request.user.is_authenticated :
        if XAPI_ANONYMIZE_ACTOR:
            name = request.user.owner.hashkey
        else:
            name = request.user.get_display_name()
    else:
        if not request.session or not request.session.session_key:
            request.session.save()
        name = request.session.session_key
    return {
        "account" : {
            "homePage": request.get_host(), 
            "name": name,
        },
        "objectType": "Agent",
    }