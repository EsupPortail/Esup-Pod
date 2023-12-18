from django.conf import settings
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import TransportError
from django.utils import translation

import json
import logging

logger = logging.getLogger(__name__)

DEBUG = getattr(settings, "DEBUG", False)

ES_URL = getattr(settings, "ES_URL", ["http://127.0.0.1:9200/"])
ES_INDEX = getattr(settings, "ES_INDEX", "pod")
ES_TIMEOUT = getattr(settings, "ES_TIMEOUT", 30)
ES_MAX_RETRIES = getattr(settings, "ES_MAX_RETRIES", 10)
ES_VERSION = getattr(settings, "ES_VERSION", 6)
ES_OPTIONS = getattr(settings, "ES_OPTIONS", {})


def index_es(video):
    translation.activate(settings.LANGUAGE_CODE)
    es = Elasticsearch(
        ES_URL,
        timeout=ES_TIMEOUT,
        max_retries=ES_MAX_RETRIES,
        retry_on_timeout=True,
        **ES_OPTIONS,
    )
    if es.ping():
        try:
            data = video.get_json_to_index()
            if data != "{}":
                if ES_VERSION in [7, 8]:
                    res = es.index(index=ES_INDEX, id=video.id, body=data, refresh=True)
                else:
                    res = es.index(
                        index=ES_INDEX,
                        id=video.id,
                        doc_type="pod",
                        body=data,
                        refresh=True,
                    )
                if DEBUG:
                    logger.info(res)
                return res
        except TransportError as e:
            logger.error(
                "An error occured during index creation: %s-%s : %s"
                % (e.status_code, e.error, e.info)
            )
    translation.deactivate()


def delete_es(video):
    """Delete an Elasticsearch entry."""
    es = Elasticsearch(
        ES_URL,
        timeout=ES_TIMEOUT,
        max_retries=ES_MAX_RETRIES,
        retry_on_timeout=True,
        **ES_OPTIONS,
    )
    if es.ping():
        try:
            if ES_VERSION in [7, 8]:
                delete = es.delete(
                    index=ES_INDEX, id=video.id, refresh=True, ignore=[400, 404]
                )
            else:
                delete = es.delete(
                    index=ES_INDEX,
                    doc_type="pod",
                    id=video.id,
                    refresh=True,
                    ignore=[400, 404],
                )
            if DEBUG:
                logger.info(delete)
            return delete
        except TransportError as e:
            logger.error(
                "An error occured during delete video : %s-%s : %s"
                % (e.status_code, e.error, e.info)
            )


def create_index_es():
    es = Elasticsearch(
        ES_URL,
        timeout=ES_TIMEOUT,
        max_retries=ES_MAX_RETRIES,
        retry_on_timeout=True,
        **ES_OPTIONS,
    )
    if ES_VERSION in [7, 8]:
        template_file = "pod/video_search/search_template7.json"
    else:
        template_file = "pod/video_search/search_template.json"
    json_data = open(template_file)
    es_template = json.load(json_data)
    try:
        create = es.indices.create(index=ES_INDEX, body=es_template)  # ignore=[400, 404]
        logger.info(create)
        return create
    except TransportError as e:
        # (400, u'IndexAlreadyExistsException[[pod] already exists]')
        if e.status_code == 400:
            logger.error("ES responded with ERROR 400. Does pod index already exists?")

        logger.error(
            "An error occured during"
            " index creation: %s-%s : %s"
            % (e.status_code, e.error, e.info["error"]["reason"])
        )


def delete_index_es():
    es = Elasticsearch(
        ES_URL,
        timeout=ES_TIMEOUT,
        max_retries=ES_MAX_RETRIES,
        retry_on_timeout=True,
        **ES_OPTIONS,
    )
    try:
        delete = es.indices.delete(index=ES_INDEX)
        logger.info(delete)
        return delete
    except TransportError as e:
        logger.error(
            "An error occured during"
            " index video deletion: %s-%s : %s"
            % (e.status_code, e.error, e.info["error"]["reason"])
        )
