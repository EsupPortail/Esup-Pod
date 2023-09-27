"""Esup-pod Main applications."""
from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist

import json


def create_missing_pages(sender, **kwargs):
    """Create missing flat pages from json fixtures."""
    print("---> Creating missing flat pages and links...")

    count = 0
    with open("./pod/main/fixtures/flat_pages.json", encoding="utf-8") as data_file:
        json_data = json.loads(data_file.read())
        print("--> Search missing accessibility pages...")
        for fixture in json_data:
            count += create_pages_and_links(fixture)

    if count == 0:
        print("--> No missing page nor missing link found, all is up to date!")


def create_pages_and_links(fixture):
    """Create missing flat pages and associated footer links from one fixture."""
    from pod.main.models import LinkFooter
    from django.contrib.flatpages.models import FlatPage

    count = 0
    if fixture["model"] == "flatpages.flatpage":
        url = fixture["fields"]["url"]
        page, page_created = FlatPage.objects.get_or_create(url=url)
        if page_created:
            print("-> New page created at “%s”." % url)
            count += 1
            update_object_fields(page, fixture["fields"])

    elif fixture["model"] == "main.linkfooter":
        title = fixture["fields"]["title_en"]
        link, link_created = LinkFooter.objects.get_or_create(title_en=title)
        if link_created:
            print("-> New Footer link created for “%s”." % title)
            count += 1
            update_object_fields(link, fixture["fields"], title)
    return count


def update_object_fields(obj, fields, title=None):
    """Update all fields values on object obj."""
    from django.contrib.sites.models import Site
    from django.contrib.flatpages.models import FlatPage

    for field, value in fields.items():
        if field == "sites":
            obj.sites.add(Site.objects.get_current())
        elif field == "page":
            try:
                obj.page = FlatPage.objects.get(title_en=title)
            except ObjectDoesNotExist:
                print("--> [[ ERROR ]] NO page with title_en=“%s”" % title)
        else:
            # print("--> Set ATTR [%s]" % (field))
            setattr(obj, field, value)
    obj.save()


def create_missing_conf(sender, **kwargs):
    """Create missing configurations from initial_data.json."""
    from pod.main.models import Configuration

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
        print("--> No missing configurations found, all is up to date!")


class MainConfig(AppConfig):
    """Esup-pod Main configurations class."""

    name = "pod.main"
    default_auto_field = "django.db.models.BigAutoField"
    verbose_name = _("Main configurations")

    def ready(self):
        """Run code when Django starts."""
        post_migrate.connect(create_missing_conf, sender=self)
        post_migrate.connect(create_missing_pages, sender=self)
