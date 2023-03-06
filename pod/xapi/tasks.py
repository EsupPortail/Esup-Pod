# xapi/tasks.py
from django.conf import settings
from celery import shared_task
import logging
import requests
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)

XAPI_LRS_URL = getattr(settings, "XAPI_LRS_URL", "")
XAPI_LRS_LOGIN = getattr(settings, "XAPI_LRS_LOGIN", "")
XAPI_LRS_PWD = getattr(settings, "XAPI_LRS_PWD", "")


@shared_task()
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
