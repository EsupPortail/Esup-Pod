import json
import logging
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.contrib.sites.models import Site
from django.db import transaction
from django.db.models.signals import post_save

from src.apps.authentication.models import Owner, AccessGroup, GroupSite
from src.apps.authentication.models.Owner import create_owner_profile, default_site_owner
from src.apps.authentication.models.GroupSite import create_groupsite_profile, default_site_groupsite

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Import authentication data from Pod v4 to Pod v5"

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='../../data_from_v3_to_v4/v3_exported_tables.json',
            help='Path to the JSON file exported from Pod V4'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to read {file_path}: {e}"))
            return

        self.stdout.write(self.style.SUCCESS("*** Start importing Authentication data ***"))

        # Disable signals to prevent conflicts during bulk imports
        post_save.disconnect(create_owner_profile, sender=User)
        post_save.disconnect(default_site_owner, sender=Owner)
        post_save.disconnect(create_groupsite_profile, sender=Group)
        post_save.disconnect(default_site_groupsite, sender=GroupSite)

        try:
            with transaction.atomic():
                self.import_users(data.get('auth_user', []))
                self.import_owners(data.get('authentication_owner', []))
                self.import_owner_sites(data.get('authentication_owner_sites', []))
                self.import_groups(data.get('auth_group', []))
                self.import_user_groups(data.get('auth_user_groups', []))
                self.import_accessgroups(data.get('authentication_accessgroup', []))
                self.import_accessgroup_sites(data.get('authentication_accessgroup_sites', []))
                self.import_owner_accessgroups(data.get('authentication_owner_accessgroups', []))
                self.import_groupsite(data.get('authentication_groupsite', []))
                self.import_groupsite_sites(data.get('authentication_groupsite_sites', []))
                self.stdout.write(self.style.SUCCESS("All authentication tables imported successfully."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error during import: {e}"))
            logger.exception("Error during authentication data import")
        finally:
            # Reconnect signals
            post_save.connect(create_owner_profile, sender=User)
            post_save.connect(default_site_owner, sender=Owner)
            post_save.connect(create_groupsite_profile, sender=Group)
            post_save.connect(default_site_groupsite, sender=GroupSite)
            self.stdout.write(self.style.SUCCESS("*** Finished importing Authentication data ***"))

    def import_users(self, items):
        self.stdout.write("Importing Users...")
        for item in items:
            defaults = {
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
                defaults['last_login'] = item['last_login']
            if item.get('date_joined'):
                defaults['date_joined'] = item['date_joined']
                
            User.objects.update_or_create(id=item['id'], defaults=defaults)

    def import_owners(self, items):
        self.stdout.write("Importing Owners...")
        for item in items:
            Owner.objects.update_or_create(
                id=item['id'],
                defaults={
                    'user_id': item['user_id'],
                    'auth_type': item.get('auth_type', 'local'),
                    'affiliation': item.get('affiliation', 'member'),
                    'comment': item.get('comment', ''),
                    'hashkey': item.get('hashkey', ''),
                    'userpicture': item.get('userpicture', ''),
                    'establishment': item.get('establishment', 'U1'),
                    'accepts_notifications': item.get('accepts_notifications', None),
                }
            )

    def import_owner_sites(self, items):
        self.stdout.write("Importing Owner Sites...")
        for item in items:
            try:
                owner = Owner.objects.get(id=item['owner_id'])
                site, _ = Site.objects.get_or_create(id=item['site_id'], defaults={'domain': f"site{item['site_id']}.com", 'name': f"Site {item['site_id']}"})
                owner.sites.add(site)
            except Exception as e:
                logger.error(f"Error importing owner site relation: {e}")

    def import_groups(self, items):
        self.stdout.write("Importing Groups...")
        for item in items:
            Group.objects.update_or_create(
                id=item['id'],
                defaults={'name': item['name']}
            )

    def import_user_groups(self, items):
        self.stdout.write("Importing User Groups...")
        for item in items:
            try:
                user = User.objects.get(id=item['user_id'])
                group = Group.objects.get(id=item['group_id'])
                user.groups.add(group)
            except Exception as e:
                logger.error(f"Error importing user group relation: {e}")

    def import_accessgroups(self, items):
        self.stdout.write("Importing AccessGroups...")
        for item in items:
            AccessGroup.objects.update_or_create(
                id=item['id'],
                defaults={
                    'display_name': item.get('display_name', ''),
                    'code_name': item.get('code_name', ''),
                    'auto_sync': item.get('auto_sync', False),
                }
            )

    def import_accessgroup_sites(self, items):
        self.stdout.write("Importing AccessGroup Sites...")
        for item in items:
            try:
                ag = AccessGroup.objects.get(id=item['accessgroup_id'])
                site, _ = Site.objects.get_or_create(id=item['site_id'], defaults={'domain': f"site{item['site_id']}.com", 'name': f"Site {item['site_id']}"})
                ag.sites.add(site)
            except Exception as e:
                logger.error(f"Error importing accessgroup site relation: {e}")

    def import_owner_accessgroups(self, items):
        self.stdout.write("Importing Owner AccessGroups...")
        for item in items:
            try:
                owner = Owner.objects.get(id=item['owner_id'])
                ag = AccessGroup.objects.get(id=item['accessgroup_id'])
                owner.accessgroups.add(ag)
            except Exception as e:
                logger.error(f"Error importing owner accessgroup relation: {e}")

    def import_groupsite(self, items):
        self.stdout.write("Importing GroupSites...")
        for item in items:
            GroupSite.objects.update_or_create(
                id=item['id'],
                defaults={'group_id': item['group_id']}
            )

    def import_groupsite_sites(self, items):
        self.stdout.write("Importing GroupSite Sites...")
        for item in items:
            try:
                gs = GroupSite.objects.get(id=item['groupsite_id'])
                site, _ = Site.objects.get_or_create(id=item['site_id'], defaults={'domain': f"site{item['site_id']}.com", 'name': f"Site {item['site_id']}"})
                gs.sites.add(site)
            except Exception as e:
                logger.error(f"Error importing groupsite site relation: {e}")
