"""Esup-Pod integration tests.

*  run with 'python manage.py test -v 3 --settings=pod.main.test_settings pod.main.integration_tests.selenium_pod_integration_tests'
"""

import importlib
import os
import shutil

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test.utils import override_settings
from django.core.files.temp import NamedTemporaryFile
from pod.video_encode_transcript.encode import encode_video

from selenium.webdriver.firefox.webdriver import WebDriver

from pod.video.models import Video, Type


target_cache = {}
current_side_file = None


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
        cls.driver = WebDriver()
        cls.vars = {}
        cls.driver.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        """Close the WebDriver used."""
        cls.driver.quit()
        super().tearDownClass()

    @override_settings(DEBUG=False)
    def test_selenium_suites(self):
        """Run Selenium Test Suites from Side files in all installed apps."""
        self.driver.get(f"{self.live_server_url}/")
        # run initial test
        self.run_initial_tests()
        # run anonyme test
        self.run_tests("anonyme")
        # run simple user test
        # run staff uesr test

    def initialize_data(self):
        """Initialize custom test data."""
        self.user_simple = User.objects.create_user(username="user", password="user")
        self.user_staff = User.objects.create_user(
            username="staff_user",
            password="user",
            is_staff=True
        )
        # copy video file
        self.video = Video.objects.create(
            title="first-video",
            owner=self.user_simple,
            is_draft=False,
            type=Type.objects.get(id=1),
        )
        tempfile = NamedTemporaryFile(delete=True)
        self.video.video.save("test.mp4", tempfile)
        dest = os.path.join(settings.MEDIA_ROOT, self.video.video.name)
        shutil.copyfile("pod/main/static/video_test/pod.mp4", dest)
        self.video_staff = Video.objects.create(
            title="video-staff",
            owner=self.user_staff,
            is_draft=False,
            type=Type.objects.get(id=1),
        )
        tempfile = NamedTemporaryFile(delete=True)
        self.video_staff.video.save("test.mp4", tempfile)
        dest = os.path.join(settings.MEDIA_ROOT, self.video_staff.video.name)
        shutil.copyfile("pod/main/static/video_test/pod.mp4", dest)

        encode_video(self.video.id)
        encode_video(self.video_staff.id)

    def run_suite(self, suite_name, prefixe=""):
        """
        Run a Selenium test suite with the specified name and URL.

        Args:
            suite_name (str): The name of the test suite python file.
            suite_url (str): The base URL for the test suite.
        """
        global current_side_file
        print(f"Running test suite: {suite_name}")

        fname, ext = os.path.splitext(os.path.basename(suite_name))
        def_name = fname.replace(prefixe, "")
        command_lines = []
        import_lines = []
        find_def_name = False

        with open(suite_name, 'r', encoding="utf8", errors='ignore') as fp:
            # read all lines in a list
            for l_no, line in enumerate(fp):
                # check if string present on a current line
                if line.startswith("from selenium"):
                    import_lines.append(line)
                if line.find(def_name) != -1:
                    find_def_name = True
                    continue
                if find_def_name:
                    if len(line.strip()) == 0 :
                        break
                    command_lines.append(self.format_line(line))

        tempfile = suite_name.replace(fname, def_name)
        print(tempfile)
        with open(tempfile, "w") as f:
            f.writelines(import_lines)
            f.write("\n")
            f.write("def %s(cls):\n" % def_name)
            for command in command_lines:
                f.write("    %s\n" % command)
            f.write("\n")

        import_module = tempfile[tempfile.index('/pod/') + 1:]
        import_module = import_module.replace("/", ".").replace(".py", "")
        module = importlib.import_module(import_module)
        module_fct = getattr(module, def_name)
        module_fct(self)
        os.remove(tempfile)

    def format_line(self, line):
        formatted_line = line
        formatted_line = formatted_line.strip().replace("undefined", "")
        formatted_line = formatted_line.replace("self", "cls")
        formatted_line = formatted_line.replace(
            "http://localhost:9090", self.live_server_url
        )
        return formatted_line

    def run_initial_tests(self):
        """Run initial Selenium test suites for cookies and login."""
        initial_tests_dir = os.path.join(
            os.path.dirname(__file__), "init_integration_tests")
        cookies_test_path = os.path.join(initial_tests_dir, "side_init_test_cookies.py")
        self.run_single_suite(cookies_test_path, "side_init_")
        deconnexion_test_path = os.path.join(
            initial_tests_dir,
            "side_init_test_deconnexion.py"
        )
        self.run_single_suite(deconnexion_test_path, "side_init_")

    def run_tests(self, type):
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
                    print(f"Running Selenium {type} tests in {app}...")
                    self.run_tests_in_directory(tests_dir, type)
        print("All %s tests are DONE" % type)

    def run_tests_in_directory(self, directory, type):
        """
        Run Selenium test suites in the specified directory.

        Args:
            directory (str): The directory containing test suites.
            type (str): The type of test to run.
        """
        for root, dirs, files in os.walk(directory):
            for filename in files:
                prefixe = "side_%s_" % type
                if filename.startswith(prefixe):
                    suite_name = os.path.join(root, filename)
                    self.run_single_suite(suite_name, prefixe)

    def run_single_suite(self, suite_name, suffixe):
        """
        Run a single Selenium test suite.

        Args:
            suite_name (str): The name of the test suite python file to run.
        """
        try:
            self.run_suite(suite_name, suffixe)
            PodSeleniumTests.driver.save_screenshot(f"{suite_name}-info_screen.png")
        except Exception:
            PodSeleniumTests.driver.save_screenshot(f"{suite_name}-error_screen.png")
            print("ERROR !")
            print(f"Side path : {current_side_file}")
            self.fail(f"Error in suite {suite_name}")
