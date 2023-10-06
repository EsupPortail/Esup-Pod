from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import json
import os
from pyvirtualdisplay import Display
from django.conf import settings
from selenium.webdriver.support.ui import Select
from django.test import override_settings

# python manage.py test -v 3 --settings=pod.main.test_settings \
# pod.main.integration_tests.selenium_pod_integration_tests

target_cache = {}


def find_element(driver, target):
    """find an element in the page"""

    if target in target_cache:
        target = target_cache[target]

    if target.startswith('link='):
        try:
            return driver.find_element(By.LINK_TEXT, target[5:])
        except NoSuchElementException:
            result = driver.find_element(By.LINK_TEXT, target[5:].lower())
            target_cache[target] = 'link=' + target[5:].lower()
            msg = '   label %s is being cached as %s'
            print(msg, target, target_cache[target])
            return result
    elif target.startswith('//'):
        return driver.find_element(By.XPATH, target)

    elif target.startswith('xpath='):
        return driver.find_element(By.XPATH, target[6:])

    elif target.startswith('css='):
        return driver.find_element(By.CSS_SELECTOR, target[4:])

    elif target.startswith('id='):
        return driver.find_element(By.ID, target[3:])

    elif target.startswith('name='):
        return driver.find_element(By.NAME, target[5:])
    else:
        direct = (
            driver.find_element(By.NAME, target)
            or driver.find_element(By.ID, target)
            or driver.find_element(By.LINK_TEXT, target)
        )
        if direct:
            return direct
        raise Exception('Don\'t know how to find %s' % target)


class SeleniumTestCase(object):
    """A Single Selenium Test Case"""

    def __init__(self, test_data, callback=None):
        self.test_data = test_data
        self.callback = callback
        self.base_url = None
        self.commands = []

    def run(self, driver, url):
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
            print(f'   {method_name} {args}')
            method(*args)
        if self.callback:
            self.callback(driver.page_source)

    def cookies_commands(self, driver, url):
        with open('pod/main/integration_tests/commands/cookies_commands.side', 'r') as side_file:
            side_data = json.load(side_file)
            self.test_data['commands'] = side_data.get('commands', [])
            self.run(driver, url)

    def open(self, driver, target):
        driver.get(self.base_url + target)

    def click(self, driver, target):
        element = find_element(driver, target)
        driver.execute_script("arguments[0].scrollIntoView();", element)
        element.click()

    def clickAndWait(self, driver, target):
        self.click(driver, target)

    def type(self, driver, target, text=''):
        element = find_element(driver, target)
        element.click()
        element.clear()
        element.send_keys(text)

    def select(self, driver, target, value):
        element = find_element(driver, target)
        if value.startswith('label='):
            Select(element).select_by_visible_text(value[6:])
        else:
            msg = "Don\'t know how to select %s on %s"
            raise Exception(msg % (value, target))

    def verifyTextPresent(self, driver, text):
        try:
            source = driver.page_source
            assert bool(text in source)
        except:
            print(
                'verifyTextPresent: ',
                repr(text),
                'not present in',
                repr(source)
            )
            raise

    def verifyTextNotPresent(self, driver, text):
        try:
            assert not bool(text in driver.page_source)
        except:
            print(
                'verifyNotTextPresent: ',
                repr(text),
                'present'
            )
            raise

    def assertElementPresent(self, driver, target):
        try:
            assert bool(find_element(driver, target))
        except:
            print('assertElementPresent: ', repr(target), 'not present')
            raise

    def verifyElementPresent(self, driver, target):
        try:
            assert bool(find_element(driver, target))
        except:
            print('verifyElementPresent: ', repr(target), 'not present')
            raise

    def verifyElementNotPresent(self, driver, target):
        present = True
        try:
            find_element(driver, target)
        except NoSuchElementException:
            present = False

        try:
            assert not present
        except:
            print('verifyElementNotPresent: ', repr(target), 'present')
            raise

    def waitForTextPresent(self, driver, text):
        try:
            assert bool(text in driver.page_source)
        except:
            print('waitForTextPresent: ', repr(text), 'not present')
            raise

    def waitForTextNotPresent(self, driver, text):
        try:
            assert not bool(text in driver.page_source)
        except:
            print('waitForTextNotPresent: ', repr(text), 'present')
            raise

    def assertText(self, driver, target, value=u''):
        try:
            target_value = find_element(driver, target).text
            print('   assertText target value =' + repr(target_value))
            if value.startswith('exact:'):
                assert target_value == value[len('exact:'):]
            else:
                assert target_value == value
        except:
            print(
                'assertText: ',
                repr(target),
                repr(find_element(driver, target).get_attribute('value')),
                repr(value),
            )
            raise

    def assertNotText(self, driver, target, value=u''):
        try:
            target_value = find_element(driver, target).text
            print('  assertNotText target value =' + repr(target_value))
            if value.startswith('exact:'):
                assert target_value != value[len('exact:'):]
            else:
                assert target_value != value
        except:
            print(
                'assertNotText: ',
                repr(target),
                repr(find_element(driver, target).get_attribute('value')),
                repr(value),
            )
            raise

    def assertValue(self, driver, target, value=u''):
        try:
            target_value = find_element(driver, target).get_attribute('value')
            print('  assertValue target value =' + repr(target_value))
            assert target_value == value
        except:
            print(
                'assertValue: ',
                repr(target),
                repr(find_element(driver, target).get_attribute('value')),
                repr(value),
            )
            raise

    def assertNotValue(self, driver, target, value=u''):
        try:
            target_value = find_element(driver, target).get_attribute('value')
            print('  assertNotValue target value =' + repr(target_value))
            assert target_value != value
        except:
            print(
                'assertNotValue: ',
                repr(target),
                repr(target_value),
                repr(value),
            )
            raise

    def verifyValue(self, driver, target, value=u''):
        try:
            target_value = find_element(driver, target).get_attribute('value')
            print('  verifyValue target value =' + repr(target_value))
            assert target_value == value
        except:
            print(
                'verifyValue: ',
                repr(target),
                repr(find_element(driver, target).get_attribute('value')),
                repr(value),
            )
            raise

    def selectWindow(self, driver, window):
        pass


