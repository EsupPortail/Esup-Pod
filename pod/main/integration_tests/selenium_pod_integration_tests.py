from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium.webdriver.firefox.webdriver import WebDriver

import glob
import json

# python manage.py test -v 3 --settings=pod.main.test_settings \
# pod.main.integration_tests.selenium_pod_integration_tests


class PodSeleniumTest(StaticLiveServerTestCase):
    """Tests the integration of Pod application with Selenium from side files"""
    fixtures = ["initial_data.json"]

    @classmethod
    def setUpClass(cls):
        """Create the driver for all selenium tests."""
        super().setUpClass()
        cls.selenium = WebDriver()
        cls.selenium.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        """Close the driver used."""
        cls.selenium.quit()
        super().tearDownClass()

    def test_selenium_suites(self):
        """Run a set of Selenium Test Suites from Side files"""
        print("\n\n - test_selenium_suites - ")
        sides = glob.glob(r"sides/*.side")
        print(sides)
        for side in sides:
            print(side)
            with open('./sides/%s' % side) as json_file:
                data = json.load(json_file)
                print(data)

        print(self.live_server_url)
        self.selenium.get(f"{self.live_server_url}/")
        print(self.selenium.title)
        assert "Welcome" in self.selenium.page_source
        print("\n\n - test_selenium_suites - ")

    def run_suite(self, suite_name):
        pass
