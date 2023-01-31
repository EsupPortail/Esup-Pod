from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.csrf import csrf_protect
from django.conf import settings

# import requests
import json
import uuid
from .models import XAPI_Statement

XAPI_LRS_URL = getattr(settings, "XAPI_LRS_URL", "")
XAPI_LRS_LOGIN = getattr(settings, "XAPI_LRS_URL", "")
XAPI_LRS_PWD = getattr(settings, "XAPI_LRS_PWD", "")

XAPI_ANONYMIZE_ACTOR = getattr(settings, "XAPI_ANONYMIZE_ACTOR", True)


@csrf_protect
@ensure_csrf_cookie
def statement(request, app: str = None):
    """
    get from \
        https://liveaspankaj.gitbooks.io/xapi-video-profile/content/statement_data_model.html
    statement ID - get from LRS ?
    statement actor : request.user or anonyme ?
    statement verbs : get from post data \
        [Initialized, Played, Paused, Seeked, Interacted, Completed, Terminated ]
    statement Object : An Object with objectType "Activity" MUST be present, \
        as specified in the xAPI Spec. \
        The Object represents the video or media being consumed by the Actor.
    statement Result : \
        optional property that represents a measured outcome related to the Statement \
            in which it is included.
    statement Context : Registration ? Language Extension : session ID, \
        CC/Subtitle Enabled and language, Frame rate, full screen, quality, \
            screen size, video size, speed, user agent, sound volume,
            length : video duration
      Completion Threshold
    Context Activities ? https://w3id.org/xapi/video

    send data to lrs
    x = requests.post(url, json = myobj, auth = HTTPBasicAuth('user', 'pass'))
    print(x.text)
    """
    statement = XAPI_Statement(uuid.uuid4())
    if request.user.is_authenticated :
        if XAPI_ANONYMIZE_ACTOR:
            statement.set_actor(request.user.owner.hashkey)
        else:
            statement.set_actor(request.user.get_display_name())
    else:
        if not request.session or not request.session.session_key:
            request.session.save()
        statement.set_actor(request.session.session_key)
    if request.body:
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        print(json.dumps(body, indent=2))
        
    return JsonResponse({"status": "ok"}, safe=False)
