from .models import Recording


def add_comment(recording_id, comment):
    recording = Recording.objects.get(id=recording_id)
    recording.comment = "%s\n%s" % (recording.comment, comment)
    recording.save()
