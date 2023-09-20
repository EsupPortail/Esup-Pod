from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium.webdriver.firefox.webdriver import WebDriver

# python manage.py test -v 3 --settings=pod.main.test_settings \
# pod.main.integration_tests.selenium_pod_integration_tests


class PodSeleniumTests(StaticLiveServerTestCase):
    fixtures = ["initial_data.json"]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.selenium = WebDriver()
        cls.selenium.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def test_home(self):
        print(self.live_server_url)
        self.selenium.get(f"{self.live_server_url}/")
        print(self.selenium.title)
        assert "Welcome" in self.selenium.page_source
