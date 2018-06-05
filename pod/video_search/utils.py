from django.conf import settings
from pod.video.models import Video

ES_URL = getattr(settings, 'ES_URL', ['http://127.0.0.1:9200/'])


def index_es(video):
    es = Elasticsearch(ES_URL)
    res = es.index(index="pod", doc_type='pod', id=video.id,
                   body=video.get_json_to_index(), refresh=True)
    return res


def delete_es(video):
    es = Elasticsearch(ES_URL)
    delete = es.delete(
        index="pod", doc_type='pod', id=video.id, refresh=True, ignore=[400, 404])
    return delete
