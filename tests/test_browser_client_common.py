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
from selenium import webdriver
from selenium.common import exceptions
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support import ui

from client_wrapper import browser_client_common
from client_wrapper import names
from tests import ndt_client_test


class CreateBrowserTest(ndt_client_test.NdtClientTest):
    """Tests for create_browser function."""

    @mock.patch.object(webdriver, 'Firefox')
    def test_create_firefox_browser_succeeds(self, mock_firefox):
        mock_firefox.return_value = 'mock firefox driver'

        self.assertEqual('mock firefox driver',
                         browser_client_common.create_browser(names.FIREFOX))
        self.assertTrue(mock_firefox.called)

    @mock.patch.object(webdriver, 'Chrome')
    def test_create_chrome_browser_succeeds(self, mock_chrome):
        mock_chrome.return_value = 'mock chrome driver'

        self.assertEqual('mock chrome driver',
                         browser_client_common.create_browser(names.CHROME))
        self.assertTrue(mock_chrome.called)

    @mock.patch.object(webdriver, 'Edge')
    def test_create_edge_driver_succeeds(self, mock_edge):
        mock_edge.return_value = 'mock edge driver'

        self.assertEqual('mock edge driver',
                         browser_client_common.create_browser(names.EDGE))
        self.assertTrue(mock_edge.called)

    @mock.patch.object(webdriver, 'Safari')
    def test_create_safari_browser_succeeds(self, mock_safari):
        mock_safari.return_value = 'mock safari driver'

        self.assertEqual('mock safari driver',
                         browser_client_common.create_browser(names.SAFARI))
        self.assertTrue(mock_safari.called)

    def test_create_unrecognized_browser_raises_error(self):
        with self.assertRaises(ValueError):
            browser_client_common.create_browser('not a real browser name')


class LoadUrlTest(ndt_client_test.NdtClientTest):
    """Tests for load_url function."""

    def test_load_url_loads_correct_url(self):
        mock_driver = mock.Mock(spec=webdriver.Firefox)
        errors = []
        self.assertTrue(browser_client_common.load_url(
            mock_driver, 'http://fake.url/foo', errors))
        self.assertListEqual([], errors)
        mock_driver.get.assert_called_once_with('http://fake.url/foo')

    def test_load_url_adds_error_when_loading_url_fails(self):
        mock_driver = mock.Mock(spec=webdriver.Firefox)
        mock_driver.get.side_effect = exceptions.WebDriverException(
            'dummy exception')
        errors = []
        self.assertFalse(browser_client_common.load_url(
            mock_driver, 'http://fake.url/foo', errors))
        self.assertErrorMessagesEqual(
            ['Failed to load URL: http://fake.url/foo'], errors)


class WaitUntilElementIsVisibleTest(ndt_client_test.NdtClientTest):
    """Tests for wait_until_element_is_visible function."""

    def setUp(self):
        wait_patcher = mock.patch.object(ui, 'WebDriverWait')
        self.addCleanup(wait_patcher.stop)
        wait_patcher.start()

        visibility_patcher = mock.patch.object(expected_conditions,
                                               'visibility_of',
                                               autospec=True)
        self.addCleanup(visibility_patcher.stop)
        visibility_patcher.start()

    def test_wait_until_element_is_visible_waits_for_correct_element(self):
        # Mock wait object to be returned by ui.WebDriverWait
        mock_wait = mock.Mock()
        ui.WebDriverWait.return_value = mock_wait

        # In reality, these would be objects, but we mock with strings for
        # simplicity.
        mock_driver = 'mock driver'
        mock_element = 'mock DOM element'
        mock_condition = 'mock expected condition'

        expected_conditions.visibility_of.return_value = mock_condition

        # Verify that the function returns True when there is no timeout.
        self.assertTrue(browser_client_common.wait_until_element_is_visible(
            mock_driver, mock_element, 20))
        # Verify we're waiting with the correct Selenium driver for the correct
        # timeout.
        ui.WebDriverWait.assert_called_once_with(mock_driver, 20)
        # Verify we're setting the expected visibility of the right element.
        expected_conditions.visibility_of.assert_called_once_with(mock_element)
        # Verify we're waiting on the right condition.
        mock_wait.until.assert_called_once_with(mock_condition)

    def test_wait_until_element_is_visible_returns_false_when_wait_times_out(
            self):
        ui.WebDriverWait.side_effect = exceptions.TimeoutException(
            'mock timeout exception')

        # In reality, these would be objects, but we mock with strings for
        # simplicity.
        mock_driver = 'mock driver'
        mock_element = 'mock DOM element'

        # Verify that the function returns False when the wait times out.
        self.assertFalse(browser_client_common.wait_until_element_is_visible(
            mock_driver, mock_element, 20))


class GetElementContainingTextTest(ndt_client_test.NdtClientTest):
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
