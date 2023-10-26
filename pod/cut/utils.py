from pod.video.models import Notes, AdvancedNotes
from pod.chapter.models import Chapter
from pod.completion.models import Overlay, Track


def clean_database(video_id):
    """Clean database when cutting video."""
    models = [Chapter, AdvancedNotes, Notes, Overlay, Track]
    for model_class in models:
        if model_class.objects.filter(video=video_id).exists():
            db = model_class.objects.filter(video=video_id)
            db.delete()
