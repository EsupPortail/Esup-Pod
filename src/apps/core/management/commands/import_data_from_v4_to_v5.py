"""Esup-Pod data migration command from V4 to V5.

This command handles importing data from Pod V4 export format into Pod V5.
"""

import html
import logging
import os
from contextlib import nullcontext as dummy_context

from django.conf import settings
from django.contrib.auth.models import User, Group
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand
from django.db import transaction, connection, models
from django.db.models.signals import post_save, pre_save, post_delete
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.html import strip_tags
from django.utils.text import slugify
from django.utils.timezone import make_aware, is_naive

from src.apps.authentication.models import Owner, AccessGroup, GroupSite
from src.apps.authentication.models.Owner import (
    create_owner_profile,
    default_site_owner,
)
from src.apps.authentication.models.GroupSite import (
    create_groupsite_profile,
    default_site_groupsite,
)
from src.apps.collection.models import (
    Channel,
    Theme,
    ThemeItem,
    Playlist,
    PlaylistItem,
)
from src.apps.layout.models import BlockConfig
from src.apps.encoding.conf import encoding_settings
from src.apps.encoding.models import EncodingVideo
from src.apps.video.models import (
    Video,
    Type,
    Discipline,
    ViewCount,
    Comment,
    Vote,
    Subtitle,
)
from src.apps.video.signals import (
    set_video_slug,
    auto_delete_file_on_delete,
    auto_delete_file_on_change,
    video_post_save,
    auto_assign_site_to_video,
    auto_assign_site_to_type,
)

logger = logging.getLogger(__name__)


def clean_html(text):
    """Strip HTML tags and unescape HTML entities from a given string."""
    if not text:
        return text
    return html.unescape(strip_tags(text))


class MigrationMapping(models.Model):
    """MigrationMapping class."""

    class Status(models.TextChoices):
        """Status class."""

        SUCCESS = "SUCCESS", "Success"
        ERROR = "ERROR", "Error"
        IGNORED = "IGNORED", "Ignored"

    model_name = models.CharField(max_length=50, db_index=True)
    v4_id = models.IntegerField(db_index=True)
    v5_id = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, db_index=True)
    message = models.TextField(blank=True)

    class Meta:
        """Meta class."""

        app_label = "core"
        db_table = "core_migrationmapping"
        unique_together = ("model_name", "v4_id")


class DryRunRollbackException(Exception):
    """Exception raised to rollback transaction in dry-run mode."""

    pass


