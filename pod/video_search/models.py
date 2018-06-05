from django.db import models
from django.conf import settings
from pod.video.models import Video

ES_URL = getattr(settings, 'ES_URL', ['http://127.0.0.1:9200/'])

# Create your models here.

@receiver(post_save, sender=Video)  # instead of @receiver(post_save, sender=Rebel) #do it  with contributor, overlay, chapter etc.
def update_video_index(sender, instance=None, created=False, **kwargs):
        es = Elasticsearch(ES_URL)
        if instance.is_draft == False:
            res = es.index(index="pod", doc_type='pod', id=instance.id,
                           body=instance.get_json_to_index(), refresh=True)
        else:
            delete = es.delete(
                index="pod", doc_type='pod', id=pod.id, refresh=True, ignore=[400, 404])