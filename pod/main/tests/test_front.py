from django.contrib.staticfiles.testing import StaticLiveServerTestCase
# from selenium.webdriver.chrome.webdriver import WebDriver
# from selenium import webdriver
# from selenium.webdriver.common.by import By


class FrontTests(StaticLiveServerTestCase):
    fixtures = [
        "initial_data_main.json",
        "initial_data_video.json",
    ]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # options = webdriver.ChromeOptions()
        # options.add_argument('headless')
        # options.add_argument('--disable-infobars')
        # options.add_argument('--disable-dev-shm-usage')
        # options.add_argument('--no-sandbox')
        # options.add_argument('--remote-debugging-port=9222')
        # cls.selenium = webdriver.Chrome(version_main=109, options=options)
        # # cls.selenium = WebDriver()
        # cls.selenium.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        # cls.selenium.quit()
        super().tearDownClass()

    def test_home_page(self):
        # self.selenium.get('%s%s' % (self.live_server_url, ''))
        # self.driver.set_window_size(936, 634)
        # self.driver.find_element(By.ID, "okcookie").click()
        # self.driver.find_element(By.ID, "pod-param-buttons__button").click()
        # self.driver.find_element(By.CSS_SELECTOR, "#pod-navbar__menusettings .btn-close").click()
        print(" --->  test_home_page of FrontTest: OK!")
