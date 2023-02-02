from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.csrf import csrf_protect
from django.conf import settings
from django.core.exceptions import SuspiciousOperation
from .tasks import send_xapi_statement_task
import json
import uuid

# pip3 install ralph-malph==3.2.1
# from ralph.models.xapi.fields.actors import AccountActorField
# from ralph.models.xapi.video.statements import VideoPlayed

XAPI_ANONYMIZE_ACTOR = getattr(settings, "XAPI_ANONYMIZE_ACTOR", True)


@csrf_protect
@ensure_csrf_cookie
def statement(request, app: str = None):
    if request.body:
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        """
        actor = AccountActorField(
            objectType = "Agent",
            account={
                "homePage": request.get_host(),
                "name": get_actor_name(request)
            },
        )
        """
        statement = {
            "actor": {
                "objectType": "Agent",
                "account": {
                    "homePage": request.get_host(),
                    "name": get_actor_name(request)
                }
            },
            "id": str(uuid.uuid4())
        }
        for key, value in body.items():
            statement[key] = value
        # send statement via celery
        send_xapi_statement_task.delay(statement)

        json_object = json.dumps(statement, indent=2)
        return JsonResponse(json_object, safe=False)
    raise SuspiciousOperation("Invalid video id")


def get_actor_name(request):
    if request.user.is_authenticated :
        if XAPI_ANONYMIZE_ACTOR:
            name = request.user.owner.hashkey
        else:
            name = str(request.user)
    else:
        if not request.session or not request.session.session_key:
            request.session.save()
        name = request.session.session_key
    return name
