from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.utils.translation import gettext_lazy as _

import json


def create_missing_conf(sender, **kwargs):
    from pod.main.models import Configuration
    from django.core.exceptions import ObjectDoesNotExist

    print("---> Creating missing configurations...")
    json_data = []
    with open("./pod/main/fixtures/initial_data.json", encoding="utf-8") as data_file:
        json_data = json.loads(data_file.read())

    updated_count = 0
    for fixture in json_data:
        if fixture["model"] == "main.configuration":
            key = fixture["fields"]["key"]
            value = fixture["fields"]["value"]
            description_fr = fixture["fields"]["description_fr"]
            description_en = fixture["fields"]["description_en"]
            try:
                conf = Configuration.objects.get(key=key)
                if not (
                    conf.description_fr == description_fr
                    and conf.description_en == description_en
                ):
                    updated_count = updated_count + 1
                    print("--> " + key)
                    print("-> Updating description...")
                    conf.description_fr = description_fr
                    conf.description_en = description_en
                    conf.save()
            except ObjectDoesNotExist:
                print("--> " + key)
                print("-> Creating...")
                updated_count = updated_count + 1
                Configuration.objects.create(
                    key=key,
                    value=value,
                    description_fr=description_fr,
                    description_en=description_en,
                )
    if updated_count == 0:
        print("--> No missing configurations found, all is up to date !")


class MainConfig(AppConfig):
    name = "pod.main"
    default_auto_field = "django.db.models.BigAutoField"
    verbose_name = _("Main configurations")

    def ready(self):
        post_migrate.connect(create_missing_conf, sender=self)