class Command(BaseCommand):
    """Command class."""

    help = "Import data (Users, Videos, Playlists, relations) from Pod v4 to Pod v5"

    def add_arguments(self, parser):
        """Define command-line arguments for the import script."""
        parser.add_argument(
            "--file",
            type=str,
            default=".tmp/v4_exported_to_v5.json",
            help="Path to the JSON file exported from Pod V4",
        )
        parser.add_argument(
            "--verify-files",
            action="store_true",
            help="Verify media files existence in /media/",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simulate migration and rollback at the end",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=1000,
            help="Number of records to process per database transaction/batch",
        )

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    def _record_batch_errors(self, model_name, batch, error):
        """Record MigrationMapping error entries for a failed batch."""
        try:
            with transaction.atomic():
                err_mappings = [
                    MigrationMapping(
                        model_name=model_name,
                        v4_id=item["id"],
                        status=MigrationMapping.Status.ERROR,
                        message=str(error),
                    )
                    for item in batch
                ]
                MigrationMapping.objects.bulk_create(err_mappings, ignore_conflicts=True)
        except Exception as inner_e:
            logger.warning(f"Could not record migration error to database: {inner_e}")

    def _get_unprocessed_items(self, model_name, items):
        """Filter out already-migrated items."""
        migrated_ids = set(
            MigrationMapping.objects.filter(
                model_name=model_name, status="SUCCESS"
            ).values_list("v4_id", flat=True)
        )
        return [item for item in items if item["id"] not in migrated_ids]

    @staticmethod
    def _parse_aware_datetime(dt_str):
        """Parse a datetime string and return a timezone-aware datetime or None."""
        if not dt_str:
            return None
        dt = parse_datetime(dt_str)
        if dt is None:
            return None
        return make_aware(dt) if is_naive(dt) else dt

    @staticmethod
    def _make_unique_slug(base_slug, existing_slugs, max_length=255):
        """Return a slug that is unique within *existing_slugs*."""
        base_slug = base_slug[: max_length - 10]  # leave room for suffix
        slug = base_slug
        counter = 1
        while slug in existing_slugs:
            slug = f"{base_slug}-{counter}"
            counter += 1
        existing_slugs.add(slug)
        return slug[:max_length]

    def _bulk_create_batched(self, model, items, batch_size, label):
        """Bulk-create *items* in batches, logging errors."""
        success_count = 0
        for i in range(0, len(items), batch_size):
            batch = items[i : i + batch_size]
            try:
                with transaction.atomic():
                    model.objects.bulk_create(batch, ignore_conflicts=True)
                    success_count += len(batch)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error inserting {label} batch: {e}"))
        return success_count

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def handle(self, *args, **options):
        """Execute the import process, managing dry-run mode and signal disconnections."""
        file_path = options["file"]
        dry_run = options["dry_run"]

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "WARNING: Running in DRY-RUN mode. "
                    "No changes will be written to the database."
                )
            )

        data = self._make_lazy_data(file_path)
        self._setup_migration_table()

        self.stdout.write(
            self.style.SUCCESS("*** Start importing data from V4 to V5 ***")
        )

        # Pre-create all django sites listed in V4 dump
        self.pre_create_sites(data.get("django_site", []))

        # Disable signals to prevent conflicts and improve performances
        self.disconnect_signals()

        try:
            self._run_import(data, options, dry_run)
        finally:
            self.reconnect_signals()
            self.stdout.write(self.style.SUCCESS("*** Finished migration process ***"))

    def _make_lazy_data(self, file_path):
        """Build the lazy JSON reader."""

        class LazyJSONData:
            """LazyJSONData class."""

            def __init__(self, fp, stdout, style):
                """Initialize the lazy JSON reader with the file path and log stdout/style."""
                self.file_path = fp
                self.stdout = stdout
                self.style = style

            def get(self, key, default=None):
                """Retrieve all items corresponding to the specified key in the JSON file using ijson."""
                import ijson

                try:
                    with open(self.file_path, "rb") as f:
                        items = list(ijson.items(f, f"{key}.item"))
                        return (
                            items if items else (default if default is not None else [])
                        )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"Error reading '{key}' with ijson: {e}")
                    )
                    return default if default is not None else []

        return LazyJSONData(file_path, self.stdout, self.style)

    def _setup_migration_table(self):
        """Ensure the MigrationMapping table exists."""
        table_names = connection.introspection.table_names()
        if MigrationMapping._meta.db_table not in table_names:
            try:
                with connection.schema_editor() as schema_editor:
                    schema_editor.create_model(MigrationMapping)
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f"Warning creating MigrationMapping table: {e}")
                )

    def _run_import(self, data, options, dry_run):
        """Execute all import steps inside an optional transaction."""
        batch_size = options["batch_size"]
        ctx = transaction.atomic() if dry_run else dummy_context()

        try:
            with ctx:
                self._run_import_steps(data, options, batch_size)

                if dry_run:
                    self.stdout.write(
                        self.style.SUCCESS(
                            "Dry run completed successfully. "
                            "Rolling back database changes..."
                        )
                    )
                    raise DryRunRollbackException("Dry run rollback")

                self.ensure_superuser_exists()
                self.stdout.write(self.style.SUCCESS("Migration completed successfully!"))
        except DryRunRollbackException:
            logger.info("Dry-run transaction rolled back.")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error during import: {e}"))
            logger.exception("Error during data import")

    def _run_import_steps(self, data, options, batch_size):
        """Sequentially run every import step."""
        # 1. Users, groups, and auth profiles
        self.import_users(data.get("auth_user", []), batch_size)
        self.import_owners(data.get("authentication_owner", []), batch_size)
        self.import_groups(data.get("auth_group", []), batch_size)
        self.import_accessgroups(data.get("authentication_accessgroup", []), batch_size)
        self.import_groupsites(data.get("authentication_groupsite", []), batch_size)

        # 2. Prereqs for videos
        self.import_types(data.get("video_type", []), batch_size)
        self.import_disciplines(data.get("video_discipline", []), batch_size)
        self.import_channels(data.get("video_channel", []), data, batch_size)
        self.import_themes(data.get("video_theme", []), batch_size)
        self.import_blocks(data.get("main_block", []), batch_size)

        # 3. Videos
        self.import_video_tags(data)
        self.import_videos(data.get("video_video", []), data, options)

        # 4. Playlists
        self.import_playlists(data.get("playlist_playlist", []), batch_size)
        self.import_playlist_contents(
            data.get("playlist_playlistcontent", []),
            data.get("playlist_playlist", []),
            batch_size,
        )

        # 5. Extra entities
        self.import_comments(data.get("video_comment", []), batch_size)
        self.import_votes(data.get("video_vote", []), batch_size)
        self.import_viewcounts(data.get("video_viewcount", []), batch_size)

        # 6. Relations (ManyToMany join tables)
        self.import_relations(data, batch_size)

        # 7. Subtitles and Encoded resolutions
        self.import_subtitles(data.get("completion_track", []), data, batch_size)
        self.import_encoded_videos(
            data.get("video_encode_transcript_encodingvideo", []),
            batch_size,
        )

    # ------------------------------------------------------------------
    # Signal management
    # ------------------------------------------------------------------

    def disconnect_signals(self):
        """Disconnect Django signals to optimize import speed and prevent side effects during bulk inserts."""
        self.stdout.write("Disconnecting signals...")
        post_save.disconnect(create_owner_profile, sender=User)
        post_save.disconnect(default_site_owner, sender=Owner)
        post_save.disconnect(create_groupsite_profile, sender=Group)
        post_save.disconnect(default_site_groupsite, sender=GroupSite)

        post_save.disconnect(set_video_slug, sender=Video)
        post_delete.disconnect(auto_delete_file_on_delete, sender=Video)
        pre_save.disconnect(auto_delete_file_on_change, sender=Video)
        post_save.disconnect(video_post_save, sender=Video)
        post_save.disconnect(auto_assign_site_to_video, sender=Video)
        post_save.disconnect(auto_assign_site_to_type, sender=Type)

    def reconnect_signals(self):
        """Reconnect Django signals after the import process completes."""
        self.stdout.write("Reconnecting signals...")
        post_save.connect(create_owner_profile, sender=User)
        post_save.connect(default_site_owner, sender=Owner)
        post_save.connect(create_groupsite_profile, sender=Group)
        post_save.connect(default_site_groupsite, sender=GroupSite)

        post_save.connect(set_video_slug, sender=Video)
        post_delete.connect(auto_delete_file_on_delete, sender=Video)
        pre_save.connect(auto_delete_file_on_change, sender=Video)
        post_save.connect(video_post_save, sender=Video)
        post_save.connect(auto_assign_site_to_video, sender=Video)
        post_save.connect(auto_assign_site_to_type, sender=Type)

    def pre_create_sites(self, items):
        """Ensure all Django Sites mentioned in the source data exist in the database."""
        for item in items:
            Site.objects.get_or_create(
                id=item["id"],
                defaults={
                    "domain": item.get("domain", f"site{item['id']}.com"),
                    "name": item.get("name", f"Site {item['id']}"),
                },
            )

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------

    def _build_user_defaults(self, item):
        """Build the defaults dict for a single User."""
        defaults = {
            "id": item["id"],
            "password": item.get("password", ""),
            "is_superuser": item.get("is_superuser", False),
            "username": item.get("username"),
            "first_name": item.get("first_name", ""),
            "last_name": item.get("last_name", ""),
            "email": item.get("email", ""),
            "is_staff": item.get("is_staff", False),
            "is_active": item.get("is_active", True),
        }
        last_login = self._parse_aware_datetime(item.get("last_login"))
        if last_login:
            defaults["last_login"] = last_login
        date_joined = self._parse_aware_datetime(item.get("date_joined"))
        if date_joined:
            defaults["date_joined"] = date_joined
        return defaults

    def import_users(self, items, batch_size):
        """Import User model records from the V4 dump in batches."""
        self.stdout.write("Importing Users...")
        items_to_process = self._get_unprocessed_items("User", items)
        if not items_to_process:
            self.stdout.write("All Users already migrated.")
            return

        success_count = 0
        error_count = 0

        for i in range(0, len(items_to_process), batch_size):
            batch = items_to_process[i : i + batch_size]
            try:
                with transaction.atomic():
                    instances = []
                    mappings = []
                    for item in batch:
                        instances.append(User(**self._build_user_defaults(item)))
                        mappings.append(
                            MigrationMapping(
                                model_name="User",
                                v4_id=item["id"],
                                v5_id=item["id"],
                                status=MigrationMapping.Status.SUCCESS,
                            )
                        )

                    User.objects.bulk_create(instances, ignore_conflicts=True)
                    MigrationMapping.objects.bulk_create(mappings, ignore_conflicts=True)
                    success_count += len(batch)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error in User batch: {e}"))
                self._record_batch_errors("User", batch, e)
                error_count += len(batch)
        self.stdout.write(
            f"Users imported: {success_count} success, " f"{error_count} errors."
        )

    # ------------------------------------------------------------------
    # Owners
    # ------------------------------------------------------------------

    def _build_owner_entry(self, item, existing_user_ids, existing_owner_users):
        """Return (Owner_instance_or_None, MigrationMapping, was_success)."""
        user_id = item.get("user_id")
        if user_id not in existing_user_ids:
            mapping = MigrationMapping(
                model_name="Owner",
                v4_id=item["id"],
                status=MigrationMapping.Status.IGNORED,
                message=f"User ID {user_id} does not exist",
            )
            return None, mapping, "ignored"

        if user_id in existing_owner_users:
            mapping = MigrationMapping(
                model_name="Owner",
                v4_id=item["id"],
                v5_id=item["id"],
                status=MigrationMapping.Status.SUCCESS,
            )
            return None, mapping, "duplicate"

        defaults = {
            "id": item["id"],
            "user_id": user_id,
            "auth_type": item.get("auth_type", "local") or "local",
            "affiliation": item.get("affiliation", "member") or "member",
            "comment": item.get("comment", "") or "",
            "hashkey": item.get("hashkey", "") or "",
            "userpicture": item.get("userpicture", "") or "",
            "establishment": item.get("establishment", "U1") or "U1",
            "accepts_notifications": item.get("accepts_notifications"),
        }
        mapping = MigrationMapping(
            model_name="Owner",
            v4_id=item["id"],
            v5_id=item["id"],
            status=MigrationMapping.Status.SUCCESS,
        )
        return Owner(**defaults), mapping, "new"

    def import_owners(self, items, batch_size):
        """Import Owner profiles associated with existing users."""
        self.stdout.write("Importing Owners...")
        items_to_process = self._get_unprocessed_items("Owner", items)
        if not items_to_process:
            self.stdout.write("All Owners already migrated.")
            return

        existing_user_ids = set(User.objects.values_list("id", flat=True))
        existing_owner_users = set(Owner.objects.values_list("user_id", flat=True))

        success_count = 0
        error_count = 0
        ignored_count = 0

        for i in range(0, len(items_to_process), batch_size):
            batch = items_to_process[i : i + batch_size]
            try:
                with transaction.atomic():
                    instances = []
                    mappings = []
                    for item in batch:
                        inst, mapping, status = self._build_owner_entry(
                            item, existing_user_ids, existing_owner_users
                        )
                        mappings.append(mapping)
                        if status == "ignored":
                            ignored_count += 1
                        elif status == "duplicate":
                            success_count += 1
                        else:
                            instances.append(inst)

                    if instances:
                        Owner.objects.bulk_create(instances, ignore_conflicts=True)
                    MigrationMapping.objects.bulk_create(mappings, ignore_conflicts=True)
                    success_count += len(instances)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error in Owner batch: {e}"))
                self._record_batch_errors("Owner", batch, e)
                error_count += len(batch)
        self.stdout.write(
            f"Owners imported: {success_count} success, "
            f"{error_count} errors, {ignored_count} ignored."
        )

    # ------------------------------------------------------------------
    # Groups
    # ------------------------------------------------------------------

    def import_groups(self, items, batch_size):
        """Import django Auth Group records."""
        self.stdout.write("Importing Groups...")
        items_to_process = self._get_unprocessed_items("Group", items)
        if not items_to_process:
            self.stdout.write("All Groups already migrated.")
            return

        success_count = 0
        error_count = 0

        for i in range(0, len(items_to_process), batch_size):
            batch = items_to_process[i : i + batch_size]
            try:
                with transaction.atomic():
                    instances = []
                    mappings = []
                    for item in batch:
                        instances.append(Group(id=item["id"], name=item["name"][:150]))
                        mappings.append(
                            MigrationMapping(
                                model_name="Group",
                                v4_id=item["id"],
                                v5_id=item["id"],
                                status=MigrationMapping.Status.SUCCESS,
                            )
                        )
                    Group.objects.bulk_create(instances, ignore_conflicts=True)
                    MigrationMapping.objects.bulk_create(mappings, ignore_conflicts=True)
                    success_count += len(instances)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error in Group batch: {e}"))
                error_count += len(batch)
        self.stdout.write(
            f"Groups imported: {success_count} success, " f"{error_count} errors."
        )

    # ------------------------------------------------------------------
    # AccessGroups
    # ------------------------------------------------------------------

    def import_accessgroups(self, items, batch_size):
        """Import AccessGroup authorization profiles."""
        self.stdout.write("Importing AccessGroups...")
        items_to_process = self._get_unprocessed_items("AccessGroup", items)
        if not items_to_process:
            self.stdout.write("All AccessGroups already migrated.")
            return

        success_count = 0
        error_count = 0

        for i in range(0, len(items_to_process), batch_size):
            batch = items_to_process[i : i + batch_size]
            try:
                with transaction.atomic():
                    instances = []
                    mappings = []
                    for item in batch:
                        instances.append(
                            AccessGroup(
                                id=item["id"],
                                display_name=item.get("display_name", "") or "",
                                code_name=item.get("code_name", "") or "",
                                auto_sync=item.get("auto_sync", False),
                            )
                        )
                        mappings.append(
                            MigrationMapping(
                                model_name="AccessGroup",
                                v4_id=item["id"],
                                v5_id=item["id"],
                                status=MigrationMapping.Status.SUCCESS,
                            )
                        )
                    AccessGroup.objects.bulk_create(instances, ignore_conflicts=True)
                    MigrationMapping.objects.bulk_create(mappings, ignore_conflicts=True)
                    success_count += len(instances)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error in AccessGroup batch: {e}"))
                error_count += len(batch)
        self.stdout.write(
            f"AccessGroups imported: {success_count} success, " f"{error_count} errors."
        )

    # ------------------------------------------------------------------
    # GroupSites
    # ------------------------------------------------------------------

    def import_groupsites(self, items, batch_size):
        """Import GroupSite model records, checking that the associated Group exists."""
        self.stdout.write("Importing GroupSites...")
        items_to_process = self._get_unprocessed_items("GroupSite", items)
        if not items_to_process:
            self.stdout.write("All GroupSites already migrated.")
            return

        existing_group_ids = set(Group.objects.values_list("id", flat=True))

        success_count = 0
        error_count = 0
        ignored_count = 0

        for i in range(0, len(items_to_process), batch_size):
            batch = items_to_process[i : i + batch_size]
            try:
                with transaction.atomic():
                    instances = []
                    mappings = []
                    for item in batch:
                        g_id = item.get("group_id")
                        if g_id not in existing_group_ids:
                            ignored_count += 1
                            continue
                        instances.append(GroupSite(id=item["id"], group_id=g_id))
                        mappings.append(
                            MigrationMapping(
                                model_name="GroupSite",
                                v4_id=item["id"],
                                v5_id=item["id"],
                                status=MigrationMapping.Status.SUCCESS,
                            )
                        )
                    if instances:
                        GroupSite.objects.bulk_create(instances, ignore_conflicts=True)
                    MigrationMapping.objects.bulk_create(mappings, ignore_conflicts=True)
                    success_count += len(instances)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error in GroupSite batch: {e}"))
                error_count += len(batch)
        self.stdout.write(
            f"GroupSites imported: {success_count} success, "
            f"{error_count} errors, {ignored_count} ignored."
        )

    # ------------------------------------------------------------------
    # Types
    # ------------------------------------------------------------------

    def import_types(self, items, batch_size):
        """Import Video Type configurations, generating slugs if necessary."""
        self.stdout.write("Importing Types...")
        items_to_process = self._get_unprocessed_items("Type", items)
        if not items_to_process:
            self.stdout.write("All Types already migrated.")
            return

        success_count = 0
        error_count = 0

        for i in range(0, len(items_to_process), batch_size):
            batch = items_to_process[i : i + batch_size]
            try:
                with transaction.atomic():
                    instances = []
                    mappings = []
                    for item in batch:
                        slug = item.get("slug") or slugify(item["title"])
                        instances.append(
                            Type(
                                id=item["id"],
                                title=item["title"][:100],
                                slug=slug[:100],
                            )
                        )
                        mappings.append(
                            MigrationMapping(
                                model_name="Type",
                                v4_id=item["id"],
                                v5_id=item["id"],
                                status=MigrationMapping.Status.SUCCESS,
                            )
                        )
                    Type.objects.bulk_create(instances, ignore_conflicts=True)
                    MigrationMapping.objects.bulk_create(mappings, ignore_conflicts=True)
                    success_count += len(instances)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error in Type batch: {e}"))
                error_count += len(batch)
        self.stdout.write(
            f"Types imported: {success_count} success, " f"{error_count} errors."
        )

    # ------------------------------------------------------------------
    # Disciplines
    # ------------------------------------------------------------------

    def import_disciplines(self, items, batch_size):
        """Import academic disciplines and clean their descriptions."""
        self.stdout.write("Importing Disciplines...")
        items_to_process = self._get_unprocessed_items("Discipline", items)
        if not items_to_process:
            self.stdout.write("All Disciplines already migrated.")
            return

        success_count = 0
        error_count = 0

        for i in range(0, len(items_to_process), batch_size):
            batch = items_to_process[i : i + batch_size]
            try:
                with transaction.atomic():
                    instances = []
                    mappings = []
                    for item in batch:
                        instances.append(
                            Discipline(
                                id=item["id"],
                                title=item["title"][:100],
                                slug=item.get("slug", "")[:255]
                                or slugify(item["title"])[:255],
                                description=clean_html(item.get("description", "") or ""),
                            )
                        )
                        mappings.append(
                            MigrationMapping(
                                model_name="Discipline",
                                v4_id=item["id"],
                                v5_id=item["id"],
                                status=MigrationMapping.Status.SUCCESS,
                            )
                        )
                    Discipline.objects.bulk_create(instances, ignore_conflicts=True)
                    MigrationMapping.objects.bulk_create(mappings, ignore_conflicts=True)
                    success_count += len(instances)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error in Discipline batch: {e}"))
                error_count += len(batch)
        self.stdout.write(
            f"Disciplines imported: {success_count} success, " f"{error_count} errors."
        )

    # ------------------------------------------------------------------
    # Channels
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_channel_owner(c_id, channel_owners_map, existing_user_ids, fallback_id):
        """Return the owner_id for a channel."""
        owners = channel_owners_map.get(c_id, [])
        valid = [o for o in owners if o in existing_user_ids]
        return valid[0] if valid else fallback_id

    def import_channels(self, items, data, batch_size):
        """Import thematic channels and resolve their corresponding owners."""
        self.stdout.write("Importing Channels...")
        items_to_process = self._get_unprocessed_items("Channel", items)
        if not items_to_process:
            self.stdout.write("All Channels already migrated.")
            return

        existing_user_ids = set(User.objects.values_list("id", flat=True))
        first_user_id = User.objects.first().id if User.objects.exists() else 1

        # Build owners map
        channel_owners_map = {}
        for row in data.get("video_channel_owners", []):
            c_id = row["channel_id"]
            channel_owners_map.setdefault(c_id, []).append(row["user_id"])

        success_count = 0
        error_count = 0

        for i in range(0, len(items_to_process), batch_size):
            batch = items_to_process[i : i + batch_size]
            try:
                with transaction.atomic():
                    instances = []
                    mappings = []
                    for item in batch:
                        c_id = item["id"]
                        owner_id = self._resolve_channel_owner(
                            c_id,
                            channel_owners_map,
                            existing_user_ids,
                            first_user_id,
                        )
                        defaults = {
                            "id": c_id,
                            "title": item["title"][:250],
                            "slug": item.get("slug", "")[:255]
                            or slugify(item["title"])[:255],
                            "description": clean_html(item.get("description", "") or ""),
                            "is_public": item.get("visible", True),
                            "owner_id": owner_id,
                            "old_v4_id": c_id,
                        }
                        instances.append(Channel(**defaults))
                        mappings.append(
                            MigrationMapping(
                                model_name="Channel",
                                v4_id=c_id,
                                v5_id=c_id,
                                status=MigrationMapping.Status.SUCCESS,
                            )
                        )

                    Channel.objects.bulk_create(instances, ignore_conflicts=True)
                    MigrationMapping.objects.bulk_create(mappings, ignore_conflicts=True)
                    success_count += len(instances)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error in Channel batch: {e}"))
                self._record_batch_errors("Channel", batch, e)
                error_count += len(batch)
        self.stdout.write(
            f"Channels imported: {success_count} success, " f"{error_count} errors."
        )

    # ------------------------------------------------------------------
    # Themes
    # ------------------------------------------------------------------

    def _import_themes_pass1(
        self, items_to_process, existing_channel_ids, existing_slugs, batch_size
    ):
        """Create themes without parents (Pass 1)."""
        self.stdout.write("Importing Themes (Pass 1 - without parents)...")
        success_count = 0
        error_count = 0

        for i in range(0, len(items_to_process), batch_size):
            batch = items_to_process[i : i + batch_size]
            try:
                with transaction.atomic():
                    instances = []
                    mappings = []
                    for item in batch:
                        c_id = item.get("channel_id")
                        if c_id not in existing_channel_ids:
                            c_id = None

                        base_slug = item.get("slug") or slugify(item["title"])
                        slug = self._make_unique_slug(base_slug, existing_slugs)

                        defaults = {
                            "id": item["id"],
                            "title": item["title"][:250],
                            "slug": slug[:255],
                            "description": clean_html(item.get("description", "") or ""),
                            "channel_id": c_id,
                            "parent_id": None,
                            "old_v4_id": item["id"],
                        }
                        instances.append(Theme(**defaults))
                        mappings.append(
                            MigrationMapping(
                                model_name="Theme",
                                v4_id=item["id"],
                                v5_id=item["id"],
                                status=MigrationMapping.Status.SUCCESS,
                            )
                        )

                    Theme.objects.bulk_create(instances, ignore_conflicts=True)
                    MigrationMapping.objects.bulk_create(mappings, ignore_conflicts=True)
                    success_count += len(instances)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error in Theme batch (Pass 1): {e}"))
                self._record_batch_errors("Theme", batch, e)
                error_count += len(batch)

        return success_count, error_count

    def _update_theme_parents(self, items, batch_size):
        """Set parent_id for themes (Pass 2)."""
        self.stdout.write("Updating Theme parents (Pass 2)...")
        existing_theme_ids = set(Theme.objects.values_list("id", flat=True))
        themes_to_update = []
        for item in items:
            t_id = item["id"]
            p_id = item.get("parentId_id")
            if (
                p_id
                and p_id in existing_theme_ids
                and t_id in existing_theme_ids
                and t_id != p_id
            ):
                themes_to_update.append(Theme(id=t_id, parent_id=p_id))

        for i in range(0, len(themes_to_update), batch_size):
            batch = themes_to_update[i : i + batch_size]
            try:
                with transaction.atomic():
                    Theme.objects.bulk_update(batch, ["parent_id"])
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error updating Theme parents batch: {e}")
                )

    def import_themes(self, items, batch_size):
        """Import hierarchical Theme objects in a two-pass process to preserve parental links."""
        items_to_process = self._get_unprocessed_items("Theme", items)
        if not items_to_process:
            self.stdout.write("All Themes already migrated.")
            return

        existing_channel_ids = set(Channel.objects.values_list("id", flat=True))
        existing_slugs = set(Theme.objects.values_list("slug", flat=True))

        success_count, error_count = self._import_themes_pass1(
            items_to_process, existing_channel_ids, existing_slugs, batch_size
        )
        self._update_theme_parents(items, batch_size)

        self.stdout.write(
            f"Themes imported: {success_count} success, " f"{error_count} errors."
        )

    # ------------------------------------------------------------------
    # Video Tags
    # ------------------------------------------------------------------

    def import_video_tags(self, data):
        """Import tagulous video tags pre-defined in the V4 dump."""
        self.stdout.write("Importing Video Tags...")
        tag_model = Video.tags.tag_model
        v4_tags = data.get("video_tagulous_video_tags", [])

        tags_to_create = []
        existing_tags = set(tag_model.objects.values_list("name", flat=True))

        for item in v4_tags:
            name = item["name"]
            if name not in existing_tags:
                slug = item.get("slug") or slugify(name)
                tags_to_create.append(
                    tag_model(
                        id=item["id"],
                        name=name[:80],
                        slug=slug[:50],
                        count=item.get("count", 0),
                        protected=item.get("protected", False),
                    )
                )
                existing_tags.add(name)

        if tags_to_create:
            tag_model.objects.bulk_create(tags_to_create, ignore_conflicts=True)
            self.stdout.write(f"Created {len(tags_to_create)} tags.")

    # ------------------------------------------------------------------
    # Video conversion helpers
    # ------------------------------------------------------------------

    def get_v5_cursus(self, v4_cursus):
        """Map V4 educational level abbreviation to the corresponding V5 Cursus choice."""
        if v4_cursus == "L":
            return "L1"
        elif v4_cursus == "M":
            return "M1"
        elif v4_cursus == "D":
            return "D"
        return "0"

    def get_v5_status(self, is_draft, is_restricted):
        """Convert draft and restricted boolean flags to V5 status code choices."""
        if is_draft:
            return "DR"
        elif is_restricted:
            return "RE"
        return "PU"

    def get_v5_license(self, v4_license):
        """Normalize V4 license text into a recognized V5 license key."""
        if not v4_license:
            return "COPYRIGHT"
        upper = v4_license.upper()
        if "CC-BY-SA" in upper:
            return "CC-BY-SA"
        elif "CC-BY-NC" in upper:
            return "CC-BY-NC"
        elif "CC-BY-ND" in upper:
            return "CC-BY-ND"
        elif "CC-BY" in upper:
            return "CC-BY"
        return "COPYRIGHT"

    # ------------------------------------------------------------------
    # Videos
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_video_file(item):
        """Resolve the video file path, adjusting the directory prefix."""
        video_file = item.get("video", "")
        videos_dir = encoding_settings.videos_dir
        if videos_dir != "videos" and video_file and video_file.startswith("videos/"):
            video_file = video_file.replace("videos/", f"{videos_dir}/", 1)
        return video_file

    @staticmethod
    def _resolve_thumbnail(thumb_id, custom_images):
        """Resolve the thumbnail path from custom images."""
        if thumb_id not in custom_images:
            return None
        path = custom_images[thumb_id]
        thumbnails_dir = encoding_settings.thumbnails_dir
        if thumbnails_dir != "thumbnails" and path and path.startswith("thumbnails/"):
            path = path.replace("thumbnails/", f"{thumbnails_dir}/", 1)
        return path

    @staticmethod
    def _parse_date_field(item, field_name):
        """Parse a date-only field like date_evt or date_delete."""
        raw = item.get(field_name)
        if not raw:
            return None
        try:
            return parse_datetime(raw + " 00:00:00").date()
        except Exception as e:
            logger.warning(
                f"Could not parse {field_name} '{raw}' " f"for video {item['id']}: {e}"
            )
            return None

    def _build_video_defaults(self, item, context):
        """Build the defaults dict for a single Video."""
        v_id = item["id"]
        owner_id = item.get("owner_id")
        if owner_id not in context["user_ids"]:
            owner_id = context["first_user_id"]

        type_id = item.get("type_id")
        if type_id not in context["type_ids"]:
            type_id = None

        channel_id = context["video_channels"].get(v_id)
        if channel_id not in context["channel_ids"]:
            channel_id = None

        video_file = self._resolve_video_file(item)
        thumbnail = self._resolve_thumbnail(
            item.get("thumbnail_id"), context["custom_images"]
        )

        created_at = self._parse_aware_datetime(item.get("date_added")) or timezone.now()

        return {
            "id": v_id,
            "title": item["title"][:250],
            "slug": item["slug"][:255],
            "description": clean_html(item.get("description", "") or ""),
            "video_file": video_file or None,
            "is_video": item.get("is_video", True),
            "thumbnail": thumbnail,
            "overview": clean_html(item.get("overview", "") or "") or None,
            "duration": item.get("duration", 0),
            "view_count": item.get("view_count", 0),
            "is_360": item.get("is_360", False),
            "owner_id": owner_id,
            "channel_id": channel_id,
            "status": self.get_v5_status(
                item.get("is_draft", False),
                item.get("is_restricted", False),
            ),
            "encoding_status": ("PR" if item.get("encoding_in_progress") else "DO"),
            "is_auth_required": item.get("is_restricted", False),
            "password": item.get("password", "") or None,
            "allow_downloading": item.get("allow_downloading", False),
            "disable_comment": item.get("disable_comment", False),
            "order": item.get("order", 1),
            "date_of_event": self._parse_date_field(item, "date_evt"),
            "type_id": type_id,
            "license_id": self.get_v5_license(item.get("licence")),
            "cursus_id": self.get_v5_cursus(item.get("cursus")),
            "language_id": item.get("main_lang", "fr")[:10],
            "transcript_language": item.get("transcript", "")[:10],
            "created_at": created_at,
            "date_to_delete": self._parse_date_field(item, "date_delete"),
        }

    def _tag_missing_files(self, missing_files_video_ids):
        """Tag videos whose source files are missing."""
        if not missing_files_video_ids:
            return
        self.stdout.write("Tagging videos with missing files...")
        tag_model = Video.tags.tag_model
        missing_tag, _ = tag_model.objects.get_or_create(
            name="Fichier égaré",
            defaults={"slug": "fichier-egare"},
        )
        through_model = Video.tags.through

        existing_relations = set(
            through_model.objects.filter(
                tagulous_video_tags_id=missing_tag.id
            ).values_list("video_id", flat=True)
        )

        relations = [
            through_model(
                video_id=v_id,
                tagulous_video_tags_id=missing_tag.id,
            )
            for v_id in missing_files_video_ids
            if v_id not in existing_relations
        ]

        if relations:
            through_model.objects.bulk_create(relations, ignore_conflicts=True)

    def import_videos(self, items, data, options):
        """Import Video records, mapping fields, resolving media paths, and optional file verification."""
        self.stdout.write("Importing Videos...")
        batch_size = options["batch_size"]
        verify_files = options["verify_files"]

        items_to_process = self._get_unprocessed_items("Video", items)
        if not items_to_process:
            self.stdout.write("All Videos already migrated.")
            return

        context = {
            "user_ids": set(User.objects.values_list("id", flat=True)),
            "type_ids": set(Type.objects.values_list("id", flat=True)),
            "channel_ids": set(Channel.objects.values_list("id", flat=True)),
            "first_user_id": (User.objects.first().id if User.objects.exists() else 1),
            "custom_images": {
                row["id"]: row["file"] for row in data.get("main_customimagemodel", [])
            },
            "video_channels": {
                row["video_id"]: row["channel_id"]
                for row in data.get("video_video_channel", [])
            },
        }

        success_count = 0
        error_count = 0
        missing_files_video_ids = set()

        for i in range(0, len(items_to_process), batch_size):
            batch = items_to_process[i : i + batch_size]
            try:
                with transaction.atomic():
                    instances = []
                    mappings = []
                    for item in batch:
                        defaults = self._build_video_defaults(item, context)

                        if verify_files and defaults["video_file"]:
                            fpath = os.path.join(
                                settings.MEDIA_ROOT,
                                defaults["video_file"],
                            )
                            if not os.path.exists(fpath):
                                self.stdout.write(
                                    self.style.WARNING(
                                        f"Video V4 ID {item['id']} "
                                        f"file not found: {fpath}"
                                    )
                                )
                                missing_files_video_ids.add(item["id"])

                        instances.append(Video(**defaults))
                        mappings.append(
                            MigrationMapping(
                                model_name="Video",
                                v4_id=item["id"],
                                v5_id=item["id"],
                                status=MigrationMapping.Status.SUCCESS,
                            )
                        )

                    if instances:
                        Video.objects.bulk_create(instances, ignore_conflicts=True)
                    MigrationMapping.objects.bulk_create(mappings, ignore_conflicts=True)
                    success_count += len(instances)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error in Video batch: {e}"))
                self._record_batch_errors("Video", batch, e)
                error_count += len(batch)

        self._tag_missing_files(missing_files_video_ids)

        self.stdout.write(
            f"Videos imported: {success_count} success, " f"{error_count} errors."
        )

    # ------------------------------------------------------------------
    # Playlists
    # ------------------------------------------------------------------

    def import_playlists(self, items, batch_size):
        """Import Playlist metadata, ignoring the automatic 'Favorites' playlist of V4."""
        self.stdout.write("Importing Playlists...")
        migrated_ids = set(
            MigrationMapping.objects.filter(model_name="Playlist").values_list(
                "v4_id", flat=True
            )
        )
        existing_user_ids = set(User.objects.values_list("id", flat=True))
        first_user_id = User.objects.first().id if User.objects.exists() else 1

        items_to_process = [item for item in items if item["id"] not in migrated_ids]
        if not items_to_process:
            self.stdout.write("All Playlists already migrated.")
            return

        success_count = 0
        ignored_count = 0
        error_count = 0

        for i in range(0, len(items_to_process), batch_size):
            batch = items_to_process[i : i + batch_size]
            try:
                with transaction.atomic():
                    instances = []
                    mappings = []
                    for item in batch:
                        if item.get("name") == "Favorites":
                            ignored_count += 1
                            mappings.append(
                                MigrationMapping(
                                    model_name="Playlist",
                                    v4_id=item["id"],
                                    v5_id=None,
                                    status=MigrationMapping.Status.IGNORED,
                                    message="Favorites playlist",
                                )
                            )
                            continue

                        owner_id = item.get("owner_id")
                        if owner_id not in existing_user_ids:
                            owner_id = first_user_id

                        slug = item.get("slug") or slugify(item["name"])

                        defaults = {
                            "id": item["id"],
                            "title": item["name"][:250],
                            "slug": slug[:255],
                            "description": clean_html(item.get("description", "") or ""),
                            "owner_id": owner_id,
                            "is_public": item.get("visibility")
                            in ["public", "protected"],
                            "password": item.get("password", "") or None,
                            "old_v4_id": item["id"],
                        }

                        instances.append(Playlist(**defaults))
                        mappings.append(
                            MigrationMapping(
                                model_name="Playlist",
                                v4_id=item["id"],
                                v5_id=item["id"],
                                status=MigrationMapping.Status.SUCCESS,
                            )
                        )

                    if instances:
                        Playlist.objects.bulk_create(instances, ignore_conflicts=True)
                    MigrationMapping.objects.bulk_create(mappings, ignore_conflicts=True)
                    success_count += len(instances)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error in Playlist batch: {e}"))
                self._record_batch_errors("Playlist", batch, e)
                error_count += len(batch)
        self.stdout.write(
            f"Playlists imported: {success_count} success, "
            f"{ignored_count} ignored (Favorites), "
            f"{error_count} errors."
        )

    # ------------------------------------------------------------------
    # Playlist Contents & Favorites
    # ------------------------------------------------------------------

    def _collect_playlist_and_favorite_entries(
        self,
        items,
        playlist_map,
        existing_playlists,
        existing_videos,
        existing_users,
        existing_playlist_rels,
        existing_favorite_rels,
    ):
        """Sort playlist content items into playlist items and favorites."""
        from src.apps.collection.models.Favorite import Favorite

        playlist_items_to_create = []
        favorites_to_create = []
        ignored_count = 0

        for item in items:
            p_id = item["playlist_id"]
            v_id = item["video_id"]

            if v_id not in existing_videos:
                ignored_count += 1
                continue

            playlist_info = playlist_map.get(p_id)
            if playlist_info and playlist_info[0] == "Favorites":
                owner_id = playlist_info[1]
                if owner_id not in existing_users:
                    ignored_count += 1
                    continue
                if (owner_id, v_id) not in existing_favorite_rels:
                    favorites_to_create.append(Favorite(user_id=owner_id, video_id=v_id))
                    existing_favorite_rels.add((owner_id, v_id))
                continue

            if p_id not in existing_playlists:
                ignored_count += 1
                continue

            if (p_id, v_id) not in existing_playlist_rels:
                rank = item.get("rank", 0)
                playlist_items_to_create.append(
                    PlaylistItem(
                        playlist_id=p_id,
                        video_id=v_id,
                        position=rank if rank > 0 else 1,
                    )
                )
                existing_playlist_rels.add((p_id, v_id))

        return playlist_items_to_create, favorites_to_create, ignored_count

    def import_playlist_contents(self, items, playlist_items, batch_size):
        """Import Playlist items and map V4 'Favorites' playlists to the V5 Favorite model."""
        self.stdout.write("Importing Playlist Contents & Favorites...")

        playlist_map = {
            item["id"]: (item["name"], item["owner_id"]) for item in playlist_items
        }

        existing_playlists = set(Playlist.objects.values_list("id", flat=True))
        existing_videos = set(Video.objects.values_list("id", flat=True))
        existing_users = set(User.objects.values_list("id", flat=True))

        from src.apps.collection.models.Favorite import Favorite

        existing_playlist_rels = set(
            PlaylistItem.objects.values_list("playlist_id", "video_id")
        )
        existing_favorite_rels = set(Favorite.objects.values_list("user_id", "video_id"))

        (
            pi_to_create,
            fav_to_create,
            ignored_count,
        ) = self._collect_playlist_and_favorite_entries(
            items,
            playlist_map,
            existing_playlists,
            existing_videos,
            existing_users,
            existing_playlist_rels,
            existing_favorite_rels,
        )

        pc_count = self._bulk_create_batched(
            PlaylistItem,
            pi_to_create,
            batch_size,
            "playlist content",
        )
        fav_count = self._bulk_create_batched(
            Favorite, fav_to_create, batch_size, "favorite"
        )

        self.stdout.write(
            f"Playlist Contents imported: {pc_count} success, "
            f"Favorites imported: {fav_count} success, "
            f"ignored: {ignored_count}"
        )

    # ------------------------------------------------------------------
    # Comments
    # ------------------------------------------------------------------

    def _import_comments_pass1(
        self,
        items_to_process,
        existing_user_ids,
        existing_video_ids,
        first_user_id,
        batch_size,
    ):
        """Import comments without hierarchy (Pass 1)."""
        success_count = 0
        error_count = 0

        for i in range(0, len(items_to_process), batch_size):
            batch = items_to_process[i : i + batch_size]
            try:
                with transaction.atomic():
                    instances = []
                    mappings = []
                    for item in batch:
                        v_id = item.get("video_id")
                        if v_id not in existing_video_ids:
                            continue
                        author_id = item.get("author_id")
                        if author_id not in existing_user_ids:
                            author_id = first_user_id

                        added = (
                            self._parse_aware_datetime(item.get("added"))
                            or timezone.now()
                        )

                        defaults = {
                            "id": item["id"],
                            "content": item.get("content", "") or "",
                            "added": added,
                            "author_id": author_id,
                            "video_id": v_id,
                            "parent_id": None,
                            "direct_parent_id": None,
                        }
                        instances.append(Comment(**defaults))
                        mappings.append(
                            MigrationMapping(
                                model_name="Comment",
                                v4_id=item["id"],
                                v5_id=item["id"],
                                status=MigrationMapping.Status.SUCCESS,
                            )
                        )

                    Comment.objects.bulk_create(instances, ignore_conflicts=True)
                    MigrationMapping.objects.bulk_create(mappings, ignore_conflicts=True)
                    success_count += len(instances)
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error in Comment batch (Pass 1): {e}")
                )
                self._record_batch_errors("Comment", batch, e)
                error_count += len(batch)

        return success_count, error_count

    def _restore_comment_hierarchy(self, items, batch_size):
        """Set parent and direct_parent on comments (Pass 2)."""
        self.stdout.write("Restoring Comment hierarchies (Pass 2)...")
        existing_ids = set(Comment.objects.values_list("id", flat=True))
        to_update = []

        for item in items:
            c_id = item["id"]
            if c_id not in existing_ids:
                continue
            p_id = item.get("parent_id")
            dp_id = item.get("direct_parent_id")

            parent_val = (
                p_id if (p_id and p_id in existing_ids and p_id != c_id) else None
            )
            dp_val = (
                dp_id if (dp_id and dp_id in existing_ids and dp_id != c_id) else None
            )

            if parent_val or dp_val:
                to_update.append(
                    Comment(
                        id=c_id,
                        parent_id=parent_val,
                        direct_parent_id=dp_val,
                    )
                )

        for i in range(0, len(to_update), batch_size):
            batch = to_update[i : i + batch_size]
            try:
                with transaction.atomic():
                    Comment.objects.bulk_update(batch, ["parent_id", "direct_parent_id"])
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error updating Comment hierarchies: {e}")
                )

    def import_comments(self, items, batch_size):
        """Import Video Comment records and restore their nested reply hierarchy."""
        self.stdout.write("Importing Comments...")
        items_to_process = self._get_unprocessed_items("Comment", items)
        if not items_to_process:
            self.stdout.write("All Comments already migrated.")
            return

        existing_user_ids = set(User.objects.values_list("id", flat=True))
        existing_video_ids = set(Video.objects.values_list("id", flat=True))
        first_user_id = User.objects.first().id if User.objects.exists() else 1

        self._import_comments_pass1(
            items_to_process,
            existing_user_ids,
            existing_video_ids,
            first_user_id,
            batch_size,
        )
        self._restore_comment_hierarchy(items, batch_size)

    # ------------------------------------------------------------------
    # Votes
    # ------------------------------------------------------------------

    def import_votes(self, items, batch_size):
        """Import Comment Vote records between users and comments."""
        self.stdout.write("Importing Votes...")
        existing_comments = set(Comment.objects.values_list("id", flat=True))
        existing_users = set(User.objects.values_list("id", flat=True))
        existing_votes = set(Vote.objects.values_list("comment_id", "user_id"))

        votes_to_create = []
        ignored_count = 0

        for item in items:
            c_id = item["comment_id"]
            u_id = item["user_id"]
            if c_id not in existing_comments or u_id not in existing_users:
                ignored_count += 1
                continue

            if (c_id, u_id) not in existing_votes:
                votes_to_create.append(Vote(id=item["id"], comment_id=c_id, user_id=u_id))
                existing_votes.add((c_id, u_id))

        if votes_to_create:
            success_count = self._bulk_create_batched(
                Vote, votes_to_create, batch_size, "votes"
            )
            self.stdout.write(
                f"Votes imported: {success_count} success, " f"ignored: {ignored_count}"
            )
        else:
            self.stdout.write("No new Votes to import.")

    # ------------------------------------------------------------------
    # ViewCounts
    # ------------------------------------------------------------------

    def _collect_viewcounts(self, items, existing_videos):
        """Parse and deduplicate viewcount entries."""
        existing_viewcounts = set(ViewCount.objects.values_list("video_id", "date"))
        to_create = []

        for item in items:
            v_id = item["video_id"]
            if v_id not in existing_videos:
                continue

            dt_str = item.get("date", "")
            if not dt_str:
                continue

            try:
                dt = parse_datetime(dt_str + " 00:00:00").date()
            except Exception:
                continue

            if (v_id, dt) not in existing_viewcounts:
                to_create.append(
                    ViewCount(
                        video_id=v_id,
                        date=dt,
                        count=item.get("count", 0),
                    )
                )
                existing_viewcounts.add((v_id, dt))

        return to_create

    def import_viewcounts(self, items, batch_size):
        """Import historical date-based video view counter records."""
        self.stdout.write("Importing View Counts (Date-based)...")
        existing_videos = set(Video.objects.values_list("id", flat=True))

        to_create = self._collect_viewcounts(items, existing_videos)
        vc_batch_size = max(batch_size, 5000)

        if to_create:
            success_count = self._bulk_create_batched(
                ViewCount, to_create, vc_batch_size, "ViewCounts"
            )
            self.stdout.write(f"ViewCounts imported: {success_count} success")
        else:
            self.stdout.write("No new ViewCounts to import.")

    # ------------------------------------------------------------------
    # M2M Relations
    # ------------------------------------------------------------------

    def import_m2m_relation(
        self,
        items,
        v4_src_key,
        v4_target_key,
        through_model,
        src_field,
        target_field,
        src_ids_set,
        target_ids_set,
        batch_size,
        relation_name,
    ):
        """Generic helper to import entries into a Many-to-Many through relationship table."""
        self.stdout.write(f"Importing {relation_name} relations...")
        existing_relations = set(
            through_model.objects.values_list(src_field, target_field)
        )

        relations_to_create = []
        ignored_count = 0

        for item in items:
            src_val = item.get(v4_src_key)
            target_val = item.get(v4_target_key)

            if src_val not in src_ids_set or target_val not in target_ids_set:
                ignored_count += 1
                continue

            if (src_val, target_val) not in existing_relations:
                kwargs = {
                    src_field: src_val,
                    target_field: target_val,
                }
                relations_to_create.append(through_model(**kwargs))
                existing_relations.add((src_val, target_val))

        if relations_to_create:
            success_count = self._bulk_create_batched(
                through_model,
                relations_to_create,
                batch_size,
                relation_name,
            )
            self.stdout.write(
                f"{relation_name} relations imported: "
                f"{success_count} success, "
                f"ignored: {ignored_count}"
            )
        else:
            self.stdout.write(f"No new {relation_name} relations to import.")

    # ------------------------------------------------------------------
    # Channel Collaborators
    # ------------------------------------------------------------------

    @staticmethod
    def _add_collab_rows(
        rows,
        through_model,
        existing_channels,
        existing_users,
        existing_relations,
        relations,
        excluded_pairs=None,
    ):
        """Add collaborator rows filtering by validity."""
        for row in rows:
            c_id = row["channel_id"]
            u_id = row["user_id"]
            if c_id not in existing_channels:
                continue
            if u_id not in existing_users:
                continue
            if excluded_pairs and (c_id, u_id) in excluded_pairs:
                continue
            if (c_id, u_id) not in existing_relations:
                relations.append(through_model(channel_id=c_id, user_id=u_id))
                existing_relations.add((c_id, u_id))

    def _collect_collaborator_relations(
        self,
        data,
        primary_owners,
        existing_channels,
        existing_users,
        existing_relations,
    ):
        """Collect channel collaborator through-model instances."""
        through_model = Channel.collaborators.through
        relations = []

        # Build set of (channel_id, primary_owner_id) to exclude
        owner_pairs = {(c_id, o_id) for c_id, o_id in primary_owners.items()}

        self._add_collab_rows(
            data.get("video_channel_owners", []),
            through_model,
            existing_channels,
            existing_users,
            existing_relations,
            relations,
            excluded_pairs=owner_pairs,
        )
        self._add_collab_rows(
            data.get("video_channel_users", []),
            through_model,
            existing_channels,
            existing_users,
            existing_relations,
            relations,
        )

        return relations

    def import_channel_collaborators(self, data, batch_size):
        """Import channel owners and authorized users as V5 Channel Collaborators."""
        self.stdout.write("Importing Channel Collaborators...")
        channels = Channel.objects.values_list("id", "owner_id")
        primary_owners = {c_id: owner_id for c_id, owner_id in channels}
        existing_channels = set(primary_owners.keys())
        existing_users = set(User.objects.values_list("id", flat=True))

        through_model = Channel.collaborators.through
        existing_relations = set(
            through_model.objects.values_list("channel_id", "user_id")
        )

        relations = self._collect_collaborator_relations(
            data,
            primary_owners,
            existing_channels,
            existing_users,
            existing_relations,
        )

        if relations:
            success_count = self._bulk_create_batched(
                through_model,
                relations,
                batch_size,
                "channel collaborators",
            )
            self.stdout.write(
                f"Channel Collaborators imported: " f"{success_count} success."
            )
        else:
            self.stdout.write("No new Channel Collaborators to import.")

    def import_relations(self, data, batch_size):
        """Execute the import of all secondary Many-to-Many relational join tables."""
        self.stdout.write("Importing Many-to-Many relations...")

        owner_ids = set(Owner.objects.values_list("id", flat=True))
        site_ids = set(Site.objects.values_list("id", flat=True))
        accessgroup_ids = set(AccessGroup.objects.values_list("id", flat=True))
        groupsite_ids = set(GroupSite.objects.values_list("id", flat=True))
        user_ids = set(User.objects.values_list("id", flat=True))
        group_ids = set(Group.objects.values_list("id", flat=True))
        video_ids = set(Video.objects.values_list("id", flat=True))
        type_ids = set(Type.objects.values_list("id", flat=True))
        discipline_ids = set(Discipline.objects.values_list("id", flat=True))
        tag_ids = set(Video.tags.tag_model.objects.values_list("id", flat=True))
        theme_ids = set(Theme.objects.values_list("id", flat=True))

        self.import_m2m_relation(
            data.get("authentication_owner_sites", []),
            "owner_id",
            "site_id",
            Owner.sites.through,
            "owner_id",
            "site_id",
            owner_ids,
            site_ids,
            batch_size,
            "Owner-Site",
        )

        self.import_m2m_relation(
            data.get("authentication_owner_accessgroups", []),
            "owner_id",
            "accessgroup_id",
            Owner.accessgroups.through,
            "owner_id",
            "accessgroup_id",
            owner_ids,
            accessgroup_ids,
            batch_size,
            "Owner-AccessGroup",
        )

        self.import_m2m_relation(
            data.get("authentication_accessgroup_sites", []),
            "accessgroup_id",
            "site_id",
            AccessGroup.sites.through,
            "accessgroup_id",
            "site_id",
            accessgroup_ids,
            site_ids,
            batch_size,
            "AccessGroup-Site",
        )

        self.import_m2m_relation(
            data.get("authentication_groupsite_sites", []),
            "groupsite_id",
            "site_id",
            GroupSite.sites.through,
            "groupsite_id",
            "site_id",
            groupsite_ids,
            site_ids,
            batch_size,
            "GroupSite-Site",
        )

        self.import_m2m_relation(
            data.get("auth_user_groups", []),
            "user_id",
            "group_id",
            User.groups.through,
            "user_id",
            "group_id",
            user_ids,
            group_ids,
            batch_size,
            "User-Group",
        )

        self.import_m2m_relation(
            data.get("video_video_sites", []),
            "video_id",
            "site_id",
            Video.sites.through,
            "video_id",
            "site_id",
            video_ids,
            site_ids,
            batch_size,
            "Video-Site",
        )

        self.import_m2m_relation(
            data.get("video_video_additional_owners", []),
            "video_id",
            "user_id",
            Video.co_owners.through,
            "video_id",
            "user_id",
            video_ids,
            user_ids,
            batch_size,
            "Video-CoOwner",
        )

        self.import_m2m_relation(
            data.get("video_video_discipline", []),
            "video_id",
            "discipline_id",
            Video.disciplines.through,
            "video_id",
            "discipline_id",
            video_ids,
            discipline_ids,
            batch_size,
            "Video-Discipline",
        )

        self.import_m2m_relation(
            data.get("video_video_restrict_access_to_groups", []),
            "video_id",
            "accessgroup_id",
            Video.restricted_groups.through,
            "video_id",
            "accessgroup_id",
            video_ids,
            accessgroup_ids,
            batch_size,
            "Video-RestrictedGroup",
        )

        self.import_m2m_relation(
            data.get("video_video_tags", []),
            "video_id",
            "tagulous_video_tags_id",
            Video.tags.through,
            "video_id",
            "tagulous_video_tags_id",
            video_ids,
            tag_ids,
            batch_size,
            "Video-Tag",
        )

        self.import_m2m_relation(
            data.get("video_video_theme", []),
            "video_id",
            "theme_id",
            ThemeItem,
            "video_id",
            "theme_id",
            video_ids,
            theme_ids,
            batch_size,
            "Theme-Video",
        )

        self.import_channel_collaborators(data, batch_size)

        self.import_m2m_relation(
            data.get("video_type_sites", []),
            "type_id",
            "site_id",
            Type.sites.through,
            "type_id",
            "site_id",
            type_ids,
            site_ids,
            batch_size,
            "Type-Site",
        )

    # ------------------------------------------------------------------
    # Superuser
    # ------------------------------------------------------------------

    def ensure_superuser_exists(self):
        """Check if a superuser is defined in the database, and create a default one if not."""
        superusers = User.objects.filter(is_superuser=True)
        if not superusers.exists():
            self.stdout.write(
                "No superuser found in the database. " "Creating a default superuser..."
            )
            username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin")
            email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "admin@example.com")
            password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "admin")

            try:
                User.objects.create_superuser(
                    username=username,
                    email=email,
                    password=password,
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Default superuser '{username}' " f"created successfully."
                    )
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error creating default superuser: {e}")
                )
        else:
            self.stdout.write(
                f"Superuser(s) found in the database "
                f"({superusers.count()} found). "
                f"Skipping default superuser creation."
            )

    # ------------------------------------------------------------------
    # Subtitles
    # ------------------------------------------------------------------

    def _validate_subtitle_item(self, item, existing_video_ids, custom_files):
        """Validate a subtitle item; return file_path or None."""
        v_id = item.get("video_id")
        if v_id not in existing_video_ids:
            logger.warning(
                f"Skipping subtitle {item['id']}: " f"Video V4 ID {v_id} not found in V5."
            )
            return None

        src_id = item.get("src_id")
        file_path = custom_files.get(src_id)
        if not file_path:
            logger.warning(
                f"Skipping subtitle {item['id']}: "
                f"CustomFileModel ID {src_id} not found "
                f"in V4 files dump."
            )
            return None
        return file_path

    def import_subtitles(self, items, data, batch_size):
        """Import subtitle tracks and resolve their target media file paths."""
        self.stdout.write("Importing Subtitles...")
        items_to_process = self._get_unprocessed_items("Subtitle", items)
        if not items_to_process:
            self.stdout.write("All Subtitles already migrated.")
            return

        existing_video_ids = set(Video.objects.values_list("id", flat=True))

        custom_files = {
            row["id"]: row["file"] for row in data.get("podfile_customfilemodel", [])
        }
        custom_files.update(
            {row["id"]: row["file"] for row in data.get("main_customfilemodel", [])}
        )

        from src.config.defaults import video as video_defaults

        valid_langs = {lang["value"] for lang in video_defaults.SUBTITLE_LANGUAGES}

        success_count = 0
        error_count = 0

        for i in range(0, len(items_to_process), batch_size):
            batch = items_to_process[i : i + batch_size]
            try:
                with transaction.atomic():
                    instances = []
                    mappings = []
                    for item in batch:
                        file_path = self._validate_subtitle_item(
                            item, existing_video_ids, custom_files
                        )
                        if not file_path:
                            continue

                        lang = item.get("lang") or "fr"
                        if lang not in valid_langs:
                            logger.warning(
                                f"Subtitle {item['id']} language "
                                f"'{lang}' is not in V5 choices, "
                                f"importing anyway."
                            )

                        instances.append(
                            Subtitle(
                                id=item["id"],
                                video_id=item.get("video_id"),
                                language=lang,
                                file=file_path,
                                is_default=False,
                            )
                        )
                        mappings.append(
                            MigrationMapping(
                                model_name="Subtitle",
                                v4_id=item["id"],
                                v5_id=item["id"],
                                status=MigrationMapping.Status.SUCCESS,
                            )
                        )

                    Subtitle.objects.bulk_create(instances, ignore_conflicts=True)
                    MigrationMapping.objects.bulk_create(mappings, ignore_conflicts=True)
                    success_count += len(instances)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error in Subtitle batch: {e}"))
                self._record_batch_errors("Subtitle", batch, e)
                error_count += len(batch)
        self.stdout.write(
            f"Subtitles imported: {success_count} success, " f"{error_count} errors."
        )

    # ------------------------------------------------------------------
    # Encoded Videos
    # ------------------------------------------------------------------

    def _validate_encoded_video_item(self, item, existing_video_ids):
        """Validate an encoded video item; return file_path or None."""
        v_id = item.get("video_id")
        if v_id not in existing_video_ids:
            logger.warning(
                f"Skipping encoded video {item['id']}: "
                f"Video V4 ID {v_id} not found in V5."
            )
            return None

        file_path = item.get("source_file")
        if not file_path:
            logger.warning(f"Skipping encoded video {item['id']}: " f"Empty source_file.")
            return None

        videos_dir = encoding_settings.videos_dir
        if videos_dir != "videos" and file_path.startswith("videos/"):
            file_path = file_path.replace("videos/", f"{videos_dir}/", 1)
        return file_path

    def import_encoded_videos(self, items, batch_size):
        """Import transcoding resolution profiles for the migrated videos."""
        self.stdout.write("Importing Encoded Videos...")
        items_to_process = self._get_unprocessed_items("EncodingVideo", items)
        if not items_to_process:
            self.stdout.write("All Encoded Videos already migrated.")
            return

        existing_video_ids = set(Video.objects.values_list("id", flat=True))

        success_count = 0
        error_count = 0

        for i in range(0, len(items_to_process), batch_size):
            batch = items_to_process[i : i + batch_size]
            try:
                with transaction.atomic():
                    instances = []
                    mappings = []
                    for item in batch:
                        file_path = self._validate_encoded_video_item(
                            item, existing_video_ids
                        )
                        if not file_path:
                            continue

                        resolution = item.get("name", "360p") or "360p"

                        instances.append(
                            EncodingVideo(
                                id=item["id"],
                                video_id=item.get("video_id"),
                                resolution=resolution,
                                file=file_path,
                            )
                        )
                        mappings.append(
                            MigrationMapping(
                                model_name="EncodingVideo",
                                v4_id=item["id"],
                                v5_id=item["id"],
                                status=MigrationMapping.Status.SUCCESS,
                            )
                        )

                    EncodingVideo.objects.bulk_create(instances, ignore_conflicts=True)
                    MigrationMapping.objects.bulk_create(mappings, ignore_conflicts=True)
                    success_count += len(instances)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error in Encoded Video batch: {e}"))
                self._record_batch_errors("EncodingVideo", batch, e)
                error_count += len(batch)
        self.stdout.write(
            f"Encoded Videos imported: {success_count} success, " f"{error_count} errors."
        )

    # ------------------------------------------------------------------
    # Blocks Configuration
    # ------------------------------------------------------------------

    def import_blocks(self, items, batch_size):
        """Import main_block from V4 to BlockConfig in V5."""
        self.stdout.write("Importing Block Configurations...")
        items_to_process = self._get_unprocessed_items("BlockConfig", items)
        if not items_to_process:
            self.stdout.write("All Blocks already migrated.")
            return

        success_count = 0
        error_count = 0

        for i in range(0, len(items_to_process), batch_size):
            batch = items_to_process[i : i + batch_size]
            try:
                with transaction.atomic():
                    instances = []
                    mappings = []
                    for item in batch:
                        t = item.get("type", "unknown")
                        dt = item.get("data_type", "unknown")
                        frontend_id = f"v4-{t}-{dt}-{item['id']}"

                        extra_config = {
                            "order": item.get("order"),
                            "type": t,
                            "data_type": dt,
                            "no_cache": item.get("no_cache"),
                            "show_restricted": item.get("show_restricted"),
                            "must_be_auth": item.get("must_be_auth"),
                            "auto_slide": item.get("auto_slide"),
                            "multi_carousel_nb": item.get("multi_carousel_nb"),
                            "view_videos_from_non_visible_channels": item.get(
                                "view_videos_from_non_visible_channels"
                            ),
                            "shows_passworded": item.get("shows_passworded"),
                        }

                        instances.append(
                            BlockConfig(
                                id=item["id"],
                                frontend_id=frontend_id,
                                admin_name=item.get("title", f"Block {item['id']}")[:150],
                                is_active=bool(item.get("visible", True)),
                                display_title=item.get("display_title", "")[:200],
                                subtitle_or_text="",
                                item_limit=(
                                    item.get("nb_element", 10)
                                    if item.get("nb_element") is not None
                                    else 10
                                ),
                                extra_config=extra_config,
                            )
                        )
                        mappings.append(
                            MigrationMapping(
                                model_name="BlockConfig",
                                v4_id=item["id"],
                                v5_id=item["id"],
                                status=MigrationMapping.Status.SUCCESS,
                            )
                        )

                    BlockConfig.objects.bulk_create(instances, ignore_conflicts=True)
                    MigrationMapping.objects.bulk_create(mappings, ignore_conflicts=True)
                    success_count += len(instances)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error in BlockConfig batch: {e}"))
                self._record_batch_errors("BlockConfig", batch, e)
                error_count += len(batch)
        self.stdout.write(
            f"Blocks imported: {success_count} success, {error_count} errors."
        )
