from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium.webdriver.firefox.webdriver import WebDriver

# python manage.py test -v 3 --settings=pod.main.test_settings \
# pod.main.integration_tests.selenium_pod_integration_tests


class PodSeleniumTests(StaticLiveServerTestCase):
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

    def Test_selenium_suites(self):
        """Run a set of Selenium Test Suites from Side files"""
        print(self.live_server_url)
        self.selenium.get(f"{self.live_server_url}/")
        print(self.selenium.title)
        assert "Welcome" in self.selenium.page_source

    def run_suite(self, suite_name):
        pass
