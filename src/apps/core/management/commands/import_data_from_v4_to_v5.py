
import logging
import os
from contextlib import nullcontext as dummy_context
from datetime import date, datetime
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.contrib.sites.models import Site
from django.db import transaction, connection
from django.db.models.signals import post_save, pre_save, post_delete
from django.utils import timezone
from django.utils.timezone import make_aware, is_naive
from django.utils.dateparse import parse_datetime
from django.utils.text import slugify
from django.conf import settings

from src.apps.authentication.models import Owner, AccessGroup, GroupSite
from src.apps.authentication.models.Owner import create_owner_profile, default_site_owner
from src.apps.authentication.models.GroupSite import create_groupsite_profile, default_site_groupsite
from src.apps.collection.models import Channel, Theme, ThemeItem, Playlist, PlaylistItem
import html
from django.utils.html import strip_tags

def clean_html(text):
    if not text:
        return text
    return html.unescape(strip_tags(text))

from src.apps.video.models import Video, Type, Discipline, ViewCount, Comment, Vote, Subtitle
from src.apps.encoding.models import EncodingVideo
from src.apps.encoding.conf import encoding_settings
from django.db import models

class MigrationMapping(models.Model):
    class Status(models.TextChoices):
        SUCCESS = 'SUCCESS', 'Success'
        ERROR = 'ERROR', 'Error'
        IGNORED = 'IGNORED', 'Ignored'
        
    model_name = models.CharField(max_length=50, db_index=True)
    v4_id = models.IntegerField(db_index=True)
    v5_id = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, db_index=True)
    message = models.TextField(blank=True)

    class Meta:
        app_label = 'core'
        db_table = 'core_migrationmapping'
        unique_together = ('model_name', 'v4_id')

from src.apps.video.signals import (
    set_video_slug,
    auto_delete_file_on_delete,
    auto_delete_file_on_change,
    video_post_save,
    auto_assign_site_to_video,
    auto_assign_site_to_type
)

logger = logging.getLogger(__name__)

class DryRunRollbackException(Exception):
    """Exception raised to rollback transaction in dry-run mode."""
    pass

