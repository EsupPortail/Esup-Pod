"""Regression tests for thumbnail selection when editing a video."""

from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase

from pod.video.forms import VideoForm
from pod.video.models import Type, Video
from pod.video_encode_transcript.models import EncodingVideo

if getattr(settings, "USE_PODFILE", False):
    from pod.podfile.models import CustomImageModel
else:
    from pod.main.models import CustomImageModel


class VideoFormThumbnailTests(TestCase):
    """Preserve a generated thumbnail omitted by an earlier edit form."""

    fixtures = ["initial_data.json"]

    def setUp(self) -> None:
        """Create an editor and a video awaiting its generated thumbnail."""
        self.user = User.objects.create(username="thumbnail-editor", is_staff=True)
        self.video = Video.objects.create(
            title="Video being encoded",
            owner=self.user,
            video="thumbnail-editor.mp4",
            type=Type.objects.get(pk=1),
            encoding_in_progress=True,
        )

    def _form(self, **kwargs) -> VideoForm:
        return VideoForm(
            instance=self.video,
            current_user=self.user,
            is_staff=True,
            is_superuser=False,
            **kwargs,
        )

    def _form_data(self, form) -> dict:
        """Submit the editable values actually available when the form opened."""
        return {
            form.add_prefix(name): field.prepare_value(
                form.initial.get(name, field.initial)
            )
            for name, field in form.fields.items()
            if not isinstance(field, forms.FileField)
        }

    def _create_thumbnail(self, filename="generated-thumbnail.png") -> CustomImageModel:
        kwargs = {"file": filename}
        if getattr(settings, "USE_PODFILE", False):
            kwargs.update(
                folder=self.video.get_or_create_video_folder(),
                created_by=self.user,
            )
        return CustomImageModel.objects.create(**kwargs)

    def _finish_encoding(self) -> CustomImageModel:
        thumbnail = self._create_thumbnail()
        EncodingVideo.objects.create(
            video=self.video,
            rendition_id=1,
            source_file="encoded-thumbnail-editor.mp4",
        )
        Video.objects.filter(pk=self.video.pk).update(
            thumbnail=thumbnail,
            encoding_in_progress=False,
        )
        self.video.refresh_from_db()
        return thumbnail

    def test_form_opened_during_encoding_preserves_generated_thumbnail(self) -> None:
        """Finishing encoding before POST must not turn an omitted field into NULL."""
        initial_form = self._form()
        self.assertNotIn("thumbnail", initial_form.fields)
        data = self._form_data(initial_form)
        data["title"] = "Edited after encoding"
        thumbnail = self._finish_encoding()

        form = self._form(data=data)

        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.video.refresh_from_db()
        self.assertEqual(self.video.title, "Edited after encoding")
        self.assertEqual(self.video.thumbnail_id, thumbnail.pk)

    def test_prefixed_form_preserves_omitted_thumbnail(self) -> None:
        """Detect omitted thumbnails using the submitted field's full name."""
        initial_form = self._form(prefix="video")
        data = self._form_data(initial_form)
        thumbnail = self._finish_encoding()

        form = self._form(data=data, prefix="video")

        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.video.refresh_from_db()
        self.assertEqual(self.video.thumbnail_id, thumbnail.pk)

    def test_explicit_empty_thumbnail_clears_selection(self) -> None:
        """An explicit empty selection remains a request to remove the thumbnail."""
        self._finish_encoding()
        initial_form = self._form()
        self.assertIn("thumbnail", initial_form.fields)
        data = self._form_data(initial_form)
        data["thumbnail"] = ""

        form = self._form(data=data)

        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.video.refresh_from_db()
        self.assertIsNone(self.video.thumbnail_id)

    def test_explicit_thumbnail_changes_selection_on_prefixed_form(self) -> None:
        """A submitted thumbnail ID still replaces the existing selection."""
        self._finish_encoding()
        replacement = self._create_thumbnail("selected-thumbnail.png")
        data = self._form_data(self._form(prefix="video"))
        data["video-thumbnail"] = str(replacement.pk)

        form = self._form(data=data, prefix="video")

        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.video.refresh_from_db()
        self.assertEqual(self.video.thumbnail_id, replacement.pk)
