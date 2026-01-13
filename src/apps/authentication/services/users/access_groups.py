from typing import Any, List
from ...models.AccessGroup import AccessGroup
from ...models.Owner import Owner


class AccessGroupService:
    @staticmethod
    def set_user_accessgroup(username: str, groups: List[str]) -> Any:
        owner = Owner.objects.get(user__username=username)  # Will raise DoesNotExist

        for group_code in groups:
            try:
                accessgroup = AccessGroup.objects.get(code_name=group_code)
                owner.accessgroups.add(accessgroup)
            except AccessGroup.DoesNotExist:
                pass
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
                pass
        return owner

    @staticmethod
    def set_users_by_name(code_name: str, users: List[str]) -> Any:
        accessgroup = AccessGroup.objects.get(code_name=code_name)

        for username in users:
            try:
                owner = Owner.objects.get(user__username=username)
                accessgroup.users.add(owner)
            except Owner.DoesNotExist:
                pass
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
                pass
        return accessgroup
