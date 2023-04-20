from pod.video.models import Notes, AdvancedNotes
from pod.chapter.models import Chapter
from pod.completion.models import Overlay, Track


def clean_database(video_id):
    """Clean database when cutting video"""
    # Delete chapter(s)
    if Chapter.objects.filter(video=video_id).exists():
        chapter = Chapter.objects.filter(video=video_id)
        chapter.delete()

    # Delete advanced note(s)
    if AdvancedNotes.objects.filter(video=video_id).exists():
        advanced_notes = AdvancedNotes.objects.filter(video=video_id)
        advanced_notes.delete()

    # Delete note(s)
    if Notes.objects.filter(video=video_id).exists():
        notes = Notes.objects.filter(video=video_id)
        notes.delete()

    # Delete superposition
    if Overlay.objects.filter(video=video_id).exists():
        overlay = Overlay.objects.filter(video=video_id)
        overlay.delete()

    # Delete subtitles
    if Track.objects.filter(video=video_id).exists():
        overlay = Track.objects.filter(video=video_id)
        overlay.delete()
