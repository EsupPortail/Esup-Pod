from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.csrf import csrf_protect
from django.conf import settings
from django.core.exceptions import SuspiciousOperation
from .xapi_tasks import send_xapi_statement_task
import json
import uuid

from ralph.models.selector import ModelSelector
from ralph.models.validator import Validator

"""
To use Ralph :
pip3 install ralph-malph==3.3.0
from ralph.models.xapi.fields.actors import AccountActorField
from ralph.models.xapi.video.statements import VideoPlayed
actor = AccountActorField(
    objectType = "Agent",
    account={
        "homePage": request.get_host(),
        "name": get_actor_name(request)
    },
)
To test with celery :
(django_pod3) pod@pod:/.../podv3$
    celery -A pod.xapi.xapi_tasks -l INFO -Q xapi --concurrency 1 -n xapi
"""
XAPI_ANONYMIZE_ACTOR = getattr(settings, "XAPI_ANONYMIZE_ACTOR", True)
XAPI_LRS_URL = getattr(settings, "XAPI_LRS_URL", "")
XAPI_AUTHENTICATED_NAME = getattr(settings, "XAPI_AUTHENTICATED_NAME", "username")


@csrf_protect
@ensure_csrf_cookie
def statement(request, app: str = None):
    if request.body and app == "video":  # we develop only video statement
        body_unicode = request.body.decode("utf-8")
        body = json.loads(body_unicode)
        statement = {
            "actor": {
                "name": "%s" % get_actor_name(request),
                "mbox": "mailto:%s" % get_actor_mail(request),
            },
            "id": str(uuid.uuid4()),
        }
        for key, value in body.items():
            statement[key] = value
        if validate_statement(statement) and XAPI_LRS_URL != "":
            send_xapi_statement_task.delay(statement)
        return JsonResponse(statement, safe=False)
    raise SuspiciousOperation(
        "none post data was sent and app parameter has to be equals to video"
    )


def get_actor_mail(request):
    """Return a email adress for the actor's statement."""
    if request.user.is_authenticated:
        if XAPI_ANONYMIZE_ACTOR:
            dns_mail = request.user.email.split("@")[1]
            mail = "%s@%s" % (request.user.owner.hashkey, dns_mail)
        else:
            mail = request.user.email
    else:
        if not request.session or not request.session.session_key:
            request.session.save()
        mail = "%s@%s" % (request.session.session_key, request.get_host())
    return mail


def get_actor_name(request):
    """Return a name for the actor's statement."""
    if request.user.is_authenticated:
        if XAPI_ANONYMIZE_ACTOR:
            name = request.user.owner.hashkey
        else:
            name = get_authenticated_name(request.user)
    else:
        if not request.session or not request.session.session_key:
            request.session.save()
        name = request.session.session_key
    return name


def get_authenticated_name(user):
    """Return the authenticated actor's name value."""
    name = str(user)
    if XAPI_AUTHENTICATED_NAME == "uuid":
        name = uuid.uuid3(uuid.NAMESPACE_DNS, user.username)
    if XAPI_AUTHENTICATED_NAME == "username":
        name = str(user.username)
    if XAPI_AUTHENTICATED_NAME == "email":
        name = str(user.email)
    return name


def validate_statement(statement):
    """Validate the statement with Ralph Lib."""
    try:
        validator = Validator(ModelSelector("ralph.models.xapi"))
        """
        # Merge into one dict (compatible python3.7)
        request = {**{"actor": actor_dict}, **request_post}
        actor = AccountActorField(
            objectType = "Agent",
            account={
                "homePage": request.get_host(),
                "name": get_actor_name(request)
            },
        )
        print(actor)
        """
        # Get the corresponding xAPI model and validate request
        event = validator.get_first_valid_model(statement)
        if event:
            return True
        else:
            return False
    except Exception as e:
        print("Statement validation exception : \n%s" % e)
        return False