class Command(BaseCommand):
    help = "Import data (Users, Videos, Playlists, relations) from Pod v4 to Pod v5"

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='.tmp/v4_exported_to_v5.json',
            help='Path to the JSON file exported from Pod V4'
        )
        parser.add_argument(
            '--verify-files',
            action='store_true',
            help='Verify media files existence in /media/'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulate migration and rollback at the end'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='Number of records to process per database transaction/batch'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        dry_run = options['dry_run']
        batch_size = options['batch_size']

        if dry_run:
            self.stdout.write(self.style.WARNING("WARNING: Running in DRY-RUN mode. No changes will be written to the database."))

        class LazyJSONData:
            def __init__(self, file_path, stdout, style):
                self.file_path = file_path
                self.stdout = stdout
                self.style = style

            def get(self, key, default=None):
                import ijson
                try:
                    with open(self.file_path, 'rb') as f:
                        items = list(ijson.items(f, f'{key}.item'))
                        return items if items else (default if default is not None else [])
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error reading '{key}' with ijson: {e}"))
                    return default if default is not None else []

        data = LazyJSONData(file_path, self.stdout, self.style)

        # Ensure the MigrationMapping table exists dynamically
        if MigrationMapping._meta.db_table not in connection.introspection.table_names():
            try:
                with connection.schema_editor() as schema_editor:
                    schema_editor.create_model(MigrationMapping)
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Warning creating MigrationMapping table: {e}"))

        self.stdout.write(self.style.SUCCESS("*** Start importing data from V4 to V5 ***"))

        # Pre-create all django sites listed in V4 dump
        self.pre_create_sites(data.get('django_site', []))

        # Disable signals to prevent conflicts and improve performances
        self.disconnect_signals()

        # Wrap in a single transaction if dry_run
        transaction_context = transaction.atomic() if dry_run else dummy_context()

        try:
            with transaction_context:
                # 1. Users, groups, and auth profiles
                self.import_users(data.get('auth_user', []), batch_size)
                self.import_owners(data.get('authentication_owner', []), batch_size)
                self.import_groups(data.get('auth_group', []), batch_size)
                self.import_accessgroups(data.get('authentication_accessgroup', []), batch_size)
                self.import_groupsites(data.get('authentication_groupsite', []), batch_size)

                # 2. Prereqs for videos (Types, Disciplines, Channels, Themes)
                self.import_types(data.get('video_type', []), batch_size)
                self.import_disciplines(data.get('video_discipline', []), batch_size)
                self.import_channels(data.get('video_channel', []), data, batch_size)
                self.import_themes(data.get('video_theme', []), batch_size)

                # 3. Videos
                self.import_video_tags(data)
                self.import_videos(data.get('video_video', []), data, options)

                # 4. Playlists
                self.import_playlists(data.get('playlist_playlist', []), batch_size)
                self.import_playlist_contents(data.get('playlist_playlistcontent', []), data.get('playlist_playlist', []), batch_size)

                # 5. Extra entities: Comments, Votes, ViewCounts
                self.import_comments(data.get('video_comment', []), batch_size)
                self.import_votes(data.get('video_vote', []), batch_size)
                self.import_viewcounts(data.get('video_viewcount', []), batch_size)

                # 6. Relations (ManyToMany join tables)
                self.import_relations(data, batch_size)

                # 7. Subtitles and Encoded resolutions
                self.import_subtitles(data.get('completion_track', []), data, batch_size)
                self.import_encoded_videos(data.get('video_encode_transcript_encodingvideo', []), batch_size)

                if dry_run:
                    self.stdout.write(self.style.SUCCESS("Dry run completed successfully. Rolling back database changes..."))
                    raise DryRunRollbackException("Dry run rollback")

                # Ensure at least one superuser exists in the target database
                self.ensure_superuser_exists()
                    
                self.stdout.write(self.style.SUCCESS("Migration completed successfully!"))
        except DryRunRollbackException:
            logger.info("Dry-run transaction rolled back.")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error during import: {e}"))
            logger.exception("Error during data import")
        finally:
            # Reconnect signals
            self.reconnect_signals()
            self.stdout.write(self.style.SUCCESS("*** Finished migration process ***"))

    def disconnect_signals(self):
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
        for item in items:
            Site.objects.get_or_create(
                id=item['id'],
                defaults={
                    'domain': item.get('domain', f"site{item['id']}.com"),
                    'name': item.get('name', f"Site {item['id']}")
                }
            )

    def import_users(self, items, batch_size):
        self.stdout.write("Importing Users...")
        migrated_ids = set(MigrationMapping.objects.filter(model_name="User", status="SUCCESS").values_list("v4_id", flat=True))
        
        items_to_process = [item for item in items if item['id'] not in migrated_ids]
        if not items_to_process:
            self.stdout.write("All Users already migrated.")
            return

        success_count = 0
        error_count = 0
        
        for i in range(0, len(items_to_process), batch_size):
            batch = items_to_process[i:i+batch_size]
            try:
                with transaction.atomic():
                    instances = []
                    mappings = []
                    for item in batch:
                        defaults = {
                            'id': item['id'],
                            'password': item.get('password', ''),
                            'is_superuser': item.get('is_superuser', False),
                            'username': item.get('username'),
                            'first_name': item.get('first_name', ''),
                            'last_name': item.get('last_name', ''),
                            'email': item.get('email', ''),
                            'is_staff': item.get('is_staff', False),
                            'is_active': item.get('is_active', True),
                        }
                        if item.get('last_login'):
                            dt = parse_datetime(item['last_login'])
                            if dt:
                                defaults['last_login'] = make_aware(dt) if is_naive(dt) else dt
                        if item.get('date_joined'):
                            dt = parse_datetime(item['date_joined'])
                            if dt:
                                defaults['date_joined'] = make_aware(dt) if is_naive(dt) else dt
                        
                        instances.append(User(**defaults))
                        mappings.append(MigrationMapping(
                            model_name="User",
                            v4_id=item['id'],
                            v5_id=item['id'],
                            status=MigrationMapping.Status.SUCCESS
                        ))
                    
                    User.objects.bulk_create(instances, ignore_conflicts=True)
                    MigrationMapping.objects.bulk_create(mappings, ignore_conflicts=True)
                    success_count += len(batch)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error in User batch: {e}"))
                try:
                    with transaction.atomic():
                        err_mappings = [
                            MigrationMapping(
                                model_name="User",
                                v4_id=item['id'],
                                status=MigrationMapping.Status.ERROR,
                                message=str(e)
                            )
                            for item in batch
                        ]
                        MigrationMapping.objects.bulk_create(err_mappings, ignore_conflicts=True)
                except Exception as inner_e:
                    logger.warning(f"Could not record migration error to database: {inner_e}")
                error_count += len(batch)
        self.stdout.write(f"Users imported: {success_count} success, {error_count} errors.")

    def import_owners(self, items, batch_size):
        self.stdout.write("Importing Owners...")
        migrated_ids = set(MigrationMapping.objects.filter(model_name="Owner", status="SUCCESS").values_list("v4_id", flat=True))
        existing_user_ids = set(User.objects.values_list("id", flat=True))
        existing_owner_users = set(Owner.objects.values_list("user_id", flat=True))

        items_to_process = [item for item in items if item['id'] not in migrated_ids]
        if not items_to_process:
            self.stdout.write("All Owners already migrated.")
            return

        success_count = 0
        error_count = 0
        ignored_count = 0

        for i in range(0, len(items_to_process), batch_size):
            batch = items_to_process[i:i+batch_size]
            try:
                with transaction.atomic():
                    instances = []
                    mappings = []
                    for item in batch:
                        user_id = item.get('user_id')
                        if user_id not in existing_user_ids:
                            ignored_count += 1
                            mappings.append(MigrationMapping(
                                model_name="Owner",
                                v4_id=item['id'],
                                status=MigrationMapping.Status.IGNORED,
                                message=f"User ID {user_id} does not exist"
                            ))
                            continue
                        if user_id in existing_owner_users:
                            # Owner profile already created, skip creating duplicate
                            mappings.append(MigrationMapping(
                                model_name="Owner",
                                v4_id=item['id'],
                                v5_id=item['id'],
                                status=MigrationMapping.Status.SUCCESS
                            ))
                            success_count += 1
                            continue

                        defaults = {
                            'id': item['id'],
                            'user_id': user_id,
                            'auth_type': item.get('auth_type', 'local') or 'local',
                            'affiliation': item.get('affiliation', 'member') or 'member',
                            'comment': item.get('comment', '') or '',
                            'hashkey': item.get('hashkey', '') or '',
                            'userpicture': item.get('userpicture', '') or '',
                            'establishment': item.get('establishment', 'U1') or 'U1',
                            'accepts_notifications': item.get('accepts_notifications'),
                        }
                        instances.append(Owner(**defaults))
                        mappings.append(MigrationMapping(
                            model_name="Owner",
                            v4_id=item['id'],
                            v5_id=item['id'],
                            status=MigrationMapping.Status.SUCCESS
                        ))

                    if instances:
                        Owner.objects.bulk_create(instances, ignore_conflicts=True)
                    MigrationMapping.objects.bulk_create(mappings, ignore_conflicts=True)
                    success_count += len(instances)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error in Owner batch: {e}"))
                try:
                    with transaction.atomic():
                        err_mappings = [
                            MigrationMapping(
                                model_name="Owner",
                                v4_id=item['id'],
                                status=MigrationMapping.Status.ERROR,
                                message=str(e)
                            )
                            for item in batch
                        ]
                        MigrationMapping.objects.bulk_create(err_mappings, ignore_conflicts=True)
                except Exception as inner_e:
                    logger.warning(f"Could not record migration error to database: {inner_e}")
                error_count += len(batch)
        self.stdout.write(f"Owners imported: {success_count} success, {error_count} errors, {ignored_count} ignored.")

    def import_groups(self, items, batch_size):
        self.stdout.write("Importing Groups...")
        migrated_ids = set(MigrationMapping.objects.filter(model_name="Group", status="SUCCESS").values_list("v4_id", flat=True))
        items_to_process = [item for item in items if item['id'] not in migrated_ids]
        if not items_to_process:
            self.stdout.write("All Groups already migrated.")
            return

        success_count = 0
        error_count = 0

        for i in range(0, len(items_to_process), batch_size):
            batch = items_to_process[i:i+batch_size]
            try:
                with transaction.atomic():
                    instances = []
                    mappings = []
                    for item in batch:
                        instances.append(Group(id=item['id'], name=item['name'][:150]))
                        mappings.append(MigrationMapping(
                            model_name="Group",
                            v4_id=item['id'],
                            v5_id=item['id'],
                            status=MigrationMapping.Status.SUCCESS
                        ))
                    Group.objects.bulk_create(instances, ignore_conflicts=True)
                    MigrationMapping.objects.bulk_create(mappings, ignore_conflicts=True)
                    success_count += len(instances)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error in Group batch: {e}"))
                error_count += len(batch)
        self.stdout.write(f"Groups imported: {success_count} success, {error_count} errors.")

    def import_accessgroups(self, items, batch_size):
        self.stdout.write("Importing AccessGroups...")
        migrated_ids = set(MigrationMapping.objects.filter(model_name="AccessGroup", status="SUCCESS").values_list("v4_id", flat=True))
        items_to_process = [item for item in items if item['id'] not in migrated_ids]
        if not items_to_process:
            self.stdout.write("All AccessGroups already migrated.")
            return

        success_count = 0
        error_count = 0

        for i in range(0, len(items_to_process), batch_size):
            batch = items_to_process[i:i+batch_size]
            try:
                with transaction.atomic():
                    instances = []
                    mappings = []
                    for item in batch:
                        instances.append(AccessGroup(
                            id=item['id'],
                            display_name=item.get('display_name', '') or '',
                            code_name=item.get('code_name', '') or '',
                            auto_sync=item.get('auto_sync', False)
                        ))
                        mappings.append(MigrationMapping(
                            model_name="AccessGroup",
                            v4_id=item['id'],
                            v5_id=item['id'],
                            status=MigrationMapping.Status.SUCCESS
                        ))
                    AccessGroup.objects.bulk_create(instances, ignore_conflicts=True)
                    MigrationMapping.objects.bulk_create(mappings, ignore_conflicts=True)
                    success_count += len(instances)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error in AccessGroup batch: {e}"))
                error_count += len(batch)
        self.stdout.write(f"AccessGroups imported: {success_count} success, {error_count} errors.")

    def import_groupsites(self, items, batch_size):
        self.stdout.write("Importing GroupSites...")
        migrated_ids = set(MigrationMapping.objects.filter(model_name="GroupSite", status="SUCCESS").values_list("v4_id", flat=True))
        existing_group_ids = set(Group.objects.values_list("id", flat=True))

        items_to_process = [item for item in items if item['id'] not in migrated_ids]
        if not items_to_process:
            self.stdout.write("All GroupSites already migrated.")
            return

        success_count = 0
        error_count = 0
        ignored_count = 0

        for i in range(0, len(items_to_process), batch_size):
            batch = items_to_process[i:i+batch_size]
            try:
                with transaction.atomic():
                    instances = []
                    mappings = []
                    for item in batch:
                        g_id = item.get('group_id')
                        if g_id not in existing_group_ids:
                            ignored_count += 1
                            continue
                        instances.append(GroupSite(
                            id=item['id'],
                            group_id=g_id
                        ))
                        mappings.append(MigrationMapping(
                            model_name="GroupSite",
                            v4_id=item['id'],
                            v5_id=item['id'],
                            status=MigrationMapping.Status.SUCCESS
                        ))
                    if instances:
                        GroupSite.objects.bulk_create(instances, ignore_conflicts=True)
                    MigrationMapping.objects.bulk_create(mappings, ignore_conflicts=True)
                    success_count += len(instances)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error in GroupSite batch: {e}"))
                error_count += len(batch)
        self.stdout.write(f"GroupSites imported: {success_count} success, {error_count} errors, {ignored_count} ignored.")

    def import_types(self, items, batch_size):
        self.stdout.write("Importing Types...")
        migrated_ids = set(MigrationMapping.objects.filter(model_name="Type", status="SUCCESS").values_list("v4_id", flat=True))
        items_to_process = [item for item in items if item['id'] not in migrated_ids]
        if not items_to_process:
            self.stdout.write("All Types already migrated.")
            return

        success_count = 0
        error_count = 0

        for i in range(0, len(items_to_process), batch_size):
            batch = items_to_process[i:i+batch_size]
            try:
                with transaction.atomic():
                    instances = []
                    mappings = []
                    for item in batch:
                        slug = item.get('slug') or slugify(item['title'])
                        instances.append(Type(
                            id=item['id'],
                            title=item['title'][:100],
                            slug=slug[:100]
                        ))
                        mappings.append(MigrationMapping(
                            model_name="Type",
                            v4_id=item['id'],
                            v5_id=item['id'],
                            status=MigrationMapping.Status.SUCCESS
                        ))
                    Type.objects.bulk_create(instances, ignore_conflicts=True)
                    MigrationMapping.objects.bulk_create(mappings, ignore_conflicts=True)
                    success_count += len(instances)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error in Type batch: {e}"))
                error_count += len(batch)
        self.stdout.write(f"Types imported: {success_count} success, {error_count} errors.")

    def import_disciplines(self, items, batch_size):
        self.stdout.write("Importing Disciplines...")
        migrated_ids = set(MigrationMapping.objects.filter(model_name="Discipline", status="SUCCESS").values_list("v4_id", flat=True))
        items_to_process = [item for item in items if item['id'] not in migrated_ids]
        if not items_to_process:
            self.stdout.write("All Disciplines already migrated.")
            return

        success_count = 0
        error_count = 0

        for i in range(0, len(items_to_process), batch_size):
            batch = items_to_process[i:i+batch_size]
            try:
                with transaction.atomic():
                    instances = []
                    mappings = []
                    for item in batch:
                        instances.append(Discipline(
                            id=item['id'],
                            title=item['title'][:100],
                            slug=item.get('slug', '')[:255] or slugify(item['title'])[:255],
                            description=clean_html(item.get('description', '') or '')
                        ))
                        mappings.append(MigrationMapping(
                            model_name="Discipline",
                            v4_id=item['id'],
                            v5_id=item['id'],
                            status=MigrationMapping.Status.SUCCESS
                        ))
                    Discipline.objects.bulk_create(instances, ignore_conflicts=True)
                    MigrationMapping.objects.bulk_create(mappings, ignore_conflicts=True)
                    success_count += len(instances)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error in Discipline batch: {e}"))
                error_count += len(batch)
        self.stdout.write(f"Disciplines imported: {success_count} success, {error_count} errors.")

    def import_channels(self, items, data, batch_size):
        self.stdout.write("Importing Channels...")
        migrated_ids = set(MigrationMapping.objects.filter(model_name="Channel", status="SUCCESS").values_list("v4_id", flat=True))
        existing_user_ids = set(User.objects.values_list("id", flat=True))
        first_user_id = User.objects.first().id if User.objects.exists() else 1

        # Build owners map
        channel_owners_map = {}
        for row in data.get('video_channel_owners', []):
            c_id = row['channel_id']
            u_id = row['user_id']
            if c_id not in channel_owners_map:
                channel_owners_map[c_id] = []
            channel_owners_map[c_id].append(u_id)

        items_to_process = [item for item in items if item['id'] not in migrated_ids]
        if not items_to_process:
            self.stdout.write("All Channels already migrated.")
            return

        success_count = 0
        error_count = 0

        for i in range(0, len(items_to_process), batch_size):
            batch = items_to_process[i:i+batch_size]
            try:
                with transaction.atomic():
                    instances = []
                    mappings = []
                    for item in batch:
                        c_id = item['id']
                        owners = channel_owners_map.get(c_id, [])
                        valid_owners = [o for o in owners if o in existing_user_ids]
                        
                        owner_id = valid_owners[0] if valid_owners else first_user_id
                        
                        defaults = {
                            'id': c_id,
                            'title': item['title'][:250],
                            'slug': item.get('slug', '')[:255] or slugify(item['title'])[:255],
                            'description': clean_html(item.get('description', '') or ''),
                            'is_public': item.get('visible', True),
                            'owner_id': owner_id,
                            'old_v4_id': c_id,
                        }
                        instances.append(Channel(**defaults))
                        mappings.append(MigrationMapping(
                            model_name="Channel",
                            v4_id=c_id,
                            v5_id=c_id,
                            status=MigrationMapping.Status.SUCCESS
                        ))
                    
                    Channel.objects.bulk_create(instances, ignore_conflicts=True)
                    MigrationMapping.objects.bulk_create(mappings, ignore_conflicts=True)
                    success_count += len(instances)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error in Channel batch: {e}"))
                try:
                    with transaction.atomic():
                        err_mappings = [
                            MigrationMapping(
                                model_name="Channel",
                                v4_id=item['id'],
                                status=MigrationMapping.Status.ERROR,
                                message=str(e)
                            )
                            for item in batch
                        ]
                        MigrationMapping.objects.bulk_create(err_mappings, ignore_conflicts=True)
                except Exception as inner_e:
                    logger.warning(f"Could not record migration error to database: {inner_e}")
                error_count += len(batch)
        self.stdout.write(f"Channels imported: {success_count} success, {error_count} errors.")

    def import_themes(self, items, batch_size):
        self.stdout.write("Importing Themes (Pass 1 - without parents)...")
        migrated_ids = set(MigrationMapping.objects.filter(model_name="Theme", status="SUCCESS").values_list("v4_id", flat=True))
        existing_channel_ids = set(Channel.objects.values_list("id", flat=True))
        existing_slugs = set(Theme.objects.values_list("slug", flat=True))

        items_to_process = [item for item in items if item['id'] not in migrated_ids]
        if not items_to_process:
            self.stdout.write("All Themes already migrated.")
            return

        success_count = 0
        error_count = 0

        # Pass 1: create them with parent_id = None
        for i in range(0, len(items_to_process), batch_size):
            batch = items_to_process[i:i+batch_size]
            try:
                with transaction.atomic():
                    instances = []
                    mappings = []
                    for item in batch:
                        c_id = item.get('channel_id')
                        if c_id not in existing_channel_ids:
                            c_id = None
                            
                        base_slug = item.get('slug') or slugify(item['title'])
                        base_slug = base_slug[:240]  # Leave room for suffix
                        slug = base_slug
                        counter = 1
                        while slug in existing_slugs:
                            slug = f"{base_slug}-{counter}"
                            counter += 1
                        existing_slugs.add(slug)
                        
                        defaults = {
                            'id': item['id'],
                            'title': item['title'][:250],
                            'slug': slug[:255],
                            'description': clean_html(item.get('description', '') or ''),
                            'channel_id': c_id,
                            'parent_id': None,
                            'old_v4_id': item['id'],
                        }
                        instances.append(Theme(**defaults))
                        mappings.append(MigrationMapping(
                            model_name="Theme",
                            v4_id=item['id'],
                            v5_id=item['id'],
                            status=MigrationMapping.Status.SUCCESS
                        ))
                    
                    Theme.objects.bulk_create(instances, ignore_conflicts=True)
                    MigrationMapping.objects.bulk_create(mappings, ignore_conflicts=True)
                    success_count += len(instances)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error in Theme batch (Pass 1): {e}"))
                try:
                    with transaction.atomic():
                        err_mappings = [
                            MigrationMapping(
                                model_name="Theme",
                                v4_id=item['id'],
                                status=MigrationMapping.Status.ERROR,
                                message=str(e)
                            )
                            for item in batch
                        ]
                        MigrationMapping.objects.bulk_create(err_mappings, ignore_conflicts=True)
                except Exception as inner_e:
                    logger.warning(f"Could not record migration error to database: {inner_e}")
                error_count += len(batch)
        
        # Pass 2: Set parent_id
        self.stdout.write("Updating Theme parents (Pass 2)...")
        existing_theme_ids = set(Theme.objects.values_list("id", flat=True))
        themes_to_update = []
        for item in items:
            t_id = item['id']
            p_id = item.get('parentId_id')
            if p_id and p_id in existing_theme_ids and t_id in existing_theme_ids:
                if t_id != p_id:
                    themes_to_update.append(Theme(id=t_id, parent_id=p_id))
        
        if themes_to_update:
            for i in range(0, len(themes_to_update), batch_size):
                batch = themes_to_update[i:i+batch_size]
                try:
                    with transaction.atomic():
                        Theme.objects.bulk_update(batch, ['parent_id'])
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error updating Theme parents batch: {e}"))

        self.stdout.write(f"Themes imported: {success_count} success, {error_count} errors.")

    def import_video_tags(self, data):
        self.stdout.write("Importing Video Tags...")
        tag_model = Video.tags.tag_model
        v4_tags = data.get('video_tagulous_video_tags', [])
        
        tags_to_create = []
        existing_tags = set(tag_model.objects.values_list('name', flat=True))
        
        for item in v4_tags:
            name = item['name']
            if name not in existing_tags:
                slug = item.get('slug') or slugify(name)
                tags_to_create.append(tag_model(
                    id=item['id'],
                    name=name[:80],
                    slug=slug[:50],
                    count=item.get('count', 0),
                    protected=item.get('protected', False)
                ))
                existing_tags.add(name)
                
        if tags_to_create:
            tag_model.objects.bulk_create(tags_to_create, ignore_conflicts=True)
            self.stdout.write(f"Created {len(tags_to_create)} tags.")

    def get_v5_cursus(self, v4_cursus):
        if v4_cursus == 'L':
            return 'L1'
        elif v4_cursus == 'M':
            return 'M1'
        elif v4_cursus == 'D':
            return 'D'
        return '0'

    def get_v5_status(self, is_draft, is_restricted):
        if is_draft:
            return 'DR'
        elif is_restricted:
            return 'RE'
        return 'PU'

    def get_v5_license(self, v4_license):
        if not v4_license:
            return 'COPYRIGHT'
        v4_license_upper = v4_license.upper()
        if 'CC-BY-SA' in v4_license_upper:
            return 'CC-BY-SA'
        elif 'CC-BY-NC' in v4_license_upper:
            return 'CC-BY-NC'
        elif 'CC-BY-ND' in v4_license_upper:
            return 'CC-BY-ND'
        elif 'CC-BY' in v4_license_upper:
            return 'CC-BY'
        return 'COPYRIGHT'

    def import_videos(self, items, data, options):
        self.stdout.write("Importing Videos...")
        batch_size = options['batch_size']
        verify_files = options['verify_files']
        
        migrated_ids = set(MigrationMapping.objects.filter(model_name="Video", status="SUCCESS").values_list("v4_id", flat=True))
        existing_user_ids = set(User.objects.values_list("id", flat=True))
        existing_type_ids = set(Type.objects.values_list("id", flat=True))
        existing_channel_ids = set(Channel.objects.values_list("id", flat=True))
        first_user_id = User.objects.first().id if User.objects.exists() else 1

        # Maps
        custom_images = {row['id']: row['file'] for row in data.get('main_customimagemodel', [])}
        video_channels = {row['video_id']: row['channel_id'] for row in data.get('video_video_channel', [])}
        
        items_to_process = [item for item in items if item['id'] not in migrated_ids]
        if not items_to_process:
            self.stdout.write("All Videos already migrated.")
            return

        success_count = 0
        error_count = 0
        missing_files_video_ids = set()

        for i in range(0, len(items_to_process), batch_size):
            batch = items_to_process[i:i+batch_size]
            try:
                with transaction.atomic():
                    instances = []
                    mappings = []
                    for item in batch:
                        v_id = item['id']
                        owner_id = item.get('owner_id')
                        if owner_id not in existing_user_ids:
                            owner_id = first_user_id
                            
                        type_id = item.get('type_id')
                        if type_id not in existing_type_ids:
                            type_id = None
                            
                        channel_id = video_channels.get(v_id)
                        if channel_id not in existing_channel_ids:
                            channel_id = None

                        video_file = item.get('video', '')
                        videos_dir = encoding_settings.videos_dir
                        if videos_dir != "videos" and video_file and video_file.startswith("videos/"):
                            video_file = video_file.replace("videos/", f"{videos_dir}/", 1)
                        if verify_files and video_file:
                            file_path = os.path.join(settings.MEDIA_ROOT, video_file)
                            if not os.path.exists(file_path):
                                self.stdout.write(self.style.WARNING(f"Video V4 ID {v_id} file not found: {file_path}"))
                                missing_files_video_ids.add(v_id)

                        created_at = timezone.now()
                        if item.get('date_added'):
                            dt = parse_datetime(item['date_added'])
                            if dt:
                                created_at = make_aware(dt) if is_naive(dt) else dt
                                
                        date_of_event = None
                        if item.get('date_evt'):
                            try:
                                date_of_event = parse_datetime(item['date_evt'] + " 00:00:00").date()
                            except Exception as date_e:
                                logger.warning(f"Could not parse date_evt '{item.get('date_evt')}' for video {item['id']}: {date_e}")
                                
                        date_to_delete = None
                        if item.get('date_delete'):
                            try:
                                date_to_delete = parse_datetime(item['date_delete'] + " 00:00:00").date()
                            except Exception as date_e:
                                logger.warning(f"Could not parse date_delete '{item.get('date_delete')}' for video {item['id']}: {date_e}")

                        thumbnail_path = None
                        thumb_id = item.get('thumbnail_id')
                        if thumb_id in custom_images:
                            thumbnail_path = custom_images[thumb_id]
                            thumbnails_dir = encoding_settings.thumbnails_dir
                            if thumbnails_dir != "thumbnails" and thumbnail_path and thumbnail_path.startswith("thumbnails/"):
                                thumbnail_path = thumbnail_path.replace("thumbnails/", f"{thumbnails_dir}/", 1)

                        encoding_status = 'DO'
                        if item.get('encoding_in_progress'):
                            encoding_status = 'PR'

                        defaults = {
                            'id': v_id,
                            'title': item['title'][:250],
                            'slug': item['slug'][:255],
                            'description': clean_html(item.get('description', '') or ''),
                            'video_file': video_file or None,
                            'is_video': item.get('is_video', True),
                            'thumbnail': thumbnail_path,
                            'overview': clean_html(item.get('overview', '') or '') or None,
                            'duration': item.get('duration', 0),
                            'view_count': item.get('view_count', 0),
                            'is_360': item.get('is_360', False),
                            'owner_id': owner_id,
                            'channel_id': channel_id,
                            'status': self.get_v5_status(item.get('is_draft', False), item.get('is_restricted', False)),
                            'encoding_status': encoding_status,
                            'is_auth_required': item.get('is_restricted', False),
                            'password': item.get('password', '') or None,
                            'allow_downloading': item.get('allow_downloading', False),
                            'disable_comment': item.get('disable_comment', False),
                            'order': item.get('order', 1),
                            'date_of_event': date_of_event,
                            'license': self.get_v5_license(item.get('licence')),
                            'cursus': self.get_v5_cursus(item.get('cursus')),
                            'language': item.get('main_lang', 'fr')[:10],
                            'transcript_language': item.get('transcript', '')[:10],
                            'created_at': created_at,
                            'date_to_delete': date_to_delete,
                        }
                        
                        instances.append(Video(**defaults))
                        mappings.append(MigrationMapping(
                            model_name="Video",
                            v4_id=v_id,
                            v5_id=v_id,
                            status=MigrationMapping.Status.SUCCESS
                        ))

                    if instances:
                        Video.objects.bulk_create(instances, ignore_conflicts=True)
                    MigrationMapping.objects.bulk_create(mappings, ignore_conflicts=True)
                    success_count += len(instances)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error in Video batch: {e}"))
                try:
                    with transaction.atomic():
                        err_mappings = [
                            MigrationMapping(
                                model_name="Video",
                                v4_id=item['id'],
                                status=MigrationMapping.Status.ERROR,
                                message=str(e)
                            )
                            for item in batch
                        ]
                        MigrationMapping.objects.bulk_create(err_mappings, ignore_conflicts=True)
                except Exception as inner_e:
                    logger.warning(f"Could not record migration error to database: {inner_e}")
                error_count += len(batch)
                
        # Link missing file tags if any
        if missing_files_video_ids:
            self.stdout.write("Tagging videos with missing files...")
            tag_model = Video.tags.tag_model
            missing_tag, _ = tag_model.objects.get_or_create(name='Fichier égaré', defaults={'slug': 'fichier-egare'})
            through_model = Video.tags.through
            
            relations_to_create = []
            existing_relations = set(through_model.objects.filter(tagulous_video_tags_id=missing_tag.id).values_list('video_id', flat=True))
            
            for v_id in missing_files_video_ids:
                if v_id not in existing_relations:
                    relations_to_create.append(through_model(video_id=v_id, tagulous_video_tags_id=missing_tag.id))
            
            if relations_to_create:
                through_model.objects.bulk_create(relations_to_create, ignore_conflicts=True)
                
        self.stdout.write(f"Videos imported: {success_count} success, {error_count} errors.")

    def import_playlists(self, items, batch_size):
        self.stdout.write("Importing Playlists...")
        migrated_ids = set(MigrationMapping.objects.filter(model_name="Playlist").values_list("v4_id", flat=True))
        existing_user_ids = set(User.objects.values_list("id", flat=True))
        first_user_id = User.objects.first().id if User.objects.exists() else 1

        items_to_process = [item for item in items if item['id'] not in migrated_ids]
        if not items_to_process:
            self.stdout.write("All Playlists already migrated.")
            return

        success_count = 0
        ignored_count = 0
        error_count = 0

        for i in range(0, len(items_to_process), batch_size):
            batch = items_to_process[i:i+batch_size]
            try:
                with transaction.atomic():
                    instances = []
                    mappings = []
                    for item in batch:
                        if item.get('name') == 'Favorites':
                            ignored_count += 1
                            mappings.append(MigrationMapping(
                                model_name="Playlist",
                                v4_id=item['id'],
                                v5_id=None,
                                status=MigrationMapping.Status.IGNORED,
                                message="Favorites playlist"
                            ))
                            continue

                        owner_id = item.get('owner_id')
                        if owner_id not in existing_user_ids:
                            owner_id = first_user_id
                            
                        slug = item.get('slug') or slugify(item['name'])
                        
                        defaults = {
                            'id': item['id'],
                            'title': item['name'][:250],
                            'slug': slug[:255],
                            'description': clean_html(item.get('description', '') or ''),
                            'owner_id': owner_id,
                            'is_public': item.get('visibility') in ['public', 'protected'],
                            'password': item.get('password', '') or None,
                            'old_v4_id': item['id'],
                        }
                        
                        instances.append(Playlist(**defaults))
                        mappings.append(MigrationMapping(
                            model_name="Playlist",
                            v4_id=item['id'],
                            v5_id=item['id'],
                            status=MigrationMapping.Status.SUCCESS
                        ))
                    
                    if instances:
                        Playlist.objects.bulk_create(instances, ignore_conflicts=True)
                    MigrationMapping.objects.bulk_create(mappings, ignore_conflicts=True)
                    success_count += len(instances)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error in Playlist batch: {e}"))
                try:
                    with transaction.atomic():
                        err_mappings = []
                        for item in batch:
                            err_mappings.append(MigrationMapping(
                                model_name="Playlist",
                                v4_id=item['id'],
                                status=MigrationMapping.Status.ERROR,
                                message=str(e)
                            ))
                        MigrationMapping.objects.bulk_create(err_mappings, ignore_conflicts=True)
                except Exception as inner_e:
                    logger.warning(f"Could not record migration error to database: {inner_e}")
                error_count += len(batch)
        self.stdout.write(f"Playlists imported: {success_count} success, {ignored_count} ignored (Favorites), {error_count} errors.")

    def import_playlist_contents(self, items, playlist_items, batch_size):
        self.stdout.write("Importing Playlist Contents & Favorites...")
        
        # Build a map of V4 playlist ID -> (name, owner_id)
        playlist_map = {item['id']: (item['name'], item['owner_id']) for item in playlist_items}
        
        existing_playlists = set(Playlist.objects.values_list("id", flat=True))
        existing_videos = set(Video.objects.values_list("id", flat=True))
        existing_users = set(User.objects.values_list("id", flat=True))
        
        from src.apps.collection.models.Favorite import Favorite
        
        existing_playlist_relations = set(PlaylistItem.objects.values_list("playlist_id", "video_id"))
        existing_favorite_relations = set(Favorite.objects.values_list("user_id", "video_id"))

        playlist_items_to_create = []
        favorites_to_create = []
        
        playlist_contents_count = 0
        favorites_count = 0
        ignored_count = 0

        for item in items:
            p_id = item['playlist_id']
            v_id = item['video_id']
            
            if v_id not in existing_videos:
                ignored_count += 1
                continue
                
            # Check if this playlist is a "Favorites" playlist
            playlist_info = playlist_map.get(p_id)
            if playlist_info and playlist_info[0] == 'Favorites':
                owner_id = playlist_info[1]
                if owner_id in existing_users:
                    if (owner_id, v_id) not in existing_favorite_relations:
                        favorites_to_create.append(Favorite(
                            user_id=owner_id,
                            video_id=v_id
                        ))
                        existing_favorite_relations.add((owner_id, v_id))
                else:
                    ignored_count += 1
                continue
            
            # Regular playlist content
            if p_id not in existing_playlists:
                ignored_count += 1
                continue
                
            if (p_id, v_id) not in existing_playlist_relations:
                rank = item.get('rank', 0)
                playlist_items_to_create.append(PlaylistItem(
                    playlist_id=p_id,
                    video_id=v_id,
                    position=rank if rank > 0 else 1
                ))
                existing_playlist_relations.add((p_id, v_id))

        if playlist_items_to_create:
            for i in range(0, len(playlist_items_to_create), batch_size):
                batch = playlist_items_to_create[i:i+batch_size]
                try:
                    with transaction.atomic():
                        PlaylistItem.objects.bulk_create(batch, ignore_conflicts=True)
                        playlist_contents_count += len(batch)
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error inserting playlist content batch: {e}"))
                    
        if favorites_to_create:
            for i in range(0, len(favorites_to_create), batch_size):
                batch = favorites_to_create[i:i+batch_size]
                try:
                    with transaction.atomic():
                        Favorite.objects.bulk_create(batch, ignore_conflicts=True)
                        favorites_count += len(batch)
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error inserting favorite batch: {e}"))

        self.stdout.write(f"Playlist Contents imported: {playlist_contents_count} success, Favorites imported: {favorites_count} success, ignored: {ignored_count}")


    def import_comments(self, items, batch_size):
        self.stdout.write("Importing Comments...")
        migrated_ids = set(MigrationMapping.objects.filter(model_name="Comment", status="SUCCESS").values_list("v4_id", flat=True))
        existing_user_ids = set(User.objects.values_list("id", flat=True))
        existing_video_ids = set(Video.objects.values_list("id", flat=True))
        first_user_id = User.objects.first().id if User.objects.exists() else 1

        items_to_process = [item for item in items if item['id'] not in migrated_ids]
        if not items_to_process:
            self.stdout.write("All Comments already migrated.")
            return

        success_count = 0
        error_count = 0

        # Pass 1: Import comments without hierarchy
        for i in range(0, len(items_to_process), batch_size):
            batch = items_to_process[i:i+batch_size]
            try:
                with transaction.atomic():
                    instances = []
                    mappings = []
                    for item in batch:
                        v_id = item.get('video_id')
                        if v_id not in existing_video_ids:
                            continue
                        author_id = item.get('author_id')
                        if author_id not in existing_user_ids:
                            author_id = first_user_id
                            
                        added = timezone.now()
                        if item.get('added'):
                            dt = parse_datetime(item['added'])
                            if dt:
                                added = make_aware(dt) if is_naive(dt) else dt
                                
                        defaults = {
                            'id': item['id'],
                            'content': item.get('content', '') or '',
                            'added': added,
                            'author_id': author_id,
                            'video_id': v_id,
                            'parent_id': None,
                            'direct_parent_id': None
                        }
                        instances.append(Comment(**defaults))
                        mappings.append(MigrationMapping(
                            model_name="Comment",
                            v4_id=item['id'],
                            v5_id=item['id'],
                            status=MigrationMapping.Status.SUCCESS
                        ))
                    
                    Comment.objects.bulk_create(instances, ignore_conflicts=True)
                    MigrationMapping.objects.bulk_create(mappings, ignore_conflicts=True)
                    success_count += len(instances)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error in Comment batch (Pass 1): {e}"))
                try:
                    with transaction.atomic():
                        err_mappings = [
                            MigrationMapping(
                                model_name="Comment",
                                v4_id=item['id'],
                                status=MigrationMapping.Status.ERROR,
                                message=str(e)
                            )
                            for item in batch
                        ]
                        MigrationMapping.objects.bulk_create(err_mappings, ignore_conflicts=True)
                except Exception as inner_e:
                    logger.warning(f"Could not record migration error to database: {inner_e}")
                error_count += len(batch)

        # Pass 2: Restore hierarchies
        self.stdout.write("Restoring Comment hierarchies (Pass 2)...")
        existing_comment_ids = set(Comment.objects.values_list("id", flat=True))
        comments_to_update = []
        
        for item in items:
            c_id = item['id']
            p_id = item.get('parent_id')
            dp_id = item.get('direct_parent_id')
            
            if c_id in existing_comment_ids:
                has_update = False
                parent_val = None
                dp_val = None
                
                if p_id and p_id in existing_comment_ids and p_id != c_id:
                    parent_val = p_id
                    has_update = True
                if dp_id and dp_id in existing_comment_ids and dp_id != c_id:
                    dp_val = dp_id
                    has_update = True
                    
                if has_update:
                    comments_to_update.append(Comment(id=c_id, parent_id=parent_val, direct_parent_id=dp_val))
                    
        if comments_to_update:
            for i in range(0, len(comments_to_update), batch_size):
                batch = comments_to_update[i:i+batch_size]
                try:
                    with transaction.atomic():
                        Comment.objects.bulk_update(batch, ['parent_id', 'direct_parent_id'])
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error updating Comment hierarchies: {e}"))

    def import_votes(self, items, batch_size):
        self.stdout.write("Importing Votes...")
        existing_comments = set(Comment.objects.values_list("id", flat=True))
        existing_users = set(User.objects.values_list("id", flat=True))
        existing_votes = set(Vote.objects.values_list("comment_id", "user_id"))

        votes_to_create = []
        ignored_count = 0

        for item in items:
            c_id = item['comment_id']
            u_id = item['user_id']
            if c_id not in existing_comments or u_id not in existing_users:
                ignored_count += 1
                continue
                
            if (c_id, u_id) not in existing_votes:
                votes_to_create.append(Vote(
                    id=item['id'],
                    comment_id=c_id,
                    user_id=u_id
                ))
                existing_votes.add((c_id, u_id))

        if votes_to_create:
            success_count = 0
            for i in range(0, len(votes_to_create), batch_size):
                batch = votes_to_create[i:i+batch_size]
                try:
                    with transaction.atomic():
                        Vote.objects.bulk_create(batch, ignore_conflicts=True)
                        success_count += len(batch)
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error inserting votes batch: {e}"))
            self.stdout.write(f"Votes imported: {success_count} success, ignored: {ignored_count}")
        else:
            self.stdout.write("No new Votes to import.")

    def import_viewcounts(self, items, batch_size):
        self.stdout.write("Importing View Counts (Date-based)...")
        existing_videos = set(Video.objects.values_list("id", flat=True))
        existing_viewcounts = set(ViewCount.objects.values_list("video_id", "date"))
        
        viewcounts_to_create = []
        ignored_count = 0
        vc_batch_size = max(batch_size, 5000)

        for item in items:
            v_id = item['video_id']
            if v_id not in existing_videos:
                ignored_count += 1
                continue
                
            dt_str = item.get('date', '')
            if not dt_str:
                continue
                
            try:
                dt = parse_datetime(dt_str + " 00:00:00").date()
            except Exception:
                continue
                
            if (v_id, dt) not in existing_viewcounts:
                viewcounts_to_create.append(ViewCount(
                    video_id=v_id,
                    date=dt,
                    count=item.get('count', 0)
                ))
                existing_viewcounts.add((v_id, dt))

        if viewcounts_to_create:
            success_count = 0
            for i in range(0, len(viewcounts_to_create), vc_batch_size):
                batch = viewcounts_to_create[i:i+vc_batch_size]
                try:
                    with transaction.atomic():
                        ViewCount.objects.bulk_create(batch, ignore_conflicts=True)
                        success_count += len(batch)
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error inserting ViewCounts batch: {e}"))
            self.stdout.write(f"ViewCounts imported: {success_count} success, ignored: {ignored_count}")
        else:
            self.stdout.write("No new ViewCounts to import.")

    def import_m2m_relation(self, items, v4_src_key, v4_target_key, through_model, src_field, target_field, src_ids_set, target_ids_set, batch_size, relation_name):
        self.stdout.write(f"Importing {relation_name} relations...")
        existing_relations = set(through_model.objects.values_list(src_field, target_field))
        
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
                    target_field: target_val
                }
                relations_to_create.append(through_model(**kwargs))
                existing_relations.add((src_val, target_val))
                
        if relations_to_create:
            success_count = 0
            for i in range(0, len(relations_to_create), batch_size):
                batch = relations_to_create[i:i+batch_size]
                try:
                    with transaction.atomic():
                        through_model.objects.bulk_create(batch, ignore_conflicts=True)
                        success_count += len(batch)
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error inserting {relation_name} batch: {e}"))
            self.stdout.write(f"{relation_name} relations imported: {success_count} success, ignored: {ignored_count}")
        else:
            self.stdout.write(f"No new {relation_name} relations to import.")

    def import_channel_collaborators(self, data, batch_size):
        self.stdout.write("Importing Channel Collaborators...")
        channels = Channel.objects.values_list('id', 'owner_id')
        primary_owners = {c_id: owner_id for c_id, owner_id in channels}
        existing_channels = set(primary_owners.keys())
        existing_users = set(User.objects.values_list('id', flat=True))
        
        through_model = Channel.collaborators.through
        existing_relations = set(through_model.objects.values_list('channel_id', 'user_id'))
        
        relations_to_create = []
        
        # 1. Additional owners
        for row in data.get('video_channel_owners', []):
            c_id = row['channel_id']
            u_id = row['user_id']
            if c_id not in existing_channels or u_id not in existing_users:
                continue
            if u_id == primary_owners[c_id]:
                continue
            if (c_id, u_id) not in existing_relations:
                relations_to_create.append(through_model(channel_id=c_id, user_id=u_id))
                existing_relations.add((c_id, u_id))
                
        # 2. Channel users
        for row in data.get('video_channel_users', []):
            c_id = row['channel_id']
            u_id = row['user_id']
            if c_id not in existing_channels or u_id not in existing_users:
                continue
            if (c_id, u_id) not in existing_relations:
                relations_to_create.append(through_model(channel_id=c_id, user_id=u_id))
                existing_relations.add((c_id, u_id))
                
        if relations_to_create:
            success_count = 0
            for i in range(0, len(relations_to_create), batch_size):
                batch = relations_to_create[i:i+batch_size]
                try:
                    with transaction.atomic():
                        through_model.objects.bulk_create(batch, ignore_conflicts=True)
                        success_count += len(batch)
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error inserting channel collaborators batch: {e}"))
            self.stdout.write(f"Channel Collaborators imported: {success_count} success.")
        else:
            self.stdout.write("No new Channel Collaborators to import.")

    def import_relations(self, data, batch_size):
        self.stdout.write("Importing Many-to-Many relations...")
        
        owner_ids = set(Owner.objects.values_list('id', flat=True))
        site_ids = set(Site.objects.values_list('id', flat=True))
        accessgroup_ids = set(AccessGroup.objects.values_list('id', flat=True))
        groupsite_ids = set(GroupSite.objects.values_list('id', flat=True))
        user_ids = set(User.objects.values_list('id', flat=True))
        group_ids = set(Group.objects.values_list('id', flat=True))
        video_ids = set(Video.objects.values_list('id', flat=True))
        type_ids = set(Type.objects.values_list('id', flat=True))
        discipline_ids = set(Discipline.objects.values_list('id', flat=True))
        tag_ids = set(Video.tags.tag_model.objects.values_list('id', flat=True))
        theme_ids = set(Theme.objects.values_list('id', flat=True))
        
        self.import_m2m_relation(
            data.get('authentication_owner_sites', []),
            'owner_id', 'site_id',
            Owner.sites.through, 'owner_id', 'site_id',
            owner_ids, site_ids, batch_size, "Owner-Site"
        )
        
        self.import_m2m_relation(
            data.get('authentication_owner_accessgroups', []),
            'owner_id', 'accessgroup_id',
            Owner.accessgroups.through, 'owner_id', 'accessgroup_id',
            owner_ids, accessgroup_ids, batch_size, "Owner-AccessGroup"
        )
        
        self.import_m2m_relation(
            data.get('authentication_accessgroup_sites', []),
            'accessgroup_id', 'site_id',
            AccessGroup.sites.through, 'accessgroup_id', 'site_id',
            accessgroup_ids, site_ids, batch_size, "AccessGroup-Site"
        )
        
        self.import_m2m_relation(
            data.get('authentication_groupsite_sites', []),
            'groupsite_id', 'site_id',
            GroupSite.sites.through, 'groupsite_id', 'site_id',
            groupsite_ids, site_ids, batch_size, "GroupSite-Site"
        )
        
        self.import_m2m_relation(
            data.get('auth_user_groups', []),
            'user_id', 'group_id',
            User.groups.through, 'user_id', 'group_id',
            user_ids, group_ids, batch_size, "User-Group"
        )
        
        self.import_m2m_relation(
            data.get('video_video_sites', []),
            'video_id', 'site_id',
            Video.sites.through, 'video_id', 'site_id',
            video_ids, site_ids, batch_size, "Video-Site"
        )
        
        self.import_m2m_relation(
            data.get('video_video_additional_owners', []),
            'video_id', 'user_id',
            Video.co_owners.through, 'video_id', 'user_id',
            video_ids, user_ids, batch_size, "Video-CoOwner"
        )
        
        self.import_m2m_relation(
            data.get('video_video_discipline', []),
            'video_id', 'discipline_id',
            Video.disciplines.through, 'video_id', 'discipline_id',
            video_ids, discipline_ids, batch_size, "Video-Discipline"
        )
        
        self.import_m2m_relation(
            data.get('video_video_restrict_access_to_groups', []),
            'video_id', 'accessgroup_id',
            Video.restricted_groups.through, 'video_id', 'accessgroup_id',
            video_ids, accessgroup_ids, batch_size, "Video-RestrictedGroup"
        )
        
        self.import_m2m_relation(
            data.get('video_video_tags', []),
            'video_id', 'tagulous_video_tags_id',
            Video.tags.through, 'video_id', 'tagulous_video_tags_id',
            video_ids, tag_ids, batch_size, "Video-Tag"
        )
        
        self.import_m2m_relation(
            data.get('video_video_theme', []),
            'video_id', 'theme_id',
            ThemeItem, 'video_id', 'theme_id',
            video_ids, theme_ids, batch_size, "Theme-Video"
        )
        
        self.import_channel_collaborators(data, batch_size)
        
        self.import_m2m_relation(
            data.get('video_type_sites', []),
            'type_id', 'site_id',
            Type.sites.through, 'type_id', 'site_id',
            type_ids, site_ids, batch_size, "Type-Site"
        )

    def ensure_superuser_exists(self):
        superusers = User.objects.filter(is_superuser=True)
        if not superusers.exists():
            self.stdout.write("No superuser found in the database. Creating a default superuser...")
            username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin")
            email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "admin@example.com")
            password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "admin")
            
            try:
                # Use User.objects.create_superuser to automatically trigger password hashing
                # and create a corresponding authentication.Owner profile via signals
                User.objects.create_superuser(username=username, email=email, password=password)
                self.stdout.write(self.style.SUCCESS(f"Default superuser '{username}' created successfully."))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error creating default superuser: {e}"))
        else:
            self.stdout.write(f"Superuser(s) found in the database ({superusers.count()} found). Skipping default superuser creation.")

    def import_subtitles(self, items, data, batch_size):
        self.stdout.write("Importing Subtitles...")
        migrated_ids = set(MigrationMapping.objects.filter(model_name="Subtitle", status="SUCCESS").values_list("v4_id", flat=True))
        existing_video_ids = set(Video.objects.values_list("id", flat=True))
        
        # Load custom files from podfile_customfilemodel & main_customfilemodel
        custom_files = {row['id']: row['file'] for row in data.get('podfile_customfilemodel', [])}
        custom_files.update({row['id']: row['file'] for row in data.get('main_customfilemodel', [])})

        items_to_process = [item for item in items if item['id'] not in migrated_ids]
        if not items_to_process:
            self.stdout.write("All Subtitles already migrated.")
            return

        success_count = 0
        error_count = 0

        from src.apps.video.conf import video_settings
        valid_langs = {lang["value"] for lang in video_settings.subtitle_languages}

        for i in range(0, len(items_to_process), batch_size):
            batch = items_to_process[i:i+batch_size]
            try:
                with transaction.atomic():
                    instances = []
                    mappings = []
                    for item in batch:
                        v_id = item.get('video_id')
                        if v_id not in existing_video_ids:
                            logger.warning(f"Skipping subtitle {item['id']}: Video V4 ID {v_id} not found in V5.")
                            continue
                        
                        src_id = item.get('src_id')
                        file_path = custom_files.get(src_id)
                        if not file_path:
                            logger.warning(f"Skipping subtitle {item['id']}: CustomFileModel ID {src_id} not found in V4 files dump.")
                            continue
                        
                        lang = item.get('lang') or 'fr'
                        if lang not in valid_langs:
                            logger.warning(f"Subtitle {item['id']} language '{lang}' is not in V5 choices, importing anyway.")

                        instances.append(Subtitle(
                            id=item['id'],
                            video_id=v_id,
                            language=lang,
                            file=file_path,
                            is_default=False
                        ))
                        mappings.append(MigrationMapping(
                            model_name="Subtitle",
                            v4_id=item['id'],
                            v5_id=item['id'],
                            status=MigrationMapping.Status.SUCCESS
                        ))
                    
                    Subtitle.objects.bulk_create(instances, ignore_conflicts=True)
                    MigrationMapping.objects.bulk_create(mappings, ignore_conflicts=True)
                    success_count += len(instances)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error in Subtitle batch: {e}"))
                try:
                    with transaction.atomic():
                        err_mappings = [
                            MigrationMapping(
                                model_name="Subtitle",
                                v4_id=item['id'],
                                status=MigrationMapping.Status.ERROR,
                                message=str(e)
                            )
                            for item in batch
                        ]
                        MigrationMapping.objects.bulk_create(err_mappings, ignore_conflicts=True)
                except Exception as inner_e:
                    logger.warning(f"Could not record subtitle migration error to database: {inner_e}")
                error_count += len(batch)
        self.stdout.write(f"Subtitles imported: {success_count} success, {error_count} errors.")

    def import_encoded_videos(self, items, batch_size):
        self.stdout.write("Importing Encoded Videos...")
        migrated_ids = set(MigrationMapping.objects.filter(model_name="EncodingVideo", status="SUCCESS").values_list("v4_id", flat=True))
        existing_video_ids = set(Video.objects.values_list("id", flat=True))

        items_to_process = [item for item in items if item['id'] not in migrated_ids]
        if not items_to_process:
            self.stdout.write("All Encoded Videos already migrated.")
            return

        success_count = 0
        error_count = 0

        for i in range(0, len(items_to_process), batch_size):
            batch = items_to_process[i:i+batch_size]
            try:
                with transaction.atomic():
                    instances = []
                    mappings = []
                    for item in batch:
                        v_id = item.get('video_id')
                        if v_id not in existing_video_ids:
                            logger.warning(f"Skipping encoded video {item['id']}: Video V4 ID {v_id} not found in V5.")
                            continue
                        
                        file_path = item.get('source_file')
                        if not file_path:
                            logger.warning(f"Skipping encoded video {item['id']}: Empty source_file.")
                            continue

                        videos_dir = encoding_settings.videos_dir
                        if videos_dir != "videos" and file_path.startswith("videos/"):
                            file_path = file_path.replace("videos/", f"{videos_dir}/", 1)

                        resolution = item.get('name', '360p') or '360p'
                        
                        instances.append(EncodingVideo(
                            id=item['id'],
                            video_id=v_id,
                            resolution=resolution,
                            file=file_path
                        ))
                        mappings.append(MigrationMapping(
                            model_name="EncodingVideo",
                            v4_id=item['id'],
                            v5_id=item['id'],
                            status=MigrationMapping.Status.SUCCESS
                        ))
                    
                    EncodingVideo.objects.bulk_create(instances, ignore_conflicts=True)
                    MigrationMapping.objects.bulk_create(mappings, ignore_conflicts=True)
                    success_count += len(instances)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error in Encoded Video batch: {e}"))
                try:
                    with transaction.atomic():
                        err_mappings = [
                            MigrationMapping(
                                model_name="EncodingVideo",
                                v4_id=item['id'],
                                status=MigrationMapping.Status.ERROR,
                                message=str(e)
                            )
                            for item in batch
                        ]
                        MigrationMapping.objects.bulk_create(err_mappings, ignore_conflicts=True)
                except Exception as inner_e:
                    logger.warning(f"Could not record encoded video migration error to database: {inner_e}")
                error_count += len(batch)
        self.stdout.write(f"Encoded Videos imported: {success_count} success, {error_count} errors.")
