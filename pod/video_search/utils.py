"""Esup-Pod Video Search utilities."""

from django.conf import settings
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import TransportError
from django.utils import translation

import json
import logging

logger = logging.getLogger(__name__)

DEBUG = getattr(settings, "DEBUG", True)

ES_URL = getattr(settings, "ES_URL", ["http://elasticsearch.localhost:9200/"])
ES_INDEX = getattr(settings, "ES_INDEX", "pod")
ES_TIMEOUT = getattr(settings, "ES_TIMEOUT", 30)
ES_MAX_RETRIES = getattr(settings, "ES_MAX_RETRIES", 10)
ES_VERSION = getattr(settings, "ES_VERSION", 8)
ES_OPTIONS = getattr(settings, "ES_OPTIONS", {})


def index_es(video):
    """Get ElasticSearch index."""
    translation.activate(settings.LANGUAGE_CODE)
    es = Elasticsearch(
        ES_URL,
        request_timeout=ES_TIMEOUT,
        max_retries=ES_MAX_RETRIES,
        retry_on_timeout=True,
        **ES_OPTIONS,
    )
    if es.ping():
        try:
            data = video.get_json_to_index()
            if data != "{}":
                res = es.index(index=ES_INDEX, id=video.id, body=data, refresh=True)
                if DEBUG:
                    logger.info(res)
                return res
        except TransportError as e:
            logger.error(
                "An error occured during index creation: %s-%s: %s"
                % (e.status_code, e.error, e.info)
            )
    else:
        logger.warning(
            "Elasticsearch did not responded to ping request at %s. Video %s not indexed."
            % (ES_URL, video.id)
        )
    translation.deactivate()


def delete_es(video_id):
    """Delete an Elasticsearch video entry by video id."""
    es = Elasticsearch(
        ES_URL,
        request_timeout=ES_TIMEOUT,
        max_retries=ES_MAX_RETRIES,
        retry_on_timeout=True,
        **ES_OPTIONS,
    )
    if es.ping():
        try:
            # Pass transport options to elasticsearch
            es = es.options(ignore_status=[400, 404])
            # Do the deletion
            delete = es.delete(index=ES_INDEX, id=video_id, refresh=True)
            if DEBUG:
                logger.info(delete)
            return delete
        except TransportError as e:
            logger.error(
                "An error occured during delete video: %s-%s: %s"
                % (e.status_code, e.error, e.info)
            )


def create_index_es():
    """Create ElasticSearch index."""
    es = Elasticsearch(
        ES_URL,
        request_timeout=ES_TIMEOUT,
        max_retries=ES_MAX_RETRIES,
        retry_on_timeout=True,
        **ES_OPTIONS,
    )
    template_file = "pod/video_search/search_template_fr.json"
    es_template = json.load(open(template_file))
    try:
        create = es.indices.create(index=ES_INDEX, body=es_template)  # ignore=[400, 404]
        logger.info(create)
        return create
    except TransportError as e:
        logger.error("An error occured during index creation: %s" % e.message)
        return False


def delete_index_es():
    """Delete ElasticSearch index."""
    es = Elasticsearch(
        ES_URL,
        request_timeout=ES_TIMEOUT,
        max_retries=ES_MAX_RETRIES,
        retry_on_timeout=True,
        **ES_OPTIONS,
    )
    try:
        delete = es.indices.delete(index=ES_INDEX)
        logger.info(delete)
        return delete
    except TransportError as e:
        logger.error("An error occured during index video deletion: %s" % e.message)
        return False
