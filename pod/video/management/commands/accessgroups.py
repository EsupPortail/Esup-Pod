import json
from django.core.management.base import BaseCommand
from django.utils import translation
from django.conf import settings
from pod.authentication.models import AccessGroup, Owner
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import Group

LANGUAGE_CODE = getattr(settings, "LANGUAGE_CODE", "fr")


def edit_group_properties(group):
    existing_group = AccessGroup.objects.get(code_name=group["code_name"])
    print("--> Already exists")
    if group["display_name"] != existing_group.display_name:
        print(
            '---> Changing display_name from "'
            + existing_group.display_name
            + '" to "'
            + group["display_name"]
            + '"'
        )
        existing_group.display_name = group["display_name"]
    return existing_group


def add_users_to_group(group, existing_group):
    if "users_to_add" in group:
        print("---> There is some users to add")
        for user in group["users_to_add"]:
            try:
                owner = Owner.objects.get(user__username=user)
                if owner in existing_group.users.all():
                    print('----> User with username "' + user + '" is already in group')
                else:
                    print('----> Adding "' + user + '" to the group')
                    existing_group.users.add(owner)
            except ObjectDoesNotExist:
                print('----> User with username "' + user + "\" doesn't exist")


def remove_users_to_group(group, existing_group):
    if "users_to_remove" in group:
        print("---> There is some users to remove")
        for user in group["users_to_remove"]:
            try:
                owner = Owner.objects.get(user__username=user)
                if owner not in existing_group.users.all():
                    print('----> User with username "' + user + '" is not in group')
                else:
                    print('----> Removing "' + user + '" to the group')
                    existing_group.users.remove(owner)
            except ObjectDoesNotExist:
                print('----> User with username "' + user + "\" doesn't exist")


def command_import_json(options):
    json_data = open(options["file"])
    groups = json.load(json_data)
    for group in groups:
        print("\n-> Processing " + group["code_name"])
        try:
            existing_group = edit_group_properties(group)
            add_users_to_group(group, existing_group)
            remove_users_to_group(group, existing_group)
            existing_group.save()
        except ObjectDoesNotExist:
            print("Group with name " + group["code_name"] + " doesn't exists")
            if not (group["code_name"] and group["display_name"]):
                print("No such informations to create " + group["code_name"])
            else:
                newgroup = AccessGroup.objects.create(
                    code_name=group["code_name"],
                    display_name=group["display_name"],
                )
                print("Successfully creating " + group["code_name"])
                add_users_to_group(group, newgroup)
                remove_users_to_group(group, newgroup)
                newgroup.save()
    json_data.close()


def command_migrate_groups(options):
    for group in Group.objects.all():
        if AccessGroup.objects.filter(id=group.id).exists():
            print('-> AccessGroup with id "' + str(group.id) + '" already exists.')
        else:
            AccessGroup.objects.create(
                code_name=group.name, id=group.id, display_name=group.name
            )
            print(
                '-> Successfully creating AccessGroup "'
                + group.name
                + '" with id "'
                + str(group.id)
                + '".'
            )


class Command(BaseCommand):
    # First possible argument: checkDirectory
    args = "import_json"
    help = "Import groups from json"
    "published by the recorders. "
    valid_args = ["import_json", "migrate_groups"]

    def add_arguments(self, parser):
        parser.add_argument("task")
        parser.add_argument("file", nargs="?", default="")

    def handle(self, *args, **options):
        # Activate a fixed locale fr
        translation.activate(LANGUAGE_CODE)
        if options["task"] and options["task"] in self.valid_args:
            if options["task"] == "import_json":
                command_import_json(options)
            elif options["task"] == "migrate_groups":
                command_migrate_groups(options)

        else:
            print("*** Warning: you must give some arguments: %s ***" % self.valid_args)
