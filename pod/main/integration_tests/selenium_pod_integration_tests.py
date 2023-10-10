from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import json
import os
from pyvirtualdisplay import Display
from django.conf import settings
from selenium.webdriver.support.ui import Select
from django.test.utils import override_settings
from django.contrib.auth.models import User
from pod.video.models import Video, Type

# python manage.py test -v 3 --settings=pod.main.test_settings \
# pod.main.integration_tests.selenium_pod_integration_tests

target_cache = {}


def parse_target(target):
    """
    Parse the target string to determine the Selenium locator type and value.

    Args:
        target (str): The target element identifier, which can start with 'link=', '//', 'xpath=', 'css=', 'id=', or 'name='.

    Returns:
        tuple: A tuple containing the Selenium locator type (e.g., By.LINK_TEXT, By.XPATH, By.CSS_SELECTOR, By.ID, By.NAME) and the corresponding value.

    Returns:
        tuple: A tuple containing the Selenium locator type and the corresponding value, or (None, None) if the target identifier format is not recognized.
    """
    if target.startswith("link="):
        return By.LINK_TEXT, target[5:]
    elif target.startswith("//"):
        return By.XPATH, target
    elif target.startswith("xpath="):
        return By.XPATH, target[6:]
    elif target.startswith("css="):
        return By.CSS_SELECTOR, target[4:]
    elif target.startswith("id="):
        return By.ID, target[3:]
    elif target.startswith("name="):
        return By.NAME, target[5:]
    else:
        return None, None


def find_element(driver, target):
    """
    Find and return a web element using various locator strategies (e.g., By.ID, By.XPATH, By.CSS_SELECTOR).

    Args:
        driver (WebDriver): The WebDriver instance for interacting with the web page.
        target (str): The target element identifier, which can start with 'link=', '//', 'xpath=', 'css=', 'id=', or 'name='.

    Returns:
        WebElement: The located web element.

    Raises:
        NoSuchElementException: If the specified element is not found on the web page.
        Exception: If the target identifier format is not recognized.
    """
    if target in target_cache:
        target = target_cache[target]

    locator, value = parse_target(target)

    if locator is not None:
        try:
            return driver.find_element(locator, value)
        except NoSuchElementException:
            result = driver.find_element(locator, value.lower())
            target_cache[target] = f"{locator}={value.lower()}"
            msg = f"label {value} is being cached as {target_cache[target]}"
            print(msg)
            return result
    else:
        direct = (
            driver.find_element(By.NAME, target)
            or driver.find_element(By.ID, target)
            or driver.find_element(By.LINK_TEXT, target)
        )
        if direct:
            return direct
        raise Exception("Don't know how to find %s" % target)


