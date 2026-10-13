"""Esup-Pod regression tests for shared co-owner form widgets."""

from copy import deepcopy

from django import forms
from django.contrib.auth.models import User
from django.test import TestCase

from pod.meeting.forms import MeetingForm
from pod.playlist.forms import PlaylistForm


class AddOwnerWidgetTests(TestCase):
    """Exercise the co-owner fields used by every shared widget consumer."""

    form_classes = (
        PlaylistForm,
        MeetingForm,
    )

    @classmethod
    def setUpTestData(cls):
        """Create selected and unselected users for widget rendering."""
        cls.selected = User.objects.create_user("selected.coowner")
        cls.unselected = User.objects.create_user("unselected.coowner")

    def coowner_form(self, form_class, values):
        """Bind a consumer's actual field independently of unrelated required fields."""
        form = forms.Form(data={"additional_owners": values})
        form.fields["additional_owners"] = deepcopy(
            form_class.base_fields["additional_owners"]
        )
        return form

    def test_valid_selection_renders_only_selected_users(self):
        """Keep valid selections without fetching or rendering every possible user."""
        for form_class in self.form_classes:
            with self.subTest(form=form_class.__name__):
                form = self.coowner_form(form_class, [str(self.selected.pk)])
                self.assertTrue(form.is_valid(), form.errors)
                self.assertEqual(
                    list(form.cleaned_data["additional_owners"]), [self.selected]
                )
                with self.assertNumQueries(1):
                    html = str(form["additional_owners"])
                self.assertIn(self.selected.username, html)
                self.assertNotIn(self.unselected.username, html)

    def test_malformed_selection_renders_validation_errors(self):
        """Reject malformed identifiers without crashing while redisplaying a form."""
        for form_class in self.form_classes:
            for values in (["invalid-user"], [str(self.selected.pk), "invalid-user"]):
                with self.subTest(form=form_class.__name__, values=values):
                    form = self.coowner_form(form_class, values)
                    self.assertFalse(form.is_valid())
                    self.assertIn("additional_owners", form.errors)
                    html = form.as_p()
                    self.assertIn('name="additional_owners"', html)
                    if str(self.selected.pk) in values:
                        self.assertIn(self.selected.username, html)
                    self.assertNotIn("additional_owners", form.cleaned_data)

    def test_empty_selection_remains_valid(self):
        """Allow users to intentionally clear an optional co-owner selection."""
        for form_class in self.form_classes:
            with self.subTest(form=form_class.__name__):
                form = self.coowner_form(form_class, [])
                self.assertTrue(form.is_valid(), form.errors)
                self.assertEqual(list(form.cleaned_data["additional_owners"]), [])
                self.assertIn('name="additional_owners"', form.as_p())

    def test_out_of_queryset_selection_remains_invalid(self):
        """Do not bypass a consumer's queryset restrictions when rendering errors."""
        for form_class in self.form_classes:
            with self.subTest(form=form_class.__name__):
                form = self.coowner_form(form_class, [str(self.unselected.pk)])
                field = form.fields["additional_owners"]
                field.queryset = field.queryset.filter(pk=self.selected.pk)
                self.assertFalse(form.is_valid())
                self.assertIn("additional_owners", form.errors)
                self.assertNotIn(self.unselected.username, str(form["additional_owners"]))

    def test_explicit_choice_fields_keep_working(self):
        """Support an explicit primary key or another unique user field."""
        for field_name in ("pk", "username"):
            with self.subTest(field=field_name):
                value = str(getattr(self.selected, field_name))
                form = self.coowner_form(PlaylistForm, [value])
                form.fields["additional_owners"].to_field_name = field_name
                self.assertTrue(form.is_valid(), form.errors)
                html = str(form["additional_owners"])
                self.assertIn(self.selected.username, html)
                self.assertIn(f'value="{value}" selected', html)