class SeleniumTestSuite(object):
    """A Selenium Test Suite"""

    def __init__(self, filename, callback=None):
        self.filename = filename
        self.callback = callback

        self.tests = []

        with open(filename, 'r') as json_file:
            json_data = json.load(json_file)
            self.title = json_data.get('name', 'Untitled Suite')
            self.tests = [(test_data.get('name', 'Untitled Test'), test_data)
                          for test_data in json_data.get('tests', [])]

    def run(self, driver, url):
        print("ICI AVEC : ", driver, url)
        for test_title, test_data in self.tests:
            try:
                test = SeleniumTestCase(test_data, self.callback)
                test.run(driver, url)
            except Exception as e:
                print(f'Error in {test_title} ({test.filename}): {e}')
                raise

    def __repr__(self):
        test_titles = '\n'.join([title for title, _ in self.tests])
        return f'{self.title}\n{test_titles}'


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

    @override_settings(DEBUG=False)
    def test_selenium_suites(self):
        """Run Selenium Test Suites from Side files in all installed apps"""
        run_all_tests()


def run_suite(suite_name, suite_url):
    print(f'Running test suite: {suite_name}')

    with open(suite_name, 'r') as json_file:
        suite_data = json.load(json_file)
        suite_tests = suite_data.get('tests', [])

    for test_data in suite_tests:
        test_case = SeleniumTestCase(test_data)
        try:
            test_case.run(PodSeleniumTests.selenium, suite_url)
        except Exception as e:
            PodSeleniumTests.selenium.save_screenshot(f'{suite_name}-error_screen.png')
            print(f'Error in suite {suite_name}: {e}')


def run_all_tests():
    for app in settings.INSTALLED_APPS:
        app_module = __import__(app, fromlist=["integration_tests"])
        integration_tests_dir = os.path.join(
            os.path.dirname(app_module.__file__), "integration_tests"
        )
        if os.path.exists(integration_tests_dir):
            tests_dir = os.path.join(integration_tests_dir, "tests")
            if os.path.exists(tests_dir):
                print(f"Running Selenium tests in {app}...")
                run_tests_in_directory(tests_dir)


def run_tests_in_directory(directory):
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if filename.endswith('.side'):
                suite_name = os.path.join(root, filename)
                run_single_suite(suite_name)


def run_single_suite(suite_name):
    with Display(visible=0, size=(1920, 1080)):
        with WebDriver() as driver:
            PodSeleniumTests.selenium = driver
            PodSeleniumTests.setUpClass()
            try:
                suite_url = "http://localhost:8080"
                run_suite(suite_name, suite_url)
            except Exception as e:
                print(f'Error in suite {suite_name}: {e}')
            PodSeleniumTests.tearDownClass()