class SeleniumTestCase(object):
    """A Single Selenium Test Case"""

    def __init__(self, test_data, callback=None):
        """
        Initialize a SeleniumTestCase instance.

        Args:
            test_data (dict): Test case data, including name, URL, and commands.
            callback (callable, optional): Callback function to be executed after the test.
        """
        self.test_data = test_data
        self.callback = callback
        self.base_url = None
        self.commands = []

    def run(self, driver, url):
        """
        Run the Selenium test case.

        Args:
            driver (WebDriver): The WebDriver instance for interacting with the web page.
            url (str): The base URL for the test case.
        """
        self.base_url = url
        print(f'Running test: {self.test_data["name"]}')
        for command in self.commands:
            method_name, target, value = command
            method = getattr(self, method_name)
            args = [driver]
            if target is not None:
                args.append(target)
            if value is not None:
                args.append(value)
            print(f"   {method_name} {args}")
            method(*args)
        if self.callback:
            self.callback(driver.page_source)

    def cookies_commands(self, driver, url):
        """
        Execute custom commands to handle cookies acceptance on website.

        Args:
            driver (WebDriver): The WebDriver instance for interacting with the web page.
            url (str): The base URL for the test case.
        """
        with open(
            "pod/main/integration_tests/commands/cookies_commands.side", "r"
        ) as side_file:
            side_data = json.load(side_file)
            self.test_data["commands"] = side_data.get("commands", [])
            self.run(driver, url)

    def open(self, driver, target):
        """
        Open a URL in the WebDriver.

        Args:
            driver (WebDriver): The WebDriver instance for interacting with the web page.
            target (str): The URL to open.
        """
        driver.get(self.base_url + target)

    def click(self, driver, target):
        """
        Click on a web element identified by a target.

        Args:
            driver (WebDriver): The WebDriver instance for interacting with the web page.
            target (str): The identifier for the web element to be clicked.
        """
        element = find_element(driver, target)
        driver.execute_script("arguments[0].scrollIntoView();", element)
        element.click()

    def clickAndWait(self, driver, target):
        """
        Click on a web element identified by a target and wait for a response.

        Args:
            driver (WebDriver): The WebDriver instance for interacting with the web page.
            target (str): The identifier for the web element to be clicked.
        """
        self.click(driver, target)

    def type(self, driver, target, text=""):
        """
        Simulate typing text into an input field on a web page.

        Args:
            driver (WebDriver): The WebDriver instance for interacting with the web page.
            target (str): The identifier for the input field.
            text (str): The text to be typed into the input field (optional).
        """
        element = find_element(driver, target)
        element.click()
        element.clear()
        element.send_keys(text)

    def select(self, driver, target, value):
        """
        Select an option from a dropdown list on a web page.

        Args:
            driver (WebDriver): The WebDriver instance for interacting with the web page.
            target (str): The identifier for the dropdown element.
            value (str): The option value to be selected.
        """
        element = find_element(driver, target)
        if value.startswith("label="):
            Select(element).select_by_visible_text(value[6:])
        else:
            msg = "Don't know how to select %s on %s"
            raise Exception(msg % (value, target))

    def verifyTextPresent(self, driver, text):
        """
        Verify if the specified text is present in the page source.

        Args:
            driver (WebDriver): The WebDriver instance for interacting with the web page.
            text (str): The text to be verified for presence.
        """
        try:
            source = driver.page_source
            assert bool(text in source)
        except Exception:
            print("verifyTextPresent: ", repr(text), "not present in", repr(source))
            raise

    def verifyTextNotPresent(self, driver, text):
        """
        Verify if the specified text is not present in the page source.

        Args:
            driver (WebDriver): The WebDriver instance for interacting with the web page.
            text (str): The text to be verified for absence.
        """
        try:
            assert not bool(text in driver.page_source)
        except Exception:
            print("verifyNotTextPresent: ", repr(text), "present")
            raise

    def assertElementPresent(self, driver, target):
        """
        Assert the presence of a specified web element.

        Args:
            driver (WebDriver): The WebDriver instance for interacting with the web page.
            target (str): The identifier for the web element to be verified for presence.
        """
        try:
            assert bool(find_element(driver, target))
        except Exception:
            print("assertElementPresent: ", repr(target), "not present")
            raise

    def verifyElementPresent(self, driver, target):
        """
        Verify the presence of a specified web element on a web page.

        Args:
            driver (WebDriver): The WebDriver instance for interacting with the web page.
            target (str): The identifier for the web element to be verified for presence.
        """
        try:
            assert bool(find_element(driver, target))
        except Exception:
            print("verifyElementPresent: ", repr(target), "not present")
            raise

    def verifyElementNotPresent(self, driver, target):
        """
        Verify the absence of a specified web element on a web page.

        Args:
            driver (WebDriver): The WebDriver instance for interacting with the web page.
            target (str): The identifier for the web element to be verified for absence.
        """

        present = True
        try:
            find_element(driver, target)
        except NoSuchElementException:
            present = False

        try:
            assert not present
        except Exception:
            print("verifyElementNotPresent: ", repr(target), "present")
            raise

    def waitForTextPresent(self, driver, text):
        """
        Wait for the specified text to be present in the page source.

        Args:
            driver (WebDriver): The WebDriver instance for interacting with the web page.
            text (str): The text to wait for in the page source.
        """

        try:
            assert bool(text in driver.page_source)
        except Exception:
            print("waitForTextPresent: ", repr(text), "not present")
            raise

    def waitForTextNotPresent(self, driver, text):
        """
        Wait for the specified text to be absent in the page source.

        Args:
            driver (WebDriver): The WebDriver instance for interacting with the web page.
            text (str): The text to wait for to be absent in the page source.
        """

        try:
            assert not bool(text in driver.page_source)
        except Exception:
            print("waitForTextNotPresent: ", repr(text), "present")
            raise

    def assertText(self, driver, target, value=""):
        """
        Assert that the text of a specified web element matches the expected value.

        Args:
            driver (WebDriver): The WebDriver instance for interacting with the web page.
            target (str): The identifier for the web element whose text needs to be asserted.
            value (str, optional): The expected text value to compare against (default is an empty string).
        """

        try:
            target_value = find_element(driver, target).text
            print("   assertText target value =" + repr(target_value))
            if value.startswith("exact:"):
                assert target_value == value[len("exact:") :]
            else:
                assert target_value == value
        except Exception:
            print(
                "assertText: ",
                repr(target),
                repr(find_element(driver, target).get_attribute("value")),
                repr(value),
            )
            raise

    def assertNotText(self, driver, target, value=""):
        """
        Assert that the text of a specified web element does not match the expected value.

        Args:
            driver (WebDriver): The WebDriver instance for interacting with the web page.
            target (str): The identifier for the web element whose text needs to be asserted.
            value (str, optional): The expected text value to compare against (default is an empty string).
        """

        try:
            target_value = find_element(driver, target).text
            print("  assertNotText target value =" + repr(target_value))
            if value.startswith("exact:"):
                assert target_value != value[len("exact:") :]
            else:
                assert target_value != value
        except Exception:
            print(
                "assertNotText: ",
                repr(target),
                repr(find_element(driver, target).get_attribute("value")),
                repr(value),
            )
            raise

    def assertValue(self, driver, target, value=""):
        """
        Assert that the value attribute of a specified web element matches the expected value.

        Args:
            driver (WebDriver): The WebDriver instance for interacting with the web page.
            target (str): The identifier for the web element whose value attribute needs to be asserted.
            value (str, optional): The expected value to compare against (default is an empty string).
        """

        try:
            target_value = find_element(driver, target).get_attribute("value")
            print("  assertValue target value =" + repr(target_value))
            assert target_value == value
        except Exception:
            print(
                "assertValue: ",
                repr(target),
                repr(find_element(driver, target).get_attribute("value")),
                repr(value),
            )
            raise

    def assertNotValue(self, driver, target, value=""):
        """
        Assert that the value attribute of a specified web element does not match the expected value.

        Args:
            driver (WebDriver): The WebDriver instance for interacting with the web page.
            target (str): The identifier for the web element whose value attribute needs to be asserted.
            value (str, optional): The expected value to compare against (default is an empty string).
        """

        try:
            target_value = find_element(driver, target).get_attribute("value")
            print("  assertNotValue target value =" + repr(target_value))
            assert target_value != value
        except Exception:
            print(
                "assertNotValue: ",
                repr(target),
                repr(target_value),
                repr(value),
            )
            raise

    def verifyValue(self, driver, target, value=""):
        """
        Verify that the value attribute of a specified web element matches the expected value.

        Args:
            driver (WebDriver): The WebDriver instance for interacting with the web page.
            target (str): The identifier for the web element whose value attribute needs to be verified.
            value (str, optional): The expected value to compare against (default is an empty string).
        """

        try:
            target_value = find_element(driver, target).get_attribute("value")
            print("  verifyValue target value =" + repr(target_value))
            assert target_value == value
        except Exception:
            print(
                "verifyValue: ",
                repr(target),
                repr(find_element(driver, target).get_attribute("value")),
                repr(value),
            )
            raise


