"""
Esup-Pod - WebTV V4 to V5 user migration.
"""

from django.db import connections, transaction
from django.contrib.auth.models import User
from src.apps.authentication.models.Owner import Owner
from src.apps.migration.models import UserMapping

# Non-listed levels → regular user (is_staff=False, is_superuser=False, is_active=True)
LEVEL_MAP = {
    1: {"is_staff": True, "is_superuser": True, "is_active": True},
    5: {"is_staff": True, "is_superuser": False, "is_active": True},
    6: {"is_staff": False, "is_superuser": False, "is_active": False},
}


def userMigrate(self, *args, **kwargs):
    """Migrates WebTV V4 users (Ze4fg_users + Ze4fg_user_profile) into Django Users."""
    with connections["webtv"].cursor() as cursor:
        cursor.execute("""
            SELECT u.*, p.first_name, p.last_name
            FROM Ze4fg_users u
            LEFT JOIN Ze4fg_user_profile p ON p.userid = u.userid
            """)
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()
        users_tmp = {
            row[columns.index("userid")]: dict(zip(columns, row)) for row in rows
        }

    with transaction.atomic():
        for old_id, data in users_tmp.items():
            username = data["username"]

            # Skip if already mapped
            if UserMapping.objects.filter(old_id=old_id).exists():
                self.stdout.write(f"Skip {username} (already mapped)")
                continue

            level = data.get("level", 2)
            flags = LEVEL_MAP.get(
                level, {"is_staff": False, "is_superuser": False, "is_active": True}
            )

            # Deactivate if banned or account not OK
            if data.get("ban_status") == "yes" or data.get("usr_status") != "Ok":
                flags["is_active"] = False

            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": data.get("email", ""),
                    "first_name": data.get("first_name") or "",
                    "last_name": data.get("last_name") or "",
                    "is_staff": flags["is_staff"],
                    "is_superuser": flags["is_superuser"],
                    "is_active": flags["is_active"],
                },
            )

            owner = Owner.objects.get(user=user)
            owner.auth_type = "CAS"
            # owner.affiliation = "member"
            # owner.establishment = "Etab_1"
            owner.accepts_notifications = data.get("msg_notify") == "yes"
            owner.save()

            UserMapping.objects.create(
                old_id=old_id,
                new_id=user.id,
                username=username,
            )

            self.stdout.write(
                f"{'Created' if created else 'Existing'}: "
                f"{username} old_id={old_id} → new_id={user.id} "
                f"(staff={flags['is_staff']}, superuser={flags['is_superuser']}, "
                f"active={flags['is_active']})"
            )

    self.stdout.write(self.style.SUCCESS("Migration completed"))
