"""Esup-Pod - tests for the BBB recording and playback settings."""

from http import HTTPStatus
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlsplit

from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.test import TestCase, override_settings
from django.urls import reverse

from pod.authentication.models import AccessGroup
from pod.meeting.models import InternalRecording, Meeting


@override_settings(MEETING_DISABLE_RECORD=False)
class MeetingRecordingSettingsTest(TestCase):
    """Verify recording policy when a moderator starts a BBB session."""

    @classmethod
    def setUpTestData(cls):
        site = Site.objects.get_current()
        cls.student = User.objects.create(username="student")
        cls.teacher = User.objects.create(username="teacher")
        cls.teacher.owner.affiliation = "faculty"
        cls.teacher.owner.save(update_fields=["affiliation"])

        cls.student_meeting = Meeting.objects.create(
            name="Student meeting",
            site=site,
            owner=cls.student,
            auto_start_recording=True,
        )
        cls.student_meeting.additional_owners.add(cls.teacher)
        cls.personal_room = Meeting.objects.create(
            name="Student room", site=site, owner=cls.student, is_personal=True
        )
        cls.teacher_meeting = Meeting.objects.create(
            name="Teacher meeting",
            site=site,
            owner=cls.teacher,
            attendee_password="viewer-password",
        )
        cls.teacher_meeting.additional_owners.add(cls.student)

    def start_meeting(self, meeting, moderator):
        """Start a session through the join view and capture the BBB parameters."""
        self.client.force_login(moderator)
        url = reverse("meeting:join", args=[meeting.meeting_id])
        bbb_response = Mock(
            status_code=HTTPStatus.OK,
            content=b"<response><returncode>SUCCESS</returncode></response>",
        )
        with patch.object(
            Meeting, "get_create_response", return_value=bbb_response
        ) as send:
            self.assertEqual(self.client.get(url).status_code, HTTPStatus.FOUND)
        send.assert_called_once()
        return parse_qs(urlsplit(send.call_args.args[0]).query)

    def assert_recording_disabled(self, params):
        """Check that BBB receives all three recording options as false."""
        for key in ("record", "autoStartRecording", "allowStartStopRecording"):
            self.assertEqual(params[key], ["false"])
        self.assertNotIn("meta_bbb-recording-ready-url", params)

    @override_settings(MEETING_DISABLE_RECORD_FOR_STUDENTS=True)
    def test_student_rooms_use_the_owners_affiliation(self):
        """Block student recording even when a teacher starts the session."""
        self.assert_recording_disabled(
            self.start_meeting(self.student_meeting, self.teacher)
        )
        self.assert_recording_disabled(
            self.start_meeting(self.personal_room, self.student)
        )
        self.student_meeting.refresh_from_db()
        self.assertTrue(self.student_meeting.record)
        self.assertTrue(self.student_meeting.auto_start_recording)

        params = self.start_meeting(self.teacher_meeting, self.student)
        self.assertEqual(params["record"][0].lower(), "true")
        self.assertIn("meta_bbb-recording-ready-url", params)

    @override_settings(MEETING_DISABLE_RECORD=True)
    def test_global_disable_overrides_recording_preference(self):
        """Block teacher recording under the global setting."""
        self.assert_recording_disabled(
            self.start_meeting(self.teacher_meeting, self.teacher)
        )
        self.teacher_meeting.refresh_from_db()
        self.assertTrue(self.teacher_meeting.record)

    @override_settings(MEETING_DISABLE_RECORD_FOR_STUDENTS=True)
    def test_student_coowner_keeps_moderation_without_recording_control(self):
        """Restrict the student on join while allowing the teacher to record."""
        self.start_meeting(self.teacher_meeting, self.teacher)
        url = reverse("meeting:join", args=[self.teacher_meeting.meeting_id])
        permission = "userdata-bbb_record_permission"
        for user, expected in ((self.student, ["false"]), (self.teacher, None)):
            with self.subTest(user=user):
                self.client.force_login(user)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)
                params = parse_qs(urlsplit(response["Location"]).query)
                self.assertEqual(params["role"], ["MODERATOR"])
                self.assertEqual(params.get(permission), expected)

        self.client.force_login(self.student)
        with self.settings(MEETING_DISABLE_RECORD_FOR_STUDENTS=False):
            response = self.client.get(url)
            self.assertEqual(response.status_code, HTTPStatus.FOUND)
            self.assertNotIn(permission, parse_qs(urlsplit(response["Location"]).query))

    @override_settings(MEETING_DISABLE_RECORD_FOR_STUDENTS=True)
    def test_student_viewer_receives_restriction_on_either_join_path(self):
        """Set the recording permission even if the student joins as a viewer."""
        meeting = self.teacher_meeting
        meeting.additional_owners.remove(self.student)
        self.start_meeting(meeting, self.teacher)
        self.client.force_login(self.student)
        join_url = reverse("meeting:join", args=[meeting.meeting_id])
        direct_url = reverse(
            "meeting:join", args=[meeting.meeting_id, meeting.get_hashkey()]
        )
        for response in (
            self.client.get(direct_url),
            self.client.post(join_url, {"password": meeting.attendee_password}),
        ):
            self.assertEqual(response.status_code, HTTPStatus.FOUND)
            params = parse_qs(urlsplit(response["Location"]).query)
            self.assertEqual(params["role"], ["VIEWER"])
            self.assertEqual(params["userdata-bbb_record_permission"], ["false"])

    @override_settings(MEETING_DISABLE_RECORD_FOR_STUDENTS=True)
    def test_recording_options_use_the_owners_affiliation(self):
        """Hide the recording fields when a teacher edits a student meeting."""
        self.client.force_login(self.teacher)
        url = reverse("meeting:edit", args=[self.student_meeting.meeting_id])
        form = self.client.get(url).context["form"]
        for field in ("record", "auto_start_recording", "allow_start_stop_recording"):
            self.assertNotIn(field, form.fields)
        self.assertFalse(
            any(options.get("id") == "recording_fields" for _, options in form.fieldsets)
        )

        url = reverse("meeting:edit", args=[self.teacher_meeting.meeting_id])
        self.assertIn("record", self.client.get(url).context["form"].fields)

    @override_settings(MEETING_DISABLE_RECORD_FOR_STUDENTS=True)
    def test_student_coowner_cannot_change_recording_options(self):
        """Preserve the teacher's settings when a student submits the meeting form."""
        meeting = self.teacher_meeting
        meeting.record = False
        meeting.auto_start_recording = False
        meeting.allow_start_stop_recording = False
        meeting.save()
        self.client.force_login(self.student)
        url = reverse("meeting:edit", args=[meeting.meeting_id])
        fields = ("record", "auto_start_recording", "allow_start_stop_recording")
        form = self.client.get(url).context["form"]
        for field in fields:
            self.assertNotIn(field, form.fields)

        response = self.client.post(
            url,
            {
                "name": meeting.name,
                "attendee_password": meeting.attendee_password,
                "start": "2026-11-26",
                "start_time": "14:00:00",
                "expected_duration": "2",
                "frequency": "1",
                "monthly_type": "date_day",
                "max_participants": "100",
                "voice_bridge": "70042",
                "welcome_text": "Updated welcome",
                **dict.fromkeys(fields, "on"),
            },
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        meeting.refresh_from_db()
        self.assertEqual(meeting.welcome_text, "Updated welcome")
        for field in fields:
            self.assertFalse(getattr(meeting, field))


class MeetingRecordingAccessTest(TestCase):
    """Verify recording access for students and meeting owners."""

    @classmethod
    def setUpTestData(cls):
        cls.organizer = User.objects.create(username="organizer")
        cls.student = User.objects.create(username="student")
        cls.meeting = Meeting.objects.create(
            name="Course", owner=cls.organizer, site=Site.objects.get_current()
        )

    def setUp(self):
        self.client.force_login(self.student)
        self.list_url = reverse(
            "meeting:internal_recordings", args=[self.meeting.meeting_id]
        )
        self.recording = {
            "recordID": "published-record",
            "meetingID": self.meeting.meeting_id,
            "name": "Published replay",
            "state": "published",
            "startTime": "1760000000000",
            "endTime": "1760000100000",
            "playback": {
                "format": {"type": "video", "url": "https://bbb.example.test/video"}
            },
        }
        self.detail_url = reverse(
            "meeting:internal_recording",
            args=[self.meeting.meeting_id, self.recording["recordID"]],
        )

    def test_student_owners_and_coowners_can_access_recordings_by_default(self):
        """Apply the usual meeting permissions when student recording is enabled."""
        self.meeting.additional_owners.add(self.student)
        bbb_response = {"recordings": {"a": self.recording}}
        with (
            patch.object(Meeting, "get_recordings", return_value=bbb_response),
            patch.object(Meeting, "get_recording", return_value=bbb_response),
        ):
            for user, can_delete in ((self.organizer, True), (self.student, False)):
                with self.subTest(user=user):
                    self.client.force_login(user)
                    response = self.client.get(
                        reverse("meeting:my_meetings"), {"all": "true"}
                    )
                    self.assertContains(response, f'href="{self.list_url}"')
                    self.assertContains(
                        self.client.get(self.list_url), "Published replay"
                    )
                    response = self.client.get(
                        self.detail_url, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
                    )
                    self.assertEqual(response.status_code, HTTPStatus.OK)
                    self.assertTrue(response.json()["canUpload"])
                    self.assertEqual(response.json()["canDelete"], can_delete)

    def test_direct_playback_checks_meeting_and_exact_recording_id(self):
        """Reject mismatched or missing recordings from BBB."""
        self.client.force_login(self.organizer)
        for data in (
            {"a": dict(self.recording, meetingID="another-meeting")},
            {"a": dict(self.recording, recordID="published-record-with-suffix")},
            {},
        ):
            with (
                self.subTest(data=data),
                patch.object(Meeting, "get_recording", return_value={"recordings": data}),
            ):
                response = self.client.get(
                    self.detail_url, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
                )
                self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    @override_settings(RESTRICT_EDIT_VIDEO_ACCESS_TO_STAFF_ONLY=True)
    def test_recording_upload_uses_the_video_staff_restriction(self):
        """Hide and reject uploads for non-staff meeting owners and co-owners."""
        self.meeting.additional_owners.add(self.student)
        upload_url = reverse(
            "meeting:upload_internal_recording_to_pod",
            args=[self.meeting.meeting_id, self.recording["recordID"]],
        )
        bbb_response = {"recordings": {"a": self.recording}}
        with (
            patch.object(Meeting, "get_recordings", return_value=bbb_response),
            patch.object(Meeting, "get_recording", return_value=bbb_response),
            patch(
                "pod.meeting.views.upload_recording_to_pod", return_value=True
            ) as upload,
        ):
            for user in (self.organizer, self.student):
                with self.subTest(user=user):
                    self.client.force_login(user)
                    page = self.client.get(self.list_url)
                    self.assertContains(page, "Published replay")
                    self.assertNotContains(page, f'action="{upload_url}"')
                    detail = self.client.get(
                        self.detail_url, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
                    )
                    self.assertEqual(detail.status_code, HTTPStatus.OK)
                    self.assertFalse(detail.json()["canUpload"])
                    self.assertEqual(
                        self.client.post(
                            upload_url, {"recording_name": "Published replay"}
                        ).status_code,
                        HTTPStatus.FORBIDDEN,
                    )
            upload.assert_not_called()
            self.assertFalse(
                InternalRecording.objects.filter(meeting=self.meeting).exists()
            )

            self.organizer.is_staff = True
            self.organizer.save(update_fields=["is_staff"])
            self.client.force_login(self.organizer)
            self.assertContains(self.client.get(self.list_url), f'action="{upload_url}"')
            self.assertRedirects(
                self.client.post(upload_url, {"recording_name": "Published replay"}),
                self.list_url,
                fetch_redirect_response=False,
            )
            upload.assert_called_once()

    def test_meeting_group_membership_does_not_grant_recording_access(self):
        """Keep recording access reserved to users with meeting permissions."""
        group = AccessGroup.objects.create(code_name="course")
        self.meeting.restrict_access_to_groups.add(group)
        self.student.owner.accessgroup_set.add(group)
        with (
            patch.object(Meeting, "get_recordings") as get_recordings,
            patch.object(Meeting, "get_recording") as get_recording,
        ):
            self.assertEqual(
                self.client.get(self.list_url).status_code, HTTPStatus.FORBIDDEN
            )
            response = self.client.get(
                self.detail_url, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
            )
            self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        get_recordings.assert_not_called()
        get_recording.assert_not_called()

    @override_settings(MEETING_DISABLE_RECORD_FOR_STUDENTS=True)
    def test_disabled_recording_blocks_student_owners_and_coowners(self):
        """Hide the menu and deny recording requests even for a student organizer."""
        self.meeting.additional_owners.add(self.student)
        with (
            patch.object(Meeting, "get_recordings") as get_recordings,
            patch.object(Meeting, "get_recording") as get_recording,
            patch.object(Meeting, "delete_recording") as delete_recording,
            patch("pod.meeting.views.save_internal_recording") as save_recording,
        ):
            for user in (self.organizer, self.student):
                with self.subTest(user=user):
                    self.client.force_login(user)
                    response = self.client.get(
                        reverse("meeting:my_meetings"), {"all": "true"}
                    )
                    self.assertNotContains(response, f'href="{self.list_url}"')
                    self.assertEqual(
                        self.client.get(self.list_url).status_code, HTTPStatus.FORBIDDEN
                    )
                    response = self.client.get(
                        self.detail_url, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
                    )
                    self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
                    for action in (
                        "upload_internal_recording_to_pod",
                        "delete_internal_recording",
                    ):
                        url = reverse(
                            f"meeting:{action}",
                            args=[self.meeting.meeting_id, self.recording["recordID"]],
                        )
                        self.assertEqual(
                            self.client.post(url).status_code, HTTPStatus.FORBIDDEN
                        )
        get_recordings.assert_not_called()
        get_recording.assert_not_called()
        delete_recording.assert_not_called()
        save_recording.assert_not_called()

    def test_recording_notification_requires_access(self):
        """Send the recording link to an owner who can open it."""
        url = reverse("meeting:recording_ready")
        data = {
            "meeting_id": self.meeting.meeting_id,
            "record_id": self.recording["recordID"],
        }
        with (
            patch("pod.meeting.views.jwt.decode", return_value=data),
            patch("pod.meeting.views.send_email_recording_ready") as send_notification,
        ):
            with self.settings(MEETING_DISABLE_RECORD_FOR_STUDENTS=True):
                self.assertEqual(self.client.post(url).status_code, HTTPStatus.OK)
            send_notification.assert_not_called()
            self.assertEqual(self.client.post(url).status_code, HTTPStatus.OK)
            send_notification.assert_called_once_with(self.meeting)

    @override_settings(MEETING_DISABLE_RECORD_FOR_STUDENTS=True)
    def test_teacher_owner_can_access_recordings_when_student_recording_is_disabled(self):
        """Allow teachers to view their recordings under the student restriction."""
        self.organizer.owner.affiliation = "faculty"
        self.organizer.owner.save(update_fields=["affiliation"])
        self.client.force_login(self.organizer)
        with patch.object(
            Meeting, "get_recordings", return_value={"recordings": {"a": self.recording}}
        ):
            self.assertContains(self.client.get(self.list_url), "Published replay")
