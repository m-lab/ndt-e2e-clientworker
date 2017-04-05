# Copyright 2016 Measurement Lab
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import absolute_import
import unittest

import mock
from selenium.common import exceptions

from client_wrapper import browser_client_common
from client_wrapper import names
from tests import ndt_client_testcase


class CreateBrowserTest(unittest.TestCase):
    """Tests for create_browser function."""

    @mock.patch.object(browser_client_common.webdriver, 'Firefox')
    def test_create_firefox_browser_succeeds(self, mock_firefox):
        mock_browser_driver = mock.Mock('mock firefox driver')
        mock_browser_driver.quit = mock.Mock()
        mock_browser_driver.set_page_load_timeout = mock.Mock()
        mock_firefox.return_value = mock_browser_driver

        with browser_client_common.create_browser(names.FIREFOX) as driver:
            self.assertTrue(mock_firefox.called)
            self.assertEqual(mock_browser_driver, driver)
            self.assertFalse(mock_browser_driver.quit.called)
            self.assertTrue(
                mock_browser_driver.set_page_load_timeout.called_once_with(10))

        self.assertTrue(mock_browser_driver.quit.called)

    @mock.patch.object(browser_client_common.webdriver, 'Chrome')
    def test_create_chrome_browser_succeeds(self, mock_chrome):
        mock_browser_driver = mock.Mock('mock chrome driver')
        mock_browser_driver.quit = mock.Mock()
        mock_browser_driver.set_page_load_timeout = mock.Mock()
        mock_chrome.return_value = mock_browser_driver

        with browser_client_common.create_browser(names.CHROME) as driver:
            self.assertTrue(mock_chrome.called)
            self.assertEqual(mock_browser_driver, driver)
            self.assertFalse(mock_browser_driver.quit.called)
            self.assertTrue(
                mock_browser_driver.set_page_load_timeout.called_once_with(10))

        self.assertTrue(mock_browser_driver.quit.called)

    @mock.patch.object(browser_client_common.webdriver, 'Edge')
    def test_create_edge_driver_succeeds(self, mock_edge):
        mock_browser_driver = mock.Mock('mock edge driver')
        mock_browser_driver.quit = mock.Mock()
        mock_browser_driver.set_page_load_timeout = mock.Mock()
        mock_edge.return_value = mock_browser_driver

        with browser_client_common.create_browser(names.EDGE) as driver:
            self.assertTrue(mock_edge.called)
            self.assertEqual(mock_browser_driver, driver)
            self.assertFalse(mock_browser_driver.quit.called)
            self.assertTrue(
                mock_browser_driver.set_page_load_timeout.called_once_with(10))

        self.assertTrue(mock_browser_driver.quit.called)

    @mock.patch.object(browser_client_common.webdriver, 'Safari')
    def test_create_safari_browser_succeeds(self, mock_safari):
        mock_browser_driver = mock.Mock('mock safari driver')
        mock_browser_driver.quit = mock.Mock()
        mock_browser_driver.set_page_load_timeout = mock.Mock()
        mock_safari.return_value = mock_browser_driver

        with browser_client_common.create_browser(names.SAFARI) as driver:
            self.assertTrue(mock_safari.called)
            self.assertEqual(mock_browser_driver, driver)
            self.assertFalse(mock_browser_driver.quit.called)
            self.assertTrue(
                mock_browser_driver.set_page_load_timeout.called_once_with(10))

        self.assertTrue(mock_browser_driver.quit.called)

    def test_create_unrecognized_browser_raises_error(self):
        with self.assertRaises(ValueError):
            with browser_client_common.create_browser('foo'):
                pass


class GetBrowserVersionTest(unittest.TestCase):

    def test_get_version_returns_successfully_when_driver_has_standard_version(
            self):
        mock_driver = mock.Mock()
        mock_driver.capabilities = {'version': '1.2.3'}

        self.assertEqual('1.2.3',
                         browser_client_common.get_browser_version(mock_driver))

    def test_get_version_returns_successfully_when_driver_has_edge_style_version(
            self):
        """Microsoft Edge's WebDriver puts version in 'browserVersion' field."""
        mock_driver = mock.Mock()
        mock_driver.capabilities = {'browserVersion': '1.2.3'}

        self.assertEqual('1.2.3',
                         browser_client_common.get_browser_version(mock_driver))

    def test_get_version_raises_BrowserVersionMissing_when_driver_has_no_version(
            self):
        mock_driver = mock.Mock()
        mock_driver.capabilities = {}

        with self.assertRaises(browser_client_common.BrowserVersionMissing):
            browser_client_common.get_browser_version(mock_driver)


