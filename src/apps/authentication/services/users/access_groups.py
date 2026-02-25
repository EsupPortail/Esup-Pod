import logging
from typing import Any, List

from ...models.AccessGroup import AccessGroup
from ...models.Owner import Owner

logger = logging.getLogger(__name__)


class AccessGroupService:
    @staticmethod
    def set_user_accessgroup(username: str, groups: List[str]) -> Any:
        owner = Owner.objects.get(user__username=username)  # Will raise DoesNotExist

        for group_code in groups:
            try:
                accessgroup = AccessGroup.objects.get(code_name=group_code)
                owner.accessgroups.add(accessgroup)
            except AccessGroup.DoesNotExist:
                logger.debug(
                    "set_user_accessgroup: AccessGroup %r not found, skipping.",
                    group_code,
                )
        return owner

    @staticmethod
    def remove_user_accessgroup(username: str, groups: List[str]) -> Any:
        owner = Owner.objects.get(user__username=username)

        for group_code in groups:
            try:
                accessgroup = AccessGroup.objects.get(code_name=group_code)
                if accessgroup in owner.accessgroups.all():
                    owner.accessgroups.remove(accessgroup)
            except AccessGroup.DoesNotExist:
                logger.debug(
                    "remove_user_accessgroup: AccessGroup %r not found, skipping.",
                    group_code,
                )
        return owner

    @staticmethod
    def set_users_by_name(code_name: str, users: List[str]) -> Any:
        accessgroup = AccessGroup.objects.get(code_name=code_name)

        for username in users:
            try:
                owner = Owner.objects.get(user__username=username)
                accessgroup.users.add(owner)
            except Owner.DoesNotExist:
                logger.debug(
                    "set_users_by_name: Owner for username %r not found, skipping.",
                    username,
                )
        return accessgroup

    @staticmethod
    def remove_users_by_name(code_name: str, users: List[str]) -> Any:
        accessgroup = AccessGroup.objects.get(code_name=code_name)

        for username in users:
            try:
                owner = Owner.objects.get(user__username=username)
                if owner in accessgroup.users.all():
                    accessgroup.users.remove(owner)
            except Owner.DoesNotExist:
                logger.debug(
                    "remove_users_by_name: Owner for username %r not found, skipping.",
                    username,
                )
        return accessgroup
