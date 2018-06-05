from django.conf import settings
from pod.video.models import Video
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import TransportError

import json
import logging

logger = logging.getLogger(__name__)

ES_URL = getattr(settings, 'ES_URL', ['http://127.0.0.1:9200/'])


def index_es(video):
    es = Elasticsearch(ES_URL)
    print(video.id)
    try:
        res = es.index(index="pod", doc_type='pod', id=video.id,
                       body=video.get_json_to_index(), refresh=True)
        logger.info(res)
        return res
    except TransportError as e:
        logger.error("An error occured during index creation: %s-%s : %s" %
                     (e.status_code, e.error, e.info['error']['reason']))


def delete_es(video):
    es = Elasticsearch(ES_URL)
    try:
        delete = es.delete(
            index="pod", doc_type='pod', id=video.id, refresh=True, ignore=[400, 404])
        logger.info(delete)
        return delete
    except TransportError as e:
        logger.error("An error occured during index video %s deletion: %s-%s : %s" %
                     (video.id, e.status_code, e.error, e.info['error']['reason']))

def create_index_es():
    es = Elasticsearch(ES_URL)
    json_data = open('pod/video_search/search_template.json')
    es_template = json.load(json_data)
    try:
        create = es.indices.create(
            index='pod', body=es_template)  # ignore=[400, 404]
        logger.info(create)
        return create
    except TransportError as e:
        # (400, u'IndexAlreadyExistsException[[pod] already exists]')
        if e.status_code == 400:
            logger.error("Pod index already exists: %s" % e.error)
        else:
            logger.error("An error occured during index creation: %s-%s : %s" %
                  (e.status_code, e.error, e.info['error']['reason']))

def delete_index_es():
    es = Elasticsearch(ES_URL)
    try:
        delete = es.indices.delete(index='pod')
        logger.info(delete)
        return delete
    except TransportError as e:
        logger.error("An error occured during index video deletion: %s-%s : %s" %
                     (e.status_code, e.error, e.info['error']['reason']))