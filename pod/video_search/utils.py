from django.conf import settings
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import TransportError
from django.utils import translation

import json
import logging

logger = logging.getLogger(__name__)

ES_URL = getattr(settings, 'ES_URL', ['http://127.0.0.1:9200/'])
ES_INDEX = getattr(settings, 'ES_INDEX', 'pod')


def index_es(video):
    translation.activate(settings.LANGUAGE_CODE)
    es = Elasticsearch(ES_URL)
    if es.ping():
        try:
            data = video.get_json_to_index()
            if data != '{}':
                res = es.index(index=ES_INDEX,
                               doc_type='pod', id=video.id,
                               body=data, refresh=True)
                logger.info(res)
                return res
        except TransportError as e:
            logger.error("An error occured during index creation: %s-%s : %s" %
                         (e.status_code, e.error, e.info['error']['reason']))
    translation.deactivate()


def delete_es(video):
    es = Elasticsearch(ES_URL)
    if es.ping():
        try:
            delete = es.delete(
                index=ES_INDEX, doc_type='pod',
                id=video.id, refresh=True, ignore=[400, 404])
            logger.info(delete)
            return delete
        except TransportError as e:
            logger.error("An error occured during delete video : %s-%s : %s" %
                         (e.status_code, e.error, e.info['error']['reason']))


def create_index_es():
    es = Elasticsearch(ES_URL)
    json_data = open('pod/video_search/search_template.json')
    es_template = json.load(json_data)
    try:
        create = es.indices.create(
            index=ES_INDEX, body=es_template)  # ignore=[400, 404]
        logger.info(create)
        return create
    except TransportError as e:
        # (400, u'IndexAlreadyExistsException[[pod] already exists]')
        if e.status_code == 400:
            logger.error("Pod index already exists: %s" % e.error)
        else:
            logger.error("An error occured during"
                         " index creation: %s-%s : %s" %
                         (e.status_code, e.error, e.info['error']['reason']))


def delete_index_es():
    es = Elasticsearch(ES_URL)
    try:
        delete = es.indices.delete(index=ES_INDEX)
        logger.info(delete)
        return delete
    except TransportError as e:
        logger.error("An error occured during"
                     " index video deletion: %s-%s : %s" %
                     (e.status_code, e.error, e.info['error']['reason']))
