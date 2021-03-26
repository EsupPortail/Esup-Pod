import json
from django.core.management.base import BaseCommand
from django.utils import translation
from django.conf import settings
from pod.authentication.models import AccessGroup, Owner
from django.core.exceptions import ObjectDoesNotExist

LANGUAGE_CODE = getattr(settings, "LANGUAGE_CODE", 'fr')


def edit_group_properties(group):
    existing_group = AccessGroup.objects.get(
        name=group["name"])
    print("--> Already exists")
    if group["display_name"] != existing_group.display_name:
        print(
            "---> Changing display_name from \"" +
            existing_group.display_name +
            "\" to \"" + group["display_name"] + "\"")
        existing_group.display_name = group["display_name"]
    return existing_group


def add_users_to_group(group, existing_group):
    if group["users_to_add"]:
        print("---> There is some users to add")
        for user in group["users_to_add"]:
            try:
                owner = Owner.objects.get(user__username=user)
                if owner in existing_group.users.all():
                    print("----> User with username \""
                          + user + "\" is already in group")
                else:
                    print("----> Adding \"" + user + "\" to the group")
                    existing_group.users.add(owner)
            except ObjectDoesNotExist:
                print(
                    "----> User with username \"" + user + "\" doesn't exist")


def remove_users_to_group(group, existing_group):
    if group["users_to_remove"]:
        print("---> There is some users to remove")
        for user in group["users_to_remove"]:
            try:
                owner = Owner.objects.get(user__username=user)
                if owner not in existing_group.users.all():
                    print("----> User with username \""
                          + user + "\" is not in group")
                else:
                    print("----> Removing \"" + user + "\" to the group")
                    existing_group.users.remove(owner)
            except ObjectDoesNotExist:
                print(
                    "----> User with username \"" + user + "\" doesn't exist")


class Command(BaseCommand):
    # First possible argument : checkDirectory
    args = 'import_json'
    help = 'Import groups from json'
    'published by the recorders. '
    valid_args = ['import_json']

    def add_arguments(self, parser):
        parser.add_argument('task')
        parser.add_argument('file')

    def handle(self, *args, **options):

        # Activate a fixed locale fr
        translation.activate(LANGUAGE_CODE)
        if options['task'] and options['task'] in self.valid_args:
            json_data = open(options['file'])
            groups = json.load(json_data)
            for group in groups:
                print("\n-> Processing " + group["name"])
                try:
                    existing_group = edit_group_properties(group)
                    add_users_to_group(group, existing_group)
                    remove_users_to_group(group, existing_group)
                    existing_group.save()
                except ObjectDoesNotExist:
                    print("Group with name " + group[
                        "name"] + " doesn't exists")
                    if not (group["name"] and group["display_name"]):
                        print(
                            "No such informations to create " + group["name"])
                    else:
                        AccessGroup.objects.create(
                            name=group[
                                "name"], display_name=group["display_name"])
                        print("Successfully creating " + group["name"])
            json_data.close()
        else:
            print(
                "*** Warning: you must give some arguments: %s ***" %
                self.valid_args)
