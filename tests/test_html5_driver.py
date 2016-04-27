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
import datetime
import unittest

import mock
import pytz

from client_wrapper import browser_client_common
from client_wrapper import html5_driver
from tests import ndt_client_test


class NdtHtml5SeleniumDriverTest(ndt_client_test.NdtClientTest):

    def setUp(self):
        self.mock_driver = mock.Mock()
        self.mock_driver.capabilities = {'version': 'mock_version'}

        wait_until_visible_patcher = mock.patch.object(
            html5_driver.browser_client_common, 'wait_until_element_is_visible')
        self.addCleanup(wait_until_visible_patcher.stop)
        wait_until_visible_patcher.start()
        html5_driver.browser_client_common.wait_until_element_is_visible.return_value = (
            True)

        # Create mock DOM elements that are returned by calls to
        # find_element_by_id.
        self.mock_page_elements = {
            'websocketButton': mock.Mock(),
            'upload-speed': mock.Mock(text='1'),
            'upload-speed-units': mock.Mock(text='Mb/s'),
            'download-speed': mock.Mock(text='2'),
            'download-speed-units': mock.Mock(text='Mb/s'),
            'latency': mock.Mock(text='3'),
            'results': mock.Mock(),
        }
        self.mock_driver.find_element_by_id.side_effect = (
            lambda id: self.mock_page_elements[id])

        # Create mock DOM elements that are returned by calls to
        # find_elements_containing_text.
        self.mock_elements_by_text = {
            'Start Test': mock.Mock(),
            'your upload speed': mock.Mock(),
            'your download speed': mock.Mock(),
        }
        create_browser_patcher = mock.patch.object(
            browser_client_common, 'find_element_containing_text')
        self.addCleanup(create_browser_patcher.stop)
        create_browser_patcher.start()
        browser_client_common.find_element_containing_text.side_effect = (
            lambda _, text: self.mock_elements_by_text[text])

        # Patch the call to create the browser driver to return our mock driver.
        create_browser_patcher = mock.patch.object(browser_client_common,
                                                   'create_browser')
        self.addCleanup(create_browser_patcher.stop)
        create_browser_patcher.start()
        browser_client_common.create_browser.return_value = self.mock_driver

    def test_test_yields_valid_results_when_all_page_elements_are_expected_values(
            self):
        result = html5_driver.NdtHtml5SeleniumDriver(
            browser='firefox',
            url='http://ndt.mock-server.com:7123/',
            timeout=1000).perform_test()

        self.assertEqual(1.0, result.c2s_result.throughput)
        self.assertEqual(2.0, result.s2c_result.throughput)
        self.assertEqual(3.0, result.latency)
        self.assertErrorMessagesEqual([], result.errors)

    def test_fails_gracefully_when_start_button_not_in_dom(self):
        self.mock_elements_by_text['Start Test'] = None

        result = html5_driver.NdtHtml5SeleniumDriver(
            browser='firefox',
            url='http://ndt.mock-server.com:7123/',
            timeout=1).perform_test()

        self.assertIsNone(result.c2s_result.throughput)
        self.assertIsNone(result.s2c_result.throughput)
        self.assertIsNone(result.latency)
        self.assertErrorMessagesEqual(
            [html5_driver.ERROR_START_BUTTON_NOT_IN_DOM], result.errors)

    def test_fails_gracefully_if_wait_for_start_button_times_out(self):
        # Simulate a webdriver timeout when waiting for any element to appear,
        # including the "Start Test" button.
        html5_driver.browser_client_common.wait_until_element_is_visible.return_value = (
            False)

        result = html5_driver.NdtHtml5SeleniumDriver(
            browser='firefox',
            url='http://ndt.mock-server.com:7123/',
            timeout=1).perform_test()

        self.assertIsNone(result.c2s_result.throughput)
        self.assertIsNone(result.s2c_result.throughput)
        self.assertIsNone(result.latency)
        self.assertErrorMessagesEqual(
            [html5_driver.ERROR_TIMED_OUT_WAITING_FOR_START_BUTTON],
            result.errors)

    def test_test_in_progress_timeout_yields_timeout_errors(self):
        """If each test times out, expect an error for each timeout."""
        # Make the "Start Test" button visible, but others time out.
        html5_driver.browser_client_common.wait_until_element_is_visible.side_effect = [
            True,  # "Start Test" button
            False,  # Upload speed label
            False,  # Download speed label
            False,  # Results div
        ]
        result = html5_driver.NdtHtml5SeleniumDriver(
            browser='firefox',
            url='http://ndt.mock-server.com:7123/',
            timeout=1).perform_test()

        self.assertErrorMessagesEqual(
            [browser_client_common.ERROR_C2S_NEVER_STARTED,
             browser_client_common.ERROR_S2C_NEVER_STARTED,
             browser_client_common.ERROR_S2C_NEVER_ENDED], result.errors)

    def test_c2s_start_timeout_yields_errors(self):
        """If waiting for just c2s start times out, expect just one error."""
        html5_driver.browser_client_common.wait_until_element_is_visible.side_effect = [
            True,  # "Start Test" button
            False,  # Upload speed label
            True,  # Download speed label
            True,  # Results div
        ]
        result = html5_driver.NdtHtml5SeleniumDriver(
            browser='firefox',
            url='http://ndt.mock-server.com:7123/',
            timeout=1).perform_test()

        self.assertErrorMessagesEqual(
            [browser_client_common.ERROR_C2S_NEVER_STARTED], result.errors)

    def test_results_page_displays_non_numeric_latency(self):
        self.mock_page_elements['latency'] = mock.Mock(text='Non-numeric value')
        result = html5_driver.NdtHtml5SeleniumDriver(
            browser='firefox',
            url='http://ndt.mock-server.com:7123/',
            timeout=1000).perform_test()

        self.assertEqual(1.0, result.c2s_result.throughput)
        self.assertEqual(2.0, result.s2c_result.throughput)
        self.assertIsNone(result.latency)
        self.assertErrorMessagesEqual(
            ['illegal value shown for latency: Non-numeric value'],
            result.errors)

    def test_results_page_displays_non_numeric_c2s_throughput(self):
        self.mock_page_elements['upload-speed'] = mock.Mock(
            text='Non-numeric value')
        result = html5_driver.NdtHtml5SeleniumDriver(
            browser='firefox',
            url='http://ndt.mock-server.com:7123/',
            timeout=1000).perform_test()

        self.assertIsNone(result.c2s_result.throughput)
        self.assertEqual(2.0, result.s2c_result.throughput)
        self.assertEqual(3.0, result.latency)
        self.assertErrorMessagesEqual(
            ['illegal value shown for c2s throughput: Non-numeric value'],
            result.errors)

    def test_results_page_displays_non_numeric_s2c_throughput(self):
        self.mock_page_elements['download-speed'] = mock.Mock(
            text='Non-numeric value')
        result = html5_driver.NdtHtml5SeleniumDriver(
            browser='firefox',
            url='http://ndt.mock-server.com:7123/',
            timeout=1000).perform_test()

        self.assertEqual(1.0, result.c2s_result.throughput)
        self.assertIsNone(result.s2c_result.throughput)
        self.assertEqual(3.0, result.latency)
        self.assertErrorMessagesEqual(
            ['illegal value shown for s2c throughput: Non-numeric value'],
            result.errors)

    def test_results_page_displays_non_numeric_metrics(self):
        """A results page with non-numeric metrics results in error list errors.

        When latency, c2s_throughput, and s2c_throughput are all non-numeric values,
        corresponding error objects are added to the errors list that indicate
        that each of these values is invalid.
        """
        self.mock_page_elements['upload-speed'] = mock.Mock(
            text='Non-numeric value')
        self.mock_page_elements['download-speed'] = mock.Mock(
            text='Non-numeric value')
        self.mock_page_elements['latency'] = mock.Mock(text='Non-numeric value')

        result = html5_driver.NdtHtml5SeleniumDriver(
            browser='firefox',
            url='http://ndt.mock-server.com:7123/',
            timeout=1000).perform_test()

        self.assertIsNone(result.c2s_result.throughput)
        self.assertIsNone(result.s2c_result.throughput)
        self.assertIsNone(result.latency)
        self.assertErrorMessagesEqual(
            ['illegal value shown for c2s throughput: Non-numeric value',
             'illegal value shown for s2c throughput: Non-numeric value',
             'illegal value shown for latency: Non-numeric value'],
            result.errors)

    def test_s2c_gbps_speed_conversion(self):
        """Test s2c speed converts from Gb/s to Mb/s correctly."""
        # If s2c speed is 72 Gb/s and c2s is speed is 34 in the browser
        self.mock_page_elements['upload-speed'] = mock.Mock(text='34')
        self.mock_page_elements['upload-speed-units'] = mock.Mock(text='Mb/s')
        self.mock_page_elements['download-speed'] = mock.Mock(text='72')
        self.mock_page_elements['download-speed-units'] = mock.Mock(text='Gb/s')

        result = html5_driver.NdtHtml5SeleniumDriver(
            browser='firefox',
            url='http://ndt.mock-server.com:7123/',
            timeout=1000).perform_test()

        # Then s2c is converted from Gb/s to Mb/s
        self.assertEqual(72000.0, result.s2c_result.throughput)
        # And c2s is not
        self.assertEqual(34.0, result.c2s_result.throughput)
        self.assertEqual(3.0, result.latency)
        self.assertErrorMessagesEqual([], result.errors)

    def test_invalid_throughput_unit_yields_error(self):
        self.mock_page_elements['upload-speed-units'] = mock.Mock(text='banana')

        result = html5_driver.NdtHtml5SeleniumDriver(
            browser='firefox',
            url='http://ndt.mock-server.com:7123/',
            timeout=1000).perform_test()

        self.assertIsNone(result.c2s_result.throughput)
        self.assertEqual(2.0, result.s2c_result.throughput)
        self.assertEqual(3.0, result.latency)
        self.assertErrorMessagesEqual(
            ['Invalid throughput unit specified: banana'], result.errors)

    def test_c2s_kbps_speed_conversion(self):
        """Test c2s speed converts from kb/s to Mb/s correctly."""
        # If c2s speed is 72 kb/s and s2c speed is 34 in the browser
        self.mock_page_elements['upload-speed'] = mock.Mock(text='72')
        self.mock_page_elements['upload-speed-units'] = mock.Mock(text='kb/s')
        self.mock_page_elements['download-speed'] = mock.Mock(text='34')
        self.mock_page_elements['download-speed-units'] = mock.Mock(text='Mb/s')
        result = html5_driver.NdtHtml5SeleniumDriver(
            browser='firefox',
            url='http://ndt.mock-server.com:7123/',
            timeout=1000).perform_test()

        # Then c2s is converted from kb/s to Mb/s
        self.assertEqual(0.072, result.c2s_result.throughput)
        # And s2c is not
        self.assertEqual(34.0, result.s2c_result.throughput)
        self.assertEqual(3.0, result.latency)
        self.assertErrorMessagesEqual([], result.errors)

    def test_ndt_result_increments_time_correctly(self):
        # Create a list of mock times to be returned by datetime.now().
        times = []
        for i in range(11):
            times.append(datetime.datetime(2016, 1, 1, 0, 0, i))

        with mock.patch.object(html5_driver.datetime,
                               'datetime',
                               autospec=True) as mocked_datetime:
            # Patch datetime.now to return the next mock time on every call to
            # now().
            mocked_datetime.now.side_effect = times

            # Modify the create_browser mock to increment the clock forward one
            # call.
            def mock_create_browser(unused_browser_name):
                datetime.datetime.now(pytz.utc)
                return self.mock_driver

            browser_client_common.create_browser.side_effect = (
                mock_create_browser)

            # Modify the wait_until_element_is_visible mock to increment the
            # clock forward one call.
            def mock_visibility_of(unused_driver, unused_element,
                                   unused_timeout):
                datetime.datetime.now(pytz.utc)
                return True

            html5_driver.browser_client_common.wait_until_element_is_visible.side_effect = (
                mock_visibility_of)

            result = html5_driver.NdtHtml5SeleniumDriver(
                browser='firefox',
                url='http://ndt.mock-server.com:7123/',
                timeout=1).perform_test()

        # Verify the recorded times matches the expected sequence.
        self.assertEqual(times[0], result.start_time)
        # times[1] is the call from mock_firefox
        # times[2] is the check for visibility of "Start Test" button
        # times[3] is the check for visibility of c2s test start
        self.assertEqual(times[4], result.c2s_result.start_time)
        # times[5] is the check for visibility of s2c test start (start of s2c
        #   marks the end of c2s)
        self.assertEqual(times[6], result.c2s_result.end_time)
        self.assertEqual(times[7], result.s2c_result.start_time)
        # times[8] is the check for visibility of results page
        self.assertEqual(times[9], result.s2c_result.end_time)
        self.assertEqual(times[10], result.end_time)


if __name__ == '__main__':
    unittest.main()