class LoadUrlTest(ndt_client_testcase.NdtClientTestCase):
    """Tests for load_url function."""

    def test_load_url_loads_correct_url(self):
        mock_driver = mock.Mock(spec=browser_client_common.webdriver.Firefox)
        errors = []
        self.assertTrue(browser_client_common.load_url(
            mock_driver, 'http://fake.url/foo', errors))
        self.assertListEqual([], errors)
        mock_driver.get.assert_called_once_with('http://fake.url/foo')

    def test_load_url_adds_error_when_loading_url_fails(self):
        mock_driver = mock.Mock(spec=browser_client_common.webdriver.Firefox)
        mock_driver.get.side_effect = exceptions.WebDriverException(
            'dummy exception')
        errors = []
        self.assertFalse(browser_client_common.load_url(
            mock_driver, 'http://fake.url/foo', errors))
        self.assertErrorMessagesEqual(
            ['Failed to load URL: http://fake.url/foo'], errors)

    def test_load_url_adds_timeout_error_to_result(self):
        mock_driver = mock.Mock(spec=browser_client_common.webdriver.Firefox)
        errors = []
        mock_driver.get.side_effect = exceptions.TimeoutException(
            'dummy exception')
        self.assertFalse(browser_client_common.load_url(
            mock_driver, 'http://fake.url/foo', errors))
        self.assertErrorMessagesEqual(
            ['Timed out waiting for page to load.',
             'Failed to load URL: http://fake.url/foo'], errors)


class WaitUntilElementIsVisibleTest(unittest.TestCase):
    """Tests for wait_until_element_is_visible function."""

    @mock.patch.object(browser_client_common.ui, 'WebDriverWait')
    @mock.patch.object(browser_client_common.expected_conditions,
                       'visibility_of')
    def test_wait_until_element_is_visible_waits_for_correct_element(
            self, mock_visibility, mock_webdriver_wait):
        # Mock wait object to be returned by ui.WebDriverWait
        mock_wait = mock.Mock()
        mock_webdriver_wait.return_value = mock_wait

        mock_driver = mock.Mock()
        mock_driver.capabilities = {'browserName': 'LOL', 'version': 'LOL'}
        # In reality, these would be objects, but we mock with strings for
        # simplicity.
        mock_element = 'mock DOM element'
        mock_condition = 'mock expected condition'

        browser_client_common.expected_conditions.visibility_of.return_value = mock_condition

        # Verify that the function returns True when there is no timeout.
        self.assertTrue(browser_client_common.wait_until_element_is_visible(
            mock_driver, mock_element, 20))
        # Verify we're waiting with the correct Selenium driver for the correct
        # timeout.
        mock_webdriver_wait.assert_called_once_with(mock_driver, 20)
        # Verify we're setting the expected visibility of the right element.
        mock_visibility.assert_called_once_with(mock_element)
        # Verify we're waiting on the right condition.
        mock_wait.until.assert_called_once_with(mock_condition)

    @mock.patch.object(browser_client_common.ui, 'WebDriverWait')
    def test_wait_until_element_is_visible_returns_false_when_wait_times_out(
            self, mock_webdriver_wait):
        mock_webdriver_wait.side_effect = exceptions.TimeoutException(
            'mock timeout exception')

        mock_driver = mock.Mock()
        mock_driver.capabilities = {'browserName': 'LOL', 'version': 'LOL'}
        # In reality, this would be an object, but we mock with a string for
        # simplicity.
        mock_element = 'mock DOM element'

        # Verify that the function returns False when the wait times out.
        self.assertFalse(browser_client_common.wait_until_element_is_visible(
            mock_driver, mock_element, 20))


class GetElementContainingTextTest(unittest.TestCase):
    """Tests for get_element_containing_text function."""

    def test_get_element_containing_text_finds_correct_element_when_element_exists(
            self):
        mock_driver = mock.Mock()
        mock_driver.find_element_by_xpath.return_value = 'mock element'
        self.assertEqual('mock element',
                         browser_client_common.find_element_containing_text(
                             mock_driver, 'foo'))
        mock_driver.find_element_by_xpath.assert_called_once_with(
            '//*[contains(text(), \'foo\')]')

    def test_get_element_containing_text_returns_None_when_element_does_not_exist(
            self):
        mock_driver = mock.Mock()
        mock_driver.find_element_by_xpath.return_value = None
        self.assertIsNone(browser_client_common.find_element_containing_text(
            mock_driver, 'foo'))


if __name__ == '__main__':
    unittest.main()