class SeleniumTestSuite(object):
    """A Selenium Test Suite"""

    def __init__(self, filename, callback=None):
        """
        Initialize a SeleniumTestSuite instance.

        Args:
            filename (str): The name of the test suite JSON file.
            callback (callable, optional): A callback function to be executed after each test (default is None).
        """
        self.filename = filename
        self.callback = callback

        self.tests = []

        with open(filename, "r") as json_file:
            json_data = json.load(json_file)
            self.title = json_data.get("name", "Untitled Suite")
            self.tests = [
                (test_data.get("name", "Untitled Test"), test_data)
                for test_data in json_data.get("tests", [])
            ]

    def run(self, driver, url):
        """
        Run the Selenium test suite with the specified WebDriver instance and URL.

        Args:
            driver (WebDriver): The WebDriver instance for interacting with the web page.
            url (str): The base URL to be used for the tests.
        """
        for test_title, test_data in self.tests:
            try:
                test = SeleniumTestCase(test_data, self.callback)
                test.run(driver, url)
            except Exception as e:
                print(f"Error in {test_title} ({test.filename}): {e}")
                raise

    def __repr__(self):
        """
        Return a string representation of the SeleniumTestSuite.

        Returns:
            str: A string representation of the test suite, including its title and test titles.
        """
        test_titles = "\n".join([title for title, _ in self.tests])
        return f"{self.title}\n{test_titles}"


