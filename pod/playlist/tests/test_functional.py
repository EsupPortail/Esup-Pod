"""Esup-Pod playlist HTTP journeys, including authorization and persisted state.

Run with: python manage.py test pod.playlist.tests --settings=pod.main.test_settings
No playlist view, form, permission check or template is mocked.
"""

import hashlib
import json
from unittest.mock import patch

from bs4 import BeautifulSoup
from django.contrib.auth.models import AnonymousUser, Permission, User
from django.contrib.messages import get_messages
from django.db import connection
from django.test import Client, RequestFactory, TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from pod.authentication.models import AccessGroup
from pod.playlist.forms import PlaylistForm
from pod.playlist.models import Playlist, PlaylistContent
from pod.playlist.utils import (
    get_favorite_playlist_for_user,
    get_video_list_for_playlist,
    user_can_see_playlist_video,
)
from pod.video.models import Type, Video


class PlaylistFunctionalTests(TestCase):
    """Exercise playlists as an owner, co-owner, stranger and anonymous visitor."""

    fixtures = ["initial_data.json"]

    @classmethod
    def setUpTestData(cls):
        """Create users, videos and playlists covering each visibility setting."""
        cls.owner = User.objects.create_user("audit.owner")
        cls.coowner = User.objects.create_user("audit.coowner")
        cls.stranger = User.objects.create_user("audit.stranger")
        cls.admin = User.objects.create_user(
            "audit.admin", is_superuser=True, is_staff=True
        )
        cls.videos = [
            Video.objects.create(
                title=f"Audit video {number:02d}",
                owner=cls.owner,
                video=f"audit-{number}.mp4",
                is_draft=False,
                type=Type.objects.get(pk=1),
            )
            for number in range(1, 14)
        ]
        cls.public = Playlist.objects.create(
            name="Audit public", owner=cls.owner, visibility="public", promoted=True
        )
        cls.private = Playlist.objects.create(
            name="Audit private", owner=cls.owner, visibility="private"
        )
        cls.protected = Playlist.objects.create(
            name="Audit protected",
            owner=cls.owner,
            visibility="protected",
            password=hashlib.sha256(b"audit-password").hexdigest(),
        )
        for playlist in (cls.public, cls.private, cls.protected):
            playlist.additional_owners.add(cls.coowner)
            for video in cls.videos[:3]:
                PlaylistContent.objects.create(playlist=playlist, video=video)

    def setUp(self):
        """Log in as the owner and capture view errors as HTTP responses."""
        self.client.force_login(self.owner)
        self.client.raise_request_exception = False

    def url(self, action, playlist=None, **kwargs):
        """Build a playlist action URL with the supplied route parameters."""
        if playlist is not None:
            kwargs["slug"] = playlist.slug
        return reverse(f"playlist:{action}", kwargs=kwargs)

    def payload(self, playlist=None, **changes):
        """Build valid playlist form data with optional field overrides."""
        data = {
            "name": playlist.name if playlist else "Created through HTTP",
            "description": "Functional audit",
            "visibility": playlist.visibility if playlist else "private",
            "autoplay": "on",
            "password": "",
            "additional_owners": [self.coowner.pk],
        }
        data.update(changes)
        return data

    def contents(self, playlist):
        """Return persisted video identifiers and ranks in playlist order."""
        return list(
            PlaylistContent.objects.filter(playlist=playlist)
            .order_by("rank")
            .values_list("video_id", "rank")
        )

    def swap(self, playlist, client=None):
        """Request a swap of the first two test videos using the chosen client."""
        return (client or self.client).post(
            self.url("save-reorganisation", playlist),
            {"json-data": json.dumps({"0": [v.slug for v in self.videos[:2]]})},
        )

    def test_create_edit_delete_journey(self):
        """Verify that an owner can create, edit and delete a playlist through HTTP."""
        response = self.client.post(self.url("add"), self.payload())
        self.assertEqual(response.status_code, 302)
        playlist = Playlist.objects.get(name="Created through HTTP")
        self.assertEqual(playlist.owner, self.owner)
        self.assertIn(self.coowner, playlist.additional_owners.all())
        response = self.client.post(
            self.url("edit", playlist),
            self.payload(
                playlist, name="Renamed through HTTP", visibility="public", autoplay=""
            ),
        )
        self.assertEqual(response.status_code, 302)
        playlist.refresh_from_db()
        self.assertEqual(playlist.name, "Renamed through HTTP")
        self.assertFalse(playlist.autoplay)
        self.assertEqual(self.client.get(response.url).status_code, 200)
        response = self.client.post(self.url("remove", playlist), {"agree": "on"})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Playlist.objects.filter(pk=playlist.pk).exists())

    def test_partial_metadata_edit_preserves_coowners(self):
        """Keep co-owners when an authorized editor omits the selection field."""
        data = self.payload(self.private, description="Partial metadata edit")
        data.pop("additional_owners")
        for editor in (self.owner, self.coowner, self.admin):
            with self.subTest(editor=editor.username):
                self.private.additional_owners.set([self.coowner])
                self.client.force_login(editor)
                response = self.client.post(self.url("edit", self.private), data)
                self.assertEqual(response.status_code, 302)
                self.private.refresh_from_db()
                self.assertEqual(self.private.description, "Partial metadata edit")
                self.assertEqual(
                    list(self.private.additional_owners.all()), [self.coowner]
                )
                self.assertEqual(self.private.owner_id, self.owner.pk)

    def test_browser_form_can_explicitly_clear_all_coowners(self):
        """Submit the rendered presence marker when the multiple select is empty."""
        response = self.client.get(self.url("edit", self.private))
        form = BeautifulSoup(response.content, "html.parser")
        marker = form.select_one('input[type="hidden"][name="additional_owners_present"]')
        self.assertIsNotNone(marker)
        data = self.payload(self.private)
        data.pop("additional_owners")
        data[marker["name"]] = marker["value"]
        response = self.client.post(self.url("edit", self.private), data)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(self.private.additional_owners.exists())

    def test_explicit_coowner_selection_replaces_previous_selection(self):
        """Apply a supplied selection even when no presence marker is included."""
        response = self.client.post(
            self.url("edit", self.private),
            self.payload(self.private, additional_owners=[self.stranger.pk]),
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(list(self.private.additional_owners.all()), [self.stranger])

    def test_invalid_coowner_selection_preserves_existing_relations(self):
        """Keep current co-owners when submitted identifiers fail validation."""
        response = self.client.post(
            self.url("edit", self.private),
            self.payload(
                self.private,
                additional_owners=["invalid-user"],
                additional_owners_present="1",
            ),
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("additional_owners", response.context["form"].errors)
        self.assertEqual(list(self.private.additional_owners.all()), [self.coowner])

    def test_omitted_coowners_are_not_rewritten_when_saving_a_form(self):
        """Preserve co-owner changes made after validation of a partial form."""
        data = self.payload(self.private)
        data.pop("additional_owners")
        form = PlaylistForm(data=data, instance=self.private, user=self.owner)
        self.assertTrue(form.is_valid(), form.errors)
        self.private.additional_owners.add(self.stranger)
        form.save()
        self.assertCountEqual(
            self.private.additional_owners.all(), [self.coowner, self.stranger]
        )

    def test_prefixed_form_distinguishes_omitted_and_cleared_coowners(self):
        """Recognize the optional selection marker when the form has a prefix."""
        data = self.payload(self.private)
        data.pop("additional_owners")
        data = {f"playlist-{name}": value for name, value in data.items()}
        for clear in (False, True):
            with self.subTest(clear=clear):
                self.private.additional_owners.set([self.coowner])
                submitted = data.copy()
                if clear:
                    submitted["playlist-additional_owners_present"] = "1"
                form = PlaylistForm(
                    data=submitted,
                    instance=self.private,
                    user=self.owner,
                    prefix="playlist",
                )
                self.assertTrue(form.is_valid(), form.errors)
                form.save()
                self.assertEqual(
                    list(self.private.additional_owners.all()),
                    [] if clear else [self.coowner],
                )

    def test_creation_without_coowners_succeeds(self):
        """Create a playlist when a client omits the optional co-owner selection."""
        data = self.payload()
        data.pop("additional_owners")
        response = self.client.post(self.url("add"), data)
        self.assertEqual(response.status_code, 302)
        playlist = Playlist.objects.get(name="Created through HTTP")
        self.assertFalse(playlist.additional_owners.exists())

    def test_base_video_queryset_keeps_first_video_lookup_lightweight(self):
        """Fetch a thumbnail candidate without loading authorization relations."""
        with self.assertNumQueries(1):
            video = get_video_list_for_playlist(self.public).order_by("rank").first()
        self.assertEqual(video.pk, self.videos[0].pk)

    def test_playlist_thumbnail_fetches_only_its_first_video(self):
        """Keep the playlist card's first-video lookup to a single query."""
        with self.assertNumQueries(1):
            video = self.public.get_first_video()
        self.assertEqual(video.pk, self.videos[0].pk)

    def test_playlist_rendering_prefetches_video_access_relations(self):
        """Reuse loaded video rights on content pages, player sidebars and AJAX."""
        self.client.logout()
        video = self.videos[0]
        requests = [
            (self.url("content", self.public), {}),
            (
                reverse("video:video", kwargs={"slug": video.slug}),
                {"playlist": self.public.slug},
            ),
            (
                reverse("enrichment:video_enrichment", kwargs={"slug": video.slug}),
                {"playlist": self.public.slug},
            ),
            (
                reverse(
                    "playlist:get-video",
                    kwargs={"video_slug": video.slug, "playlist_slug": self.public.slug},
                ),
                {},
            ),
        ]
        for url, params in requests:
            with self.subTest(url=url):
                response = self.client.get(url, params)
                self.assertEqual(response.status_code, 200)
                videos = list(response.context["videos"])
                with self.assertNumQueries(0):
                    self.assertTrue(
                        all(
                            user_can_see_playlist_video(
                                response.wsgi_request, item, self.public
                            )
                            for item in videos
                        )
                    )

    def test_creation_rejects_empty_name(self):
        """Reject an empty title without creating a playlist."""
        before = Playlist.objects.count()
        response = self.client.post(self.url("add"), self.payload(name=""))
        self.assertEqual(response.status_code, 200)
        self.assertIn("name", response.context["form"].errors)
        self.assertEqual(Playlist.objects.count(), before)

    def test_protected_creation_requires_password(self):
        """Reject creation of a protected playlist without a password."""
        before = Playlist.objects.count()
        response = self.client.post(self.url("add"), self.payload(visibility="protected"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)
        self.assertEqual(Playlist.objects.count(), before)

    def test_protected_creation_and_password_start(self):
        """Verify password hashing and anonymous playback after password entry."""
        response = self.client.post(
            self.url("add"),
            self.payload(visibility="protected", password="audit-password"),
        )
        self.assertEqual(response.status_code, 302)
        playlist = Playlist.objects.get(name="Created through HTTP")
        self.assertEqual(playlist.password, self.protected.password)
        PlaylistContent.objects.create(playlist=playlist, video=self.videos[0])
        self.client.logout()
        response = self.client.get(self.url("start-playlist", playlist))
        self.assertContains(response, 'id="playlist_password_form"')
        response = self.client.post(
            self.url("start-playlist", playlist),
            {"password": "audit-password"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="card-playlistplayer"')

    def test_whitespace_password_cannot_create_a_protected_playlist(self):
        """Reject whitespace-only passwords without creating a protected playlist."""
        before = Playlist.objects.count()
        for password in ("   ", "\t\n", "\u00a0\u2003"):
            with self.subTest(password=repr(password)):
                response = self.client.post(
                    self.url("add"),
                    self.payload(visibility="protected", password=password),
                )
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context["form"].errors)
                self.assertEqual(Playlist.objects.count(), before)

    def test_form_save_hashes_normalized_password(self):
        """Persist a digest from validated form data without relying on the view."""
        form = PlaylistForm(
            data=self.payload(visibility="protected", password="  audit-password\t"),
            user=self.owner,
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(
            form.save(commit=False).password,
            hashlib.sha256(b"audit-password").hexdigest(),
        )

    def test_group_permission_does_not_grant_private_playlist_access(self):
        """Keep playlist privacy separate from the video's group permissions."""
        group = AccessGroup.objects.create(code_name="audit-private")
        self.stranger.owner.accessgroup_set.add(group)
        self.videos[0].restrict_access_to_groups.add(group)
        request = RequestFactory().get("/")
        request.user = self.stranger
        self.assertFalse(
            user_can_see_playlist_video(request, self.videos[0], self.private)
        )
        self.client.force_login(self.stranger)
        response = self.client.get(
            reverse("video:video", kwargs={"slug": self.videos[0].slug}),
            {"playlist": self.private.slug},
        )
        self.assertEqual(response.status_code, 403)

    def test_whitespace_password_preserves_protected_playlist_access(self):
        """Keep the existing password when an edit submits only whitespace."""
        response = self.client.post(
            self.url("edit", self.protected),
            self.payload(self.protected, password=" \t\u00a0 "),
        )
        self.assertEqual(response.status_code, 302)
        self.protected.refresh_from_db()
        self.assertEqual(
            self.protected.password, hashlib.sha256(b"audit-password").hexdigest()
        )
        self.client.logout()
        response = self.client.post(
            self.url("content", self.protected), {"password": "audit-password"}
        )
        self.assertContains(response, self.videos[0].title)

    def test_password_normalization_matches_creation_editing_and_unlocking(self):
        """Hash normalized input once and apply the same normalization on access."""
        for playlist in (None, self.protected):
            with self.subTest(editing=playlist is not None):
                self.client.force_login(self.owner)
                response = self.client.post(
                    self.url("edit", playlist) if playlist else self.url("add"),
                    self.payload(
                        playlist, visibility="protected", password="  spaced secret\t "
                    ),
                )
                self.assertEqual(response.status_code, 302)
                saved = (
                    Playlist.objects.get(pk=playlist.pk)
                    if playlist
                    else Playlist.objects.get(name="Created through HTTP")
                )
                self.assertEqual(
                    saved.password, hashlib.sha256(b"spaced secret").hexdigest()
                )
                self.client.logout()
                response = self.client.post(
                    self.url("content", saved), {"password": "\tspaced secret  "}
                )
                self.assertTemplateUsed(response, "playlist/playlist.html")

    def test_whitespace_cannot_protect_a_playlist_without_an_existing_password(self):
        """Reject a switch to protected visibility without a usable password."""
        response = self.client.post(
            self.url("edit", self.private),
            self.payload(self.private, visibility="protected", password="   "),
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)
        self.private.refresh_from_db()
        self.assertEqual(self.private.visibility, "private")

    def assert_video_access_through_playlist(self, allowed):
        """Check start, player variants and AJAX access for the current visitor."""
        video = self.videos[0]
        response = self.client.get(self.url("start-playlist", self.public), follow=True)
        if allowed:
            self.assertContains(response, 'id="card-playlistplayer"')
        else:
            self.assertNotContains(response, 'id="card-playlistplayer"')
        for view in ("video:video", "enrichment:video_enrichment"):
            for embedded in ("", "true"):
                with self.subTest(view=view, embedded=embedded):
                    response = self.client.get(
                        reverse(view, kwargs={"slug": video.slug}),
                        {"playlist": self.public.slug, "is_iframe": embedded},
                    )
                    self.assertEqual(response.status_code, 200 if allowed else 403)
        response = self.client.get(
            reverse(
                "playlist:get-video",
                kwargs={"video_slug": video.slug, "playlist_slug": self.public.slug},
            )
        )
        self.assertEqual(response.status_code, 200 if allowed else 403)

    def test_allowed_group_member_can_play_restricted_playlist_videos(self):
        """Honor video group membership across all playlist playback routes."""
        group = AccessGroup.objects.create(code_name="audit-allowed")
        self.stranger.owner.accessgroup_set.add(group)
        for video in self.videos[:3]:
            video.restrict_access_to_groups.add(group)
        self.client.force_login(self.stranger)
        for restricted in (False, True):
            with self.subTest(restricted=restricted):
                Video.objects.filter(pk__in=[v.pk for v in self.videos[:3]]).update(
                    is_restricted=restricted
                )
                self.assert_video_access_through_playlist(True)

    def test_recorder_permission_allows_group_restricted_playlist_videos(self):
        """Honor the recorder grant already supported by the standalone player."""
        group = AccessGroup.objects.create(code_name="audit-recorder")
        self.videos[0].restrict_access_to_groups.add(group)
        self.stranger.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="recorder", codename="add_recording"
            )
        )
        self.client.force_login(self.stranger)
        self.assert_video_access_through_playlist(True)

    def test_group_restrictions_still_reject_unauthorized_visitors(self):
        """Reject outsiders and anonymous visitors across every playlist player."""
        group = AccessGroup.objects.create(code_name="audit-excluded")
        for video in self.videos[:3]:
            video.restrict_access_to_groups.add(group)
        self.client.force_login(self.stranger)
        self.assert_video_access_through_playlist(False)
        self.client.logout()
        self.assert_video_access_through_playlist(False)

    def test_authenticated_viewer_can_play_login_restricted_playlist_videos(self):
        """Honor a video's login-only restriction without requiring ownership."""
        Video.objects.filter(pk=self.videos[0].pk).update(is_restricted=True)
        self.client.force_login(self.stranger)
        self.assert_video_access_through_playlist(True)

    def test_video_editor_can_play_draft_playlist_videos(self):
        """Honor the video editing permission when a playlist contains a draft."""
        Video.objects.filter(pk=self.videos[0].pk).update(is_draft=True)
        self.stranger.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="video", codename="change_video"
            )
        )
        self.client.force_login(self.stranger)
        self.assert_video_access_through_playlist(True)

    def test_group_membership_does_not_bypass_video_passwords(self):
        """Keep video passwords protected even for an allowed group member."""
        group = AccessGroup.objects.create(code_name="audit-password")
        self.stranger.owner.accessgroup_set.add(group)
        for video in self.videos[:3]:
            video.restrict_access_to_groups.add(group)
        Video.objects.filter(pk__in=[v.pk for v in self.videos[:3]]).update(
            password="video-secret"
        )
        self.client.force_login(self.stranger)
        self.assert_video_access_through_playlist(False)

    def assert_playlist_access_query_count_is_constant(self, user):
        """Verify that loading and checking more playlist videos adds no queries."""
        for video in self.videos[3:]:
            PlaylistContent.objects.create(playlist=self.public, video=video)
        counts = []
        for size in (1, len(self.videos)):
            request = RequestFactory().get("/")
            request.user = User.objects.get(pk=user.pk) if user else AnonymousUser()
            with CaptureQueriesContext(connection) as queries:
                videos = get_video_list_for_playlist(
                    self.public, prefetch_access=True
                ).order_by("rank")[:size]
                allowed = [
                    user_can_see_playlist_video(request, video, self.public)
                    for video in videos
                ]
            self.assertEqual(allowed, [True] * size)
            counts.append(len(queries))
        self.assertEqual(counts[0], counts[1], counts)

    def test_public_playlist_access_queries_do_not_grow_per_video(self):
        """Avoid a query per card when checking unrestricted public videos."""
        self.assert_playlist_access_query_count_is_constant(None)

    def test_group_playlist_access_queries_do_not_grow_per_video(self):
        """Load video restrictions and viewer groups once per playlist traversal."""
        group = AccessGroup.objects.create(code_name="audit-query-count")
        self.stranger.owner.accessgroup_set.add(group)
        for video in self.videos:
            video.restrict_access_to_groups.add(group)
        self.assert_playlist_access_query_count_is_constant(self.stranger)

    def test_removed_group_membership_revokes_access_on_the_next_request(self):
        """Keep prefetched access groups local to the current request's user."""
        group = AccessGroup.objects.create(code_name="audit-revocation")
        self.videos[0].restrict_access_to_groups.add(group)
        self.stranger.owner.accessgroup_set.add(group)
        self.client.force_login(self.stranger)
        url = reverse(
            "playlist:get-video",
            kwargs={
                "video_slug": self.videos[0].slug,
                "playlist_slug": self.public.slug,
            },
        )
        self.assertEqual(self.client.get(url).status_code, 200)
        self.stranger.owner.accessgroup_set.remove(group)
        self.assertEqual(self.client.get(url).status_code, 403)

    def test_anonymous_mutation_redirects_to_login(self):
        """Redirect anonymous additions to login without changing playlist contents."""
        self.client.logout()
        before = self.contents(self.public)
        response = self.client.post(
            self.url("add-video", self.public, video_slug=self.videos[3].slug)
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("referrer=", response.url)
        self.assertEqual(self.contents(self.public), before)

    def test_video_mutations_reject_get_and_head(self):
        """Reject safe HTTP methods without changing playlist membership or ranks."""
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        before = self.contents(self.public)
        for action, video in (
            ("add-video", self.videos[3]),
            ("remove-video", self.videos[0]),
        ):
            for method in ("get", "head"):
                with self.subTest(action=action, method=method):
                    response = getattr(client, method)(
                        self.url(action, self.public, video_slug=video.slug)
                    )
                    self.assertEqual(response.status_code, 405)
                    self.assertEqual(response.headers["Allow"], "POST")
                    self.assertEqual(self.contents(self.public), before)

    def test_video_mutations_require_csrf(self):
        """Reject missing tokens, invalid tokens and requests from foreign origins."""
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        client.get(self.url("content", self.public))
        token = client.cookies["csrftoken"].value
        before = self.contents(self.public)
        for action, video in (
            ("add-video", self.videos[3]),
            ("remove-video", self.videos[0]),
        ):
            for headers in (
                {},
                {"HTTP_X_CSRFTOKEN": "invalid"},
                {"HTTP_X_CSRFTOKEN": token, "HTTP_ORIGIN": "https://other.example"},
            ):
                with self.subTest(action=action, headers=headers):
                    response = client.post(
                        self.url(action, self.public, video_slug=video.slug), **headers
                    )
                    self.assertEqual(response.status_code, 403)
                    self.assertEqual(self.contents(self.public), before)

    def test_playlist_controls_provide_valid_csrf_tokens(self):
        """Allow owners and co-owners to add from the modal and remove from cards."""
        video = self.videos[3]
        for user in (self.owner, self.coowner):
            with self.subTest(user=user.username):
                client = Client(enforce_csrf_checks=True)
                client.force_login(user)
                response = client.get(reverse("video:video", kwargs={"slug": video.slug}))
                button = BeautifulSoup(response.content, "html.parser").find(
                    id=f"{self.private.slug}-btn"
                )
                response = client.post(
                    button["href"] + "?json=true",
                    HTTP_X_CSRFTOKEN=button["data-csrf-token"],
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), {"state": "in-playlist"})
                self.assertTrue(
                    PlaylistContent.objects.filter(
                        playlist=self.private, video=video
                    ).exists()
                )
                url = self.url("content", self.private)
                response = client.get(url)
                button = BeautifulSoup(response.content, "html.parser").find(
                    id=f"remove-from-playlist-btn-{video.pk}"
                )
                response = client.post(
                    button["href"],
                    HTTP_X_CSRFTOKEN=button["data-csrf-token"],
                    HTTP_REFERER=url,
                    follow=True,
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.redirect_chain, [(url, 302)])
                self.assertFalse(
                    PlaylistContent.objects.filter(
                        playlist=self.private, video=video
                    ).exists()
                )

    def test_favorite_controls_support_csrf_cookie_and_session_settings(self):
        """Use rendered tokens for favorite additions and removals on every control."""
        video = self.videos[0]
        favorites = get_favorite_playlist_for_user(self.owner)
        player_url = reverse("video:video", kwargs={"slug": video.slug})
        content_url = self.url("content", self.public)
        for settings in ({}, {"CSRF_COOKIE_HTTPONLY": True}, {"CSRF_USE_SESSIONS": True}):
            with self.subTest(settings=settings), self.settings(**settings):
                client = Client(enforce_csrf_checks=True)
                client.force_login(self.owner)
                for url, selector, expected in (
                    (player_url, "#favorite-button", "in-playlist"),
                    (player_url, "#favorite-button", "out-playlist"),
                    (content_url, f"#favorite-btn-{video.pk}", "in-playlist"),
                    (
                        self.url("content", favorites),
                        f"#favorite-btn-{video.pk}",
                        "out-playlist",
                    ),
                ):
                    response = client.get(url)
                    button = BeautifulSoup(response.content, "html.parser").select_one(
                        selector
                    )
                    response = client.post(
                        button["href"] + "?json=true",
                        HTTP_X_CSRFTOKEN=button["data-csrf-token"],
                    )
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.json(), {"state": expected})
                    self.assertEqual(
                        PlaylistContent.objects.filter(
                            playlist=favorites, video=video
                        ).exists(),
                        expected == "in-playlist",
                    )

    def test_add_duplicate_remove_journey(self):
        """Verify JSON responses, duplicate prevention and video removal."""
        video = self.videos[3]
        add_url = self.url("add-video", self.public, video_slug=video.slug) + "?json=1"
        for _ in range(2):
            response = self.client.post(add_url)
            self.assertEqual(response.json(), {"state": "in-playlist"})
        self.assertEqual(
            PlaylistContent.objects.filter(playlist=self.public, video=video).count(), 1
        )
        response = self.client.post(
            self.url("remove-video", self.public, video_slug=video.slug) + "?json=1"
        )
        self.assertEqual(response.json(), {"state": "out-playlist"})
        self.assertFalse(
            PlaylistContent.objects.filter(playlist=self.public, video=video).exists()
        )

    def test_owner_reorganizes_and_persists_ranks(self):
        """Persist the requested rank swap when performed by the playlist owner."""
        response = self.swap(self.public)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            self.contents(self.public),
            [(self.videos[1].pk, 1), (self.videos[0].pk, 2), (self.videos[2].pk, 3)],
        )

    def test_display_order_matches_saved_ranks(self):
        """Display videos in their saved order after a rank swap."""
        self.swap(self.public)
        response = self.client.get(self.url("content", self.public))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [v.pk for v in response.context["videos"]],
            [self.videos[1].pk, self.videos[0].pk, self.videos[2].pk],
        )

    def test_start_uses_rank_one(self):
        """Start playback with the video at rank one."""
        response = self.client.get(self.url("start-playlist", self.public))
        self.assertRedirects(
            response,
            reverse("video:video", kwargs={"slug": self.videos[0].slug})
            + f"?playlist={self.public.slug}",
            fetch_redirect_response=False,
        )

    def test_empty_playlist_start_does_not_crash(self):
        """Handle an empty playlist without returning a server error."""
        empty = Playlist.objects.create(name="Audit empty", owner=self.owner)
        response = self.client.get(self.url("start-playlist", empty))
        self.assertLess(response.status_code, 500, self.response_error(response))

    @staticmethod
    def response_error(response):
        """Include the cause of an HTTP 500 without dumping the entire HTML page."""
        if response.exc_info:
            return f"{response.exc_info[0].__name__}: {response.exc_info[1]}"
        return f"HTTP {response.status_code}"

    def test_private_content_denied_to_anonymous(self):
        """Deny anonymous access to private playlist contents."""
        self.client.logout()
        self.assertEqual(
            self.client.get(self.url("content", self.private)).status_code, 403
        )

    def test_private_content_denied_to_stranger(self):
        """Deny private playlist access to an unrelated authenticated user."""
        self.client.force_login(self.stranger)
        self.assertEqual(
            self.client.get(self.url("content", self.private)).status_code, 403
        )

    def test_private_content_and_start_available_to_coowner(self):
        """Allow a co-owner to browse and start a shared private playlist."""
        self.client.force_login(self.coowner)
        self.assertEqual(
            self.client.get(self.url("content", self.private)).status_code, 200
        )
        response = self.client.get(self.url("start-playlist", self.private), follow=True)
        self.assertContains(response, 'id="card-playlistplayer"')

    def test_protected_content_requires_password_for_anonymous(self):
        """Show anonymous visitors a password form without revealing video titles."""
        self.client.logout()
        response = self.client.get(self.url("content", self.protected))
        self.assertContains(response, 'id="playlist_password_form"')
        self.assertNotContains(response, self.videos[0].title)

    def test_protected_content_requires_password_for_stranger(self):
        """Require a playlist password even when an unrelated visitor is logged in."""
        self.client.force_login(self.stranger)
        response = self.client.get(self.url("content", self.protected))
        self.assertContains(response, 'id="playlist_password_form"')

    def test_protected_content_rejects_wrong_password(self):
        """Keep protected video titles hidden after an incorrect password."""
        self.client.force_login(self.stranger)
        response = self.client.post(
            self.url("content", self.protected), {"password": "wrong"}, follow=True
        )
        self.assertNotContains(response, self.videos[0].title)

    def test_protected_content_accepts_correct_password(self):
        """Reveal playlist contents after a visitor supplies the correct password."""
        self.client.force_login(self.stranger)
        response = self.client.post(
            self.url("content", self.protected), {"password": "audit-password"}
        )
        self.assertContains(response, self.videos[0].title)

    def test_legacy_password_spaces_are_preserved_on_edit_and_unlock(self):
        """Keep raw legacy password hashes usable after an unrelated metadata edit."""
        for password in (" legacy secret ", "\tlegacy secret\u00a0", "   "):
            with self.subTest(password=repr(password)):
                digest = hashlib.sha256(password.encode()).hexdigest()
                self.protected.password = digest
                self.protected.save()
                response = self.client.post(
                    self.url("edit", self.protected), self.payload(self.protected)
                )
                self.assertEqual(response.status_code, 302)
                self.protected.refresh_from_db()
                self.assertEqual(self.protected.password, digest)
                visitor = Client()
                response = visitor.post(
                    self.url("content", self.protected), {"password": password}
                )
                self.assertContains(response, self.videos[0].title)
                self.assertEqual(
                    visitor.session[f"playlist_access_{self.protected.pk}"],
                    self.protected.get_session_auth_hash(),
                )
                self.protected.refresh_from_db()
                self.assertEqual(self.protected.password, digest)

    def test_legacy_password_fallback_does_not_accept_inexact_passwords(self):
        """Require the original spaces for legacy hashes and reject incorrect input."""
        self.protected.password = hashlib.sha256(b" legacy secret ").hexdigest()
        self.protected.save()
        for password in (
            "legacy secret",
            " legacy secret",
            "legacy secret ",
            "wrong",
            " ",
            "",
        ):
            with self.subTest(password=repr(password)):
                visitor = Client()
                response = visitor.post(
                    self.url("content", self.protected), {"password": password}
                )
                self.assertContains(response, 'id="playlist_password_form"')
                self.assertNotContains(response, self.videos[0].title)
                self.assertNotIn(f"playlist_access_{self.protected.pk}", visitor.session)

    def test_legacy_password_unlocks_playlist_start_and_player_variants(self):
        """Accept legacy passwords through each route using the shared password gate."""
        password = " legacy secret "
        self.protected.password = hashlib.sha256(password.encode()).hexdigest()
        self.protected.save()
        urls = [self.url("start-playlist", self.protected)]
        for view_name in ("video:video", "enrichment:video_enrichment"):
            for embedded in ("", "true"):
                url = reverse(view_name, kwargs={"slug": self.videos[0].slug})
                urls.append(f"{url}?playlist={self.protected.slug}&is_iframe={embedded}")
        for url in urls:
            with self.subTest(url=url):
                visitor = Client()
                response = visitor.post(url, {"password": password}, follow=True)
                self.assertEqual(response.status_code, 200)
                self.assertNotContains(response, 'id="playlist_password_form"')
                self.assertEqual(
                    visitor.session[f"playlist_access_{self.protected.pk}"],
                    self.protected.get_session_auth_hash(),
                )

    def test_direct_player_requires_protected_playlist_password(self):
        """Prevent direct player URLs from bypassing playlist password protection."""
        self.client.logout()
        response = self.client.get(
            reverse("video:video", kwargs={"slug": self.videos[0].slug}),
            {"playlist": self.protected.slug},
        )
        self.assertNotContains(response, 'id="card-playlistplayer"')

    def test_coowner_edit_preserves_original_owner(self):
        """Save a co-owner's edits without transferring the playlist's ownership."""
        self.client.force_login(self.coowner)
        response = self.client.post(
            self.url("edit", self.private),
            self.payload(self.private, description="Edited by co-owner"),
        )
        self.assertEqual(response.status_code, 302)
        self.private.refresh_from_db()
        self.assertEqual(self.private.description, "Edited by co-owner")
        self.assertEqual(self.private.owner_id, self.owner.pk)

    def test_admin_edit_preserves_original_owner(self):
        """Keep the original owner when an administrator edits a playlist."""
        self.client.force_login(self.admin)
        response = self.client.post(
            self.url("edit", self.private), self.payload(self.private)
        )
        self.assertEqual(response.status_code, 302)
        self.private.refresh_from_db()
        self.assertEqual(self.private.owner_id, self.owner.pk)

    def test_stranger_cannot_edit_by_post(self):
        """Preserve playlist metadata after an unauthorized edit request."""
        self.client.force_login(self.stranger)
        self.client.post(
            self.url("edit", self.private),
            self.payload(self.private, name="Changed by stranger"),
        )
        self.private.refresh_from_db()
        self.assertEqual(
            (self.private.name, self.private.owner_id), ("Audit private", self.owner.pk)
        )

    def test_stranger_cannot_add_video(self):
        """Preserve playlist contents after an unauthorized video addition."""
        self.client.force_login(self.stranger)
        before = self.contents(self.private)
        response = self.client.post(
            self.url("add-video", self.private, video_slug=self.videos[3].slug)
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.contents(self.private), before)

    def test_stranger_cannot_remove_video(self):
        """Preserve playlist contents after an unauthorized video removal."""
        self.client.force_login(self.stranger)
        before = self.contents(self.private)
        response = self.client.post(
            self.url("remove-video", self.private, video_slug=self.videos[0].slug)
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.contents(self.private), before)

    def test_stranger_cannot_reorganize(self):
        """Preserve video ranks after an unauthorized reorganization request."""
        self.client.force_login(self.stranger)
        before = self.contents(self.private)
        self.swap(self.private)
        self.assertEqual(self.contents(self.private), before)

    def test_stranger_cannot_delete_playlist(self):
        """Keep a playlist after an unrelated user requests its deletion."""
        self.client.force_login(self.stranger)
        self.client.post(self.url("remove", self.private), {"agree": "on"})
        self.assertTrue(Playlist.objects.filter(pk=self.private.pk).exists())

    def test_failed_deletion_does_not_claim_success(self):
        """Avoid a success message when a co-owner cannot delete a playlist."""
        self.client.force_login(self.coowner)
        response = self.client.post(self.url("remove", self.private), {"agree": "on"})
        exists = Playlist.objects.filter(pk=self.private.pk).exists()
        messages = [str(m) for m in get_messages(response.wsgi_request)]
        self.assertFalse(
            exists and "The playlist has been deleted." in messages, messages
        )

    def test_favorites_expose_reorganize_button(self):
        """Show the reorganization control on the owner's favorites page."""
        favorites = get_favorite_playlist_for_user(self.owner)
        for video in self.videos[:2]:
            PlaylistContent.objects.create(playlist=favorites, video=video)
        response = self.client.get(self.url("content", favorites))
        self.assertContains(response, 'id="reorganize-button"')

    def test_favorites_load_their_removal_script(self):
        """Load the shared playlist utilities and favorites removal script."""
        response = self.client.get(
            self.url("content", get_favorite_playlist_for_user(self.owner))
        )
        self.assertContains(response, "playlist/js/video-favorites-remove-card.js")
        self.assertContains(response, "playlist/js/utils-playlist.js")

    def test_favorites_cannot_be_renamed(self):
        """Preserve the system favorites name after an attempted edit."""
        favorites = get_favorite_playlist_for_user(self.owner)
        original_name = favorites.name
        self.client.post(
            self.url("edit", favorites), self.payload(favorites, name="Renamed favorites")
        )
        favorites.refresh_from_db()
        self.assertEqual(favorites.name, original_name)

    def test_favorites_cannot_be_deleted(self):
        """Keep the system favorites playlist after an attempted deletion."""
        favorites = get_favorite_playlist_for_user(self.owner)
        self.client.post(self.url("remove", favorites), {"agree": "on"})
        self.assertTrue(Playlist.objects.filter(pk=favorites.pk).exists())

    def test_ajax_pagination_returns_fragment(self):
        """Return the next page of cards as an HTML fragment for AJAX requests."""
        for video in self.videos[3:]:
            PlaylistContent.objects.create(playlist=self.public, video=video)
        response = self.client.get(
            self.url("content", self.public),
            {"page": 2},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["videos"]), 1)
        self.assertFalse(
            "<!doctype html" in response.content.decode().lower(),
            "AJAX pagination returned a full HTML document instead of the video fragment",
        )

    def test_pagination_pages_do_not_overlap(self):
        """Distribute thirteen videos across two pages without repeating any video."""
        for video in self.videos[3:]:
            PlaylistContent.objects.create(playlist=self.public, video=video)
        first = self.client.get(self.url("content", self.public))
        second = self.client.get(self.url("content", self.public), {"page": 2})
        first_ids = {v.pk for v in first.context["videos"]}
        second_ids = {v.pk for v in second.context["videos"]}
        self.assertEqual(len(first_ids), 12)
        self.assertEqual(len(second_ids), 1)
        self.assertFalse(first_ids & second_ids)

    def test_title_sort_ascending(self):
        """Honor the ascending title order selected in the sort form."""
        response = self.client.get(
            self.url("content", self.public), {"sort": "title", "sort_direction": "on"}
        )
        titles = [v.title for v in response.context["videos"]]
        self.assertEqual(titles, sorted(titles))

    def test_rank_sort_can_be_reversed_by_the_sort_form(self):
        """Unchecking the direction box must still select descending rank order."""
        response = self.client.get(self.url("content", self.public), {"sort": "rank"})
        self.assertEqual([video.rank for video in response.context["videos"]], [3, 2, 1])
        response = self.client.get(
            self.url("content", self.public), {"sort": "rank", "sort_direction": "on"}
        )
        self.assertEqual([video.rank for video in response.context["videos"]], [1, 2, 3])

    def test_anonymous_list_shows_only_promoted_public(self):
        """Limit the anonymous playlist listing to promoted public playlists."""
        self.client.logout()
        response = self.client.get(self.url("list"))
        self.assertEqual(list(response.context["playlists"]), [self.public])

    def test_coowner_filter_includes_shared_private_playlist(self):
        """Include shared private playlists when filtering by co-ownership."""
        self.client.force_login(self.coowner)
        response = self.client.get(self.url("list"), {"visibility": "additional"})
        self.assertIn(self.private, response.context["playlists"])

    def test_reorganization_rejects_missing_payload_without_500(self):
        """Reject missing reorganization data with HTTP 400 and preserve ranks."""
        before = self.contents(self.public)
        response = self.client.post(self.url("save-reorganisation", self.public), {})
        self.assertEqual(self.contents(self.public), before)
        self.assertEqual(response.status_code, 400, self.response_error(response))

    def test_reorganization_rejects_invalid_json(self):
        """Reject malformed JSON with HTTP 400 and preserve video ranks."""
        before = self.contents(self.public)
        response = self.client.post(
            self.url("save-reorganisation", self.public), {"json-data": "not-json"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.contents(self.public), before)

    def test_reorganization_rejects_nonmember_atomically(self):
        """Roll back all swaps when a video does not belong to the playlist."""
        before = self.contents(self.public)
        response = self.client.post(
            self.url("save-reorganisation", self.public),
            {
                "json-data": json.dumps(
                    {
                        "0": [self.videos[0].slug, self.videos[1].slug],
                        "1": [self.videos[0].slug, self.videos[3].slug],
                    }
                )
            },
        )
        self.assertEqual(self.contents(self.public), before)
        self.assertIn(response.status_code, (400, 404), self.response_error(response))

    def test_reorganization_requires_csrf(self):
        """Reject a reorganization request without a valid CSRF token."""
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        before = self.contents(self.public)
        self.assertEqual(self.swap(self.public, client).status_code, 403)
        self.assertEqual(self.contents(self.public), before)

    def test_private_player_fragment_requires_permission(self):
        """Deny anonymous access to private playlist player fragments."""
        self.client.logout()
        response = self.client.get(
            reverse(
                "playlist:get-video",
                kwargs={
                    "video_slug": self.videos[0].slug,
                    "playlist_slug": self.private.slug,
                },
            )
        )
        self.assertIn(
            response.status_code, (302, 403, 404), self.response_error(response)
        )

    def test_private_player_fragment_requires_permission_for_stranger(self):
        """Deny private player fragments to an unrelated authenticated user."""
        self.client.force_login(self.stranger)
        response = self.client.get(
            reverse(
                "playlist:get-video",
                kwargs={
                    "video_slug": self.videos[0].slug,
                    "playlist_slug": self.private.slug,
                },
            )
        )
        self.assertIn(
            response.status_code, (302, 403, 404), self.response_error(response)
        )

    def test_protected_player_fragment_requires_password(self):
        """Deny protected player fragments before the playlist password is supplied."""
        self.client.logout()
        response = self.client.get(
            reverse(
                "playlist:get-video",
                kwargs={
                    "video_slug": self.videos[0].slug,
                    "playlist_slug": self.protected.slug,
                },
            )
        )
        self.assertIn(response.status_code, (302, 403, 404))

    def test_draft_player_fragment_requires_video_permission(self):
        """Prevent a public playlist from exposing an anonymous visitor to a draft."""
        Video.objects.filter(pk=self.videos[0].pk).update(is_draft=True)
        self.client.logout()
        response = self.client.get(
            reverse(
                "playlist:get-video",
                kwargs={
                    "video_slug": self.videos[0].slug,
                    "playlist_slug": self.public.slug,
                },
            )
        )
        self.assertIn(response.status_code, (302, 403, 404))

    def test_public_player_fragment_can_load_next_video(self):
        """Load the next public video and keep the player sidebar in rank order."""
        self.client.logout()
        response = self.client.get(
            reverse(
                "playlist:get-video",
                kwargs={
                    "video_slug": self.videos[1].slug,
                    "playlist_slug": self.public.slug,
                },
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.videos[1].title.lower(), response.json()["page_title"].lower())
        self.assertIn("page_content", response.json())
        aside = BeautifulSoup(response.json()["page_aside"], "html.parser")
        self.assertEqual(
            [item["data-url-for-video"] for item in aside.select(".player-element")],
            [
                reverse(
                    "playlist:get-video",
                    kwargs={
                        "video_slug": video.slug,
                        "playlist_slug": self.public.slug,
                    },
                )
                for video in self.videos[:3]
            ],
        )

    def test_superuser_creation_form_exposes_promoted_control(self):
        """Show the promotion control when an administrator creates a playlist."""
        self.client.force_login(self.admin)
        response = self.client.get(self.url("add"))
        soup = BeautifulSoup(response.content, "html.parser")
        self.assertIsNotNone(soup.select_one("#id_promoted"))

    def test_password_access_persists_for_pagination_and_next_video(self):
        """An unlocked playlist remains accessible only in the visitor's session."""
        self.client.logout()
        response = self.client.post(
            self.url("content", self.protected), {"password": "audit-password"}
        )
        self.assertContains(response, self.videos[0].title)
        response = self.client.get(
            self.url("content", self.protected), HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertTemplateUsed(response, "playlist/playlist-videos-list.html")
        url = reverse(
            "playlist:get-video",
            kwargs={
                "video_slug": self.videos[1].slug,
                "playlist_slug": self.protected.slug,
            },
        )
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual(Client().get(url).status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get(url).status_code, 403)

    def test_changing_password_revokes_existing_session_access(self):
        """Changing a playlist password invalidates previously granted sessions."""
        visitor = Client()
        visitor.post(self.url("content", self.protected), {"password": "audit-password"})
        response = self.client.post(
            self.url("edit", self.protected),
            self.payload(self.protected, password="new-audit-password"),
        )
        self.assertEqual(response.status_code, 302)
        response = visitor.get(self.url("content", self.protected))
        self.assertContains(response, 'id="playlist_password_form"')
        self.assertNotContains(response, self.videos[0].title)

    def test_editing_description_preserves_protected_password(self):
        """An unchanged password need not be re-entered when editing metadata."""
        password = self.protected.password
        response = self.client.post(
            self.url("edit", self.protected),
            self.payload(self.protected, description="Updated description"),
        )
        self.assertEqual(response.status_code, 302)
        self.protected.refresh_from_db()
        self.assertEqual(self.protected.password, password)
        self.assertEqual(self.protected.description, "Updated description")

    def test_player_variants_require_playlist_password(self):
        """The normal, embedded and enriched players share the password gate."""
        self.client.logout()
        for view_name in ("video:video", "enrichment:video_enrichment"):
            for embedded in ("", "true"):
                with self.subTest(view=view_name, embedded=embedded):
                    response = self.client.get(
                        reverse(view_name, kwargs={"slug": self.videos[0].slug}),
                        {"playlist": self.protected.slug, "is_iframe": embedded},
                    )
                    self.assertContains(response, 'id="playlist_password_form"')
                    self.assertNotContains(response, 'id="video-player"')

    def test_player_variants_reject_video_outside_playlist(self):
        """A playlist URL cannot be used to play a video outside its contents."""
        for view_name in ("video:video", "enrichment:video_enrichment"):
            for embedded in ("", "true"):
                with self.subTest(view=view_name, embedded=embedded):
                    response = self.client.get(
                        reverse(view_name, kwargs={"slug": self.videos[3].slug}),
                        {"playlist": self.public.slug, "is_iframe": embedded},
                    )
                    self.assertEqual(response.status_code, 404)

    def test_player_variants_reject_inaccessible_draft(self):
        """Embedding and enrichment cannot bypass a video's draft permissions."""
        Video.objects.filter(pk=self.videos[0].pk).update(is_draft=True)
        self.client.force_login(self.stranger)
        for view_name in ("video:video", "enrichment:video_enrichment"):
            response = self.client.get(
                reverse(view_name, kwargs={"slug": self.videos[0].slug}),
                {"playlist": self.public.slug, "is_iframe": "true"},
            )
            self.assertEqual(response.status_code, 403)

    def test_playlist_without_accessible_videos_does_not_start_a_draft(self):
        """Starting a playlist without accessible videos returns to its contents."""
        Video.objects.filter(pk__in=[v.pk for v in self.videos[:3]]).update(is_draft=True)
        self.client.logout()
        response = self.client.get(self.url("start-playlist", self.public))
        self.assertRedirects(response, self.url("content", self.public))

    def test_coowner_can_reorganize_but_cannot_delete(self):
        """Co-owners manage content while deletion remains reserved to the owner."""
        self.client.force_login(self.coowner)
        response = self.client.get(self.url("content", self.private))
        soup = BeautifulSoup(response.content, "html.parser")
        self.assertIsNone(
            soup.select_one(f'a[href="{self.url("remove", self.private)}"]')
        )
        self.assertEqual(self.swap(self.private).status_code, 302)
        self.assertEqual(self.contents(self.private)[0][0], self.videos[1].pk)
        response = self.client.post(self.url("remove", self.private), {"agree": "on"})
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Playlist.objects.filter(pk=self.private.pk).exists())

    def test_reorganization_rejects_invalid_shapes_without_changing_ranks(self):
        """Malformed JSON values and incomplete swaps return 400 without mutations."""
        before = self.contents(self.public)
        values = [None, [], "text", 1, {"0": []}, {"0": "ab"}, {"0": [[], {}]}]
        for value in values:
            with self.subTest(value=value):
                response = self.client.post(
                    self.url("save-reorganisation", self.public),
                    {"json-data": json.dumps(value)},
                )
                self.assertEqual(response.status_code, 400)
                self.assertEqual(self.contents(self.public), before)

    def test_staff_only_promotion_allows_staff_and_administrators(self):
        """Only staff and administrators can promote playlists when restricted."""
        staff = User.objects.create_user("audit.staff", is_staff=True)
        with patch(
            "pod.playlist.forms.RESTRICT_PROMOTED_PLAYLIST_ACCESS_TO_STAFF_ONLY", True
        ):
            for user, allowed in ((self.owner, False), (staff, True), (self.admin, True)):
                with self.subTest(user=user.username):
                    self.client.force_login(user)
                    response = self.client.get(self.url("add"))
                    self.assertEqual(
                        "promoted" in response.context["form"].fields, allowed
                    )
