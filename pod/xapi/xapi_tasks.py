# xapi/tasks.py
from celery import Celery
import requests
import logging
from requests.auth import HTTPBasicAuth

# call local settings directly
# no need to load pod application to send statement
try:
    from ..custom import settings_local
except ImportError:
    from .. import settings as settings_local

logger = logging.getLogger(__name__)

XAPI_LRS_URL = getattr(settings_local, "XAPI_LRS_URL", "")
XAPI_LRS_LOGIN = getattr(settings_local, "XAPI_LRS_LOGIN", "")
XAPI_LRS_PWD = getattr(settings_local, "XAPI_LRS_PWD", "")
XAPI_CELERY_BROKER_URL = getattr(settings_local, "XAPI_CELERY_BROKER_URL", "")

xapi_app = Celery("xapi_tasks", broker=XAPI_CELERY_BROKER_URL)
xapi_app.conf.task_routes = {"pod.xapi.xapi_tasks.*": {"queue": "xapi"}}


@xapi_app.task
def send_xapi_statement_task(statement):
    """Sends the xapi statement to the specified LRS."""
    x = requests.post(
        XAPI_LRS_URL, json=statement, auth=HTTPBasicAuth(XAPI_LRS_LOGIN, XAPI_LRS_PWD)
    )
    if x.status_code == 200:
        print(x.text)
        logger.info("statement id: %s" % x.text)
    else:
        logger.error("Error during sending statement: %s" % x.text)