class PodSeleniumTests(StaticLiveServerTestCase):
    """Tests the integration of Pod application with Selenium from side files"""

    fixtures = ["initial_data.json"]

    def setUp(self):
        """Set up the tests and initialize custom test data."""
        self.initialize_data()

    @classmethod
    def setUpClass(cls):
        """Create the WebDriver for all Selenium tests."""
        super().setUpClass()
        cls.selenium = WebDriver()
        cls.selenium.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        """Close the WebDriver used."""
        cls.selenium.quit()
        super().tearDownClass()

    @override_settings(DEBUG=False)
    def test_selenium_suites(self):
        """Run Selenium Test Suites from Side files in all installed apps."""
        self.run_all_tests()

    def initialize_data(self):
        """Initialize custom test data."""
        self.user = User.objects.create_user(username="testuser", password="testpassword")
        self.video = Video.objects.create(
            title="first-video",
            owner=self.user,
            video="video.mp4",
            is_draft=False,
            type=Type.objects.get(id=1),
        )

    def run_suite(self, suite_name, suite_url):
        """
        Run a Selenium test suite with the specified name and URL.

        Args:
            suite_name (str): The name of the test suite JSON file.
            suite_url (str): The base URL for the test suite.
        """
        print(f"Running test suite: {suite_name}")

        with open(suite_name, "r") as json_file:
            suite_data = json.load(json_file)
            suite_tests = suite_data.get("tests", [])

        for test_data in suite_tests:
            test_case = SeleniumTestCase(test_data)
            try:
                test_case.run(PodSeleniumTests.selenium, suite_url)
            except Exception as e:
                PodSeleniumTests.selenium.save_screenshot(
                    f"{suite_name}-error_screen.png"
                )
                print(f"Error in suite {suite_name}: {e}")

    def run_all_tests(self):
        """
        Run Selenium test suites in all installed apps.

        This method searches for test suites in integration_tests/tests directories of all installed apps and runs them.
        """
        for app in settings.INSTALLED_APPS:
            app_module = __import__(app, fromlist=["integration_tests"])
            integration_tests_dir = os.path.join(
                os.path.dirname(app_module.__file__), "integration_tests"
            )
            if os.path.exists(integration_tests_dir):
                tests_dir = os.path.join(integration_tests_dir, "tests")
                if os.path.exists(tests_dir):
                    print(f"Running Selenium tests in {app}...")
                    self.run_tests_in_directory(tests_dir)
        print("All tests are DONE")

    def run_tests_in_directory(self, directory):
        """
        Run Selenium test suites in the specified directory.

        Args:
            directory (str): The directory containing test suites.
        """
        for root, dirs, files in os.walk(directory):
            for filename in files:
                if filename.endswith(".side"):
                    suite_name = os.path.join(root, filename)
                    self.run_single_suite(suite_name)

    def run_single_suite(self, suite_name):
        """
        Run a single Selenium test suite.

        Args:
            suite_name (str): The name of the test suite JSON file to run.
        """
        with Display(visible=0, size=(1920, 1080)):
            with WebDriver() as driver:
                PodSeleniumTests.selenium = driver
                PodSeleniumTests.setUpClass()
                try:
                    suite_url = "http://localhost:8080"
                    self.run_suite(suite_name, suite_url)
                except Exception as e:
                    print(f"Error in suite {suite_name}: {e}")
                PodSeleniumTests.tearDownClass()
