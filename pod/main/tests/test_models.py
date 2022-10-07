from django.test import TestCase
from django.contrib.flatpages.models import FlatPage
from django.conf import settings
from django.contrib.sites.models import Site
from pod.main.models import Configuration, AdditionalChannelTab

SITE_ID = getattr(settings, "SITE_ID", 1)

"""
    test the flatepages
    Creation fo welcome page
"""
# Add customImage, customFile, linkFooter


class FlatepageTestCase(TestCase):
    def setUp(self):
        fp1 = FlatPage.objects.create(title="Home", url="/")
        fp1.sites.add(Site.objects.get(id=SITE_ID))
        fp1.save()
        fp2 = FlatPage.objects.create(
            title="Home",
            url="/home/",
            title_fr="Accueil",
            title_en="Home",
            content_fr="<p>Bienvenue</p>\r\n",
            content_en="<p>Welcome</p>\r\n",
        )
        fp2.sites.add(Site.objects.get(id=SITE_ID))
        fp2.save()
        print(" --->  SetUp of FlatepageTestCase : OK !")

    """
        test all attributs when a channel have been save with the minimum of
        attributs
    """

    def test_Flatepage_null_attribut(self):
        flatPage = FlatPage.objects.get(url="/")
        self.assertQuerysetEqual(
            flatPage.sites.all(),
            Site.objects.filter(id=SITE_ID),
            transform=lambda x: x,
        )
        self.assertEqual(flatPage.registration_required, False)
        self.assertEqual(flatPage.title, "Home")
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        print("   --->  test_Flatepage_null_attribut" " of FlatepageTestCase : OK !")

    """
        test attributs when a channel have many attributs
    """

    def test_Flatepage_with_attributs(self):
        flatPage = FlatPage.objects.get(url="/home/")
        self.assertQuerysetEqual(
            flatPage.sites.all(),
            Site.objects.filter(id=SITE_ID),
            transform=lambda x: x,
        )
        self.assertEqual(flatPage.registration_required, False)
        self.assertEqual(flatPage.title, "Home")  # langage code : en
        self.assertEqual(flatPage.title_fr, "Accueil")
        self.assertEqual(flatPage.title_en, "Home")
        self.assertEqual(flatPage.content_en, "<p>Welcome</p>\r\n")
        self.assertEqual(flatPage.content_fr, "<p>Bienvenue</p>\r\n")
        response = self.client.get("/home/")
        self.assertEqual(response.status_code, 200)
        print("   --->  test_Flatepage_with_attributs" " of FlatepageTestCase : OK !")

    """
        test delete object
    """

    def test_delete_object(self):
        FlatPage.objects.get(id=1).delete()
        FlatPage.objects.get(id=2).delete()
        self.assertEqual(FlatPage.objects.all().count(), 0)

        print("   --->  test_delete_object of ChannelTestCase : OK !")


class ConfigurationTestCase(TestCase):
    fixtures = [
        "initial_data.json",
    ]

    def setUp(self):
        print(" --->  SetUp of ConfigurationTestCase : OK !")

    """
        test attributs
    """

    def test_exist(self):
        maintenance_conf = Configuration.objects.filter(key="maintenance_mode")
        self.assertTrue(maintenance_conf.exists())
        print("   --->  test_exist of ConfigurationTestCase : OK !")

    def test_attributs(self):
        conf = Configuration.objects.get(key="maintenance_mode")
        self.assertEqual(conf.key, "maintenance_mode")
        self.assertEqual(conf.value, "0")
        self.assertEqual(conf.description, "Activation of maintenance mode or not")

        print("   --->  test_attributs of ConfigurationTestCase : OK !")

    """
        test delete object
    """

    def test_delete_object(self):
        Configuration.objects.filter(key="maintenance_mode").delete()
        self.assertEquals(Configuration.objects.filter(key="maintenance_mode").count(), 0)
        print("--->  test_delete_object of ConfigurationTestCase : OK " "!")


class AdditionalChannelTabTestCase(TestCase):
    def setUp(self):
        AdditionalChannelTab.objects.create(name="Tab0")
        print(" --->  SetUp of AdditionalChannelTabTestCase : OK !")

    """
        test attributs
    """

    def test_exist(self):
        tab = AdditionalChannelTab.objects.filter(name="Tab0")
        self.assertTrue(tab.exists())
        print("   --->  test_exist of AdditionalChannelTabTestCase : OK !")

    def test_attributs(self):
        tab = AdditionalChannelTab.objects.get(name="Tab0")
        self.assertEqual(tab.name, "Tab0")

        print("   --->  test_attributs of AdditionalChannelTabTestCase : OK !")

    """
        test delete object
    """

    def test_delete_object(self):
        AdditionalChannelTab.objects.filter(name="Tab0").delete()
        self.assertEquals(AdditionalChannelTab.objects.filter(name="Tab0").count(), 0)

        print("--->  test_delete_object of AdditionalChannelTabTestCase : OK " "!")
