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
import contextlib
import datetime
import unittest

import mock
import pytz
from selenium.common import exceptions

from client_wrapper import banjo_driver
from client_wrapper import browser_client_common
from client_wrapper import names
from client_wrapper import results
from tests import ndt_client_testcase


class BanjoDriverTest(ndt_client_testcase.NdtClientTestCase):

    def setUp(self):
        self.apply_patches_for_create_browser()
        self.define_mock_behavior_for_find_element_by_id()
        self.define_mock_behavior_for_find_element_by_xpath()
        self.apply_patches_for_wait_until_element_is_visible()
        self.apply_patches_for_waiting_on_status_banner_text()

        self.banjo = banjo_driver.BanjoDriver(names.FIREFOX,
                                              'http://fakelocalhost:1234/foo')

    def define_mock_behavior_for_find_element_by_id(self):
        """Defines the behavior for driver's find_element_by_id method."""
        # Create mock DOM elements that are returned by calls to
        # find_element_by_id.
        self.mock_elements_by_id = {
            'lrfactory-internetspeed__test_button': mock.Mock(),
            'lrfactory-internetspeed__latency': mock.Mock(),
        }
        self.mock_driver.find_element_by_id.side_effect = (
            lambda id: self.mock_elements_by_id[id])

    def define_mock_behavior_for_find_element_by_xpath(self):
        """Defines the behavior for driver's find_element_by_xpath method."""
        self.mock_elements_by_xpath = {
            '//div[@id="lrfactory-internetspeed__latency"]/*[2]':
            mock.Mock(text='1.23 ms'),
            '//div[@id="lrfactory-internetspeed__download"]/*[1]':
            mock.Mock(text='4.56'),
            '//div[@id="lrfactory-internetspeed__upload"]/*[1]':
            mock.Mock(text='7.89'),
        }
        self.mock_driver.find_element_by_xpath.side_effect = (
            lambda xpath: self.mock_elements_by_xpath[xpath])

    def apply_patches_for_wait_until_element_is_visible(self):
        """Set up patches for wait_until_element_is_visible."""
        wait_until_visible_patcher = mock.patch.object(
            banjo_driver.browser_client_common, 'wait_until_element_is_visible')
        self.addCleanup(wait_until_visible_patcher.stop)
        wait_until_visible_patcher.start()
        banjo_driver.browser_client_common.wait_until_element_is_visible.return_value = (
            True)

    def apply_patches_for_waiting_on_status_banner_text(self):
        """Set up the patches related to waiting for status banner text."""
        # Patch out the call to WebDriverWait so that it does nothing.
        webdriver_wait_patcher = mock.patch.object(banjo_driver.ui,
                                                   'WebDriverWait')
        self.addCleanup(webdriver_wait_patcher.stop)
        webdriver_wait_patcher.start()

        # Patch the text_to_be_present_in_element function so we can throw
        # exceptions to simulate timeouts. Note that the proper place to
        # simulate timeouts would probably be in WebDriverWait, but it's easier
        # to do here because this allows us better control on the basis of text
        # to wait on.
        text_to_be_present_patcher = mock.patch.object(
            banjo_driver.expected_conditions, 'text_to_be_present_in_element')
        self.addCleanup(text_to_be_present_patcher.stop)
        text_to_be_present_patcher.start()

        # A dictionary of elements to trigger timeout exceptions based on
        # what text the caller is waiting for. A value of False means throw no
        # exception (simulate a successful wait), True means throw a timeout
        # exception (simulate a failed wait).
        self.timeout_by_text = {
            'Testing download...': False,
            'Waiting for upload to start...': False,
            'Testing upload...': False,
        }

        def mock_text_to_be_present_in_element(_, text):
            if self.timeout_by_text[text]:
                raise exceptions.TimeoutException('mock timeout')

        banjo_driver.expected_conditions.text_to_be_present_in_element.side_effect = (
            mock_text_to_be_present_in_element)

    def test_test_yields_valid_results_when_all_page_elements_are_expected_values(
            self):
        result = self.banjo.perform_test()

        self.assertEqual(1.23, result.latency)
        self.assertEqual(4.56, result.s2c_result.throughput)
        self.assertEqual(7.89, result.c2s_result.throughput)
        self.assertErrorMessagesEqual([], result.errors)

    def test_test_records_error_when_url_does_not_load(self):
        """If the URL fails to load, return a valid NdtResult with an error."""

        # Create a mock implementation of load_url that always fails and appends
        # an error to the error list.
        def mock_load_url(unused_driver, unused_url, errors):
            errors.append(results.TestError('mock url load error'))
            return False

        with mock.patch.object(banjo_driver.browser_client_common,
                               'load_url') as load_url_patch:
            load_url_patch.side_effect = mock_load_url

            result = self.banjo.perform_test()

            self.assertErrorMessagesEqual(
                ['mock url load error'], result.errors)

            # No other result fields should be populated.
            self.assertIsNone(result.latency)
            self.assertIsNone(result.s2c_result.throughput)
            self.assertIsNone(result.c2s_result.throughput)

    @mock.patch.object(banjo_driver, 'ui')
    def test_test_records_error_when_run_test_button_is_not_in_dom(self,
                                                                   mock_ui):
        mock_wait_driver = mock.Mock()
        mock_wait_driver.until.side_effect = exceptions.TimeoutException(
            'mock_timeout')
        mock_ui.WebDriverWait.return_value = mock_wait_driver

        result = self.banjo.perform_test()

        self.assertIsNone(result.latency)
        self.assertIsNone(result.s2c_result.throughput)
        self.assertIsNone(result.c2s_result.throughput)
        self.assertErrorMessagesEqual(
            [banjo_driver.ERROR_FAILED_TO_LOCATE_RUN_TEST_BUTTON],
            result.errors)

    def test_driver_adds_errors_if_every_wait_event_times_out(self):
        """If each test times out, expect an error for each timeout."""
        self.timeout_by_text['Testing download...'] = True
        self.timeout_by_text['Waiting for upload to start...'] = True
        self.timeout_by_text['Testing upload...'] = True
        # Simulate a timeout when waiting for the "latency" field (which we use
        # as a proxy for the results view).
        banjo_driver.browser_client_common.wait_until_element_is_visible.return_value = (
            False)

        result = self.banjo.perform_test()

        self.assertErrorMessagesEqual(
            [browser_client_common.ERROR_S2C_NEVER_STARTED,
             browser_client_common.ERROR_S2C_NEVER_ENDED,
             browser_client_common.ERROR_C2S_NEVER_STARTED,
             browser_client_common.ERROR_C2S_NEVER_ENDED], result.errors)

    def test_download_start_timeout_yields_errors(self):
        """If waiting for download start times out, expect just one error."""
        self.timeout_by_text['Testing download...'] = True

        result = self.banjo.perform_test()

        self.assertErrorMessagesEqual(
            [browser_client_common.ERROR_S2C_NEVER_STARTED], result.errors)

    def test_driver_records_event_times_correctly(self):
        # Create a list of mock times to be returned by datetime.now().
        times = []
        for i in range(7):
            times.append(datetime.datetime(2016, 1, 1, 0, 0, i))

        with mock.patch.object(banjo_driver.datetime,
                               'datetime',
                               autospec=True) as mocked_datetime:
            # Patch datetime.now to return the next mock time on every call to
            # now().
            mocked_datetime.now.side_effect = times

            # Modify the create_browser mock to increment the clock forward one
            # call so we can verify that the browser is created after
            # result.start_time.
            @contextlib.contextmanager
            def mock_create_browser(unused_browser_name):
                datetime.datetime.now(pytz.utc)
                yield self.mock_driver

            browser_client_common.create_browser.side_effect = (
                mock_create_browser)

            result = self.banjo.perform_test()

        # Verify the recorded times matches the expected sequence.
        self.assertEqual(times[0], result.start_time)
        # times[1] is the call from mock_create_browser.
        self.assertEqual(times[2], result.s2c_result.start_time)
        self.assertEqual(times[3], result.s2c_result.end_time)
        self.assertEqual(times[4], result.c2s_result.start_time)
        self.assertEqual(times[5], result.c2s_result.end_time)
        self.assertEqual(times[6], result.end_time)

    def test_errors_occur_when_results_page_displays_blank_latency(self):
        self.mock_elements_by_xpath[
            '//div[@id="lrfactory-internetspeed__latency"]/*[2]'] = mock.Mock(
                text='')
        result = self.banjo.perform_test()

        self.assertIsNone(result.latency)
        self.assertEqual(4.56, result.s2c_result.throughput)
        self.assertEqual(7.89, result.c2s_result.throughput)
        self.assertErrorMessagesEqual(
            ['Illegal value shown for latency: []'], result.errors)

    def test_errors_occur_when_results_page_displays_blank_download_throughput(
            self):
        self.mock_elements_by_xpath[
            '//div[@id="lrfactory-internetspeed__download"]/*[1]'] = mock.Mock(
                text='')

        result = self.banjo.perform_test()

        self.assertEqual(1.23, result.latency)
        self.assertIsNone(result.s2c_result.throughput)
        self.assertEqual(7.89, result.c2s_result.throughput)
        self.assertErrorMessagesEqual(
            ['Illegal value shown for s2c throughput: []'], result.errors)

    def test_errors_occur_when_results_page_displays_blank_upload_throughput(
            self):
        self.mock_elements_by_xpath[
            '//div[@id="lrfactory-internetspeed__upload"]/*[1]'] = mock.Mock(
                text='')

        result = self.banjo.perform_test()

        self.assertEqual(1.23, result.latency)
        self.assertEqual(4.56, result.s2c_result.throughput)
        self.assertIsNone(result.c2s_result.throughput)
        self.assertErrorMessagesEqual(
            ['Illegal value shown for c2s throughput: []'], result.errors)

    def test_errors_occur_when_results_page_displays_non_numeric_latency(self):
        self.mock_elements_by_xpath[
            '//div[@id="lrfactory-internetspeed__latency"]/*[2]'] = mock.Mock(
                text='banana ms')
        result = self.banjo.perform_test()

        self.assertIsNone(result.latency)
        self.assertEqual(4.56, result.s2c_result.throughput)
        self.assertEqual(7.89, result.c2s_result.throughput)
        self.assertErrorMessagesEqual(
            ['Illegal value shown for latency: [banana ms]'], result.errors)

    def test_errors_occur_when_results_page_displays_non_numeric_download_throughput(
            self):
        self.mock_elements_by_xpath[
            '//div[@id="lrfactory-internetspeed__download"]/*[1]'] = mock.Mock(
                text='banana')

        result = self.banjo.perform_test()

        self.assertEqual(1.23, result.latency)
        self.assertIsNone(result.s2c_result.throughput)
        self.assertEqual(7.89, result.c2s_result.throughput)
        self.assertErrorMessagesEqual(
            ['Illegal value shown for s2c throughput: [banana]'], result.errors)

    def test_errors_occur_when_results_page_displays_non_numeric_upload_throughput(
            self):
        self.mock_elements_by_xpath[
            '//div[@id="lrfactory-internetspeed__upload"]/*[1]'] = mock.Mock(
                text='banana')

        result = self.banjo.perform_test()

        self.assertEqual(1.23, result.latency)
        self.assertEqual(4.56, result.s2c_result.throughput)
        self.assertIsNone(result.c2s_result.throughput)
        self.assertErrorMessagesEqual(
            ['Illegal value shown for c2s throughput: [banana]'], result.errors)

    def test_errors_occur_when_results_page_displays_all_non_numeric_metrics(
            self):
        """A results page with non-numeric metrics results in error list errors.

        When latency, c2s_throughput, and s2c_throughput are all non-numeric values,
        corresponding error objects are added to the errors list that indicate
        that each of these values is invalid.
        """
        self.mock_elements_by_xpath[
            '//div[@id="lrfactory-internetspeed__latency"]/*[2]'] = mock.Mock(
                text='apple')
        self.mock_elements_by_xpath[
            '//div[@id="lrfactory-internetspeed__download"]/*[1]'] = mock.Mock(
                text='banana')
        self.mock_elements_by_xpath[
            '//div[@id="lrfactory-internetspeed__upload"]/*[1]'] = mock.Mock(
                text='cherry')

        result = self.banjo.perform_test()

        self.assertIsNone(result.latency)
        self.assertIsNone(result.s2c_result.throughput)
        self.assertIsNone(result.c2s_result.throughput)
        self.assertErrorMessagesEqual(
            ['Illegal value shown for latency: [apple]',
             'Illegal value shown for s2c throughput: [banana]',
             'Illegal value shown for c2s throughput: [cherry]'], result.errors)

    def test_records_error_when_latency_element_is_not_in_dom(self):
        self.mock_elements_by_xpath[
            '//div[@id="lrfactory-internetspeed__latency"]/*[2]'] = None

        result = self.banjo.perform_test()

        self.assertIsNone(result.latency)
        self.assertErrorMessagesEqual(
            [banjo_driver.ERROR_NO_LATENCY_FIELD], result.errors)

    def test_records_error_when_download_element_is_not_in_dom(self):
        self.mock_elements_by_xpath[
            '//div[@id="lrfactory-internetspeed__download"]/*[1]'] = None

        result = self.banjo.perform_test()

        self.assertIsNone(result.s2c_result.throughput)
        self.assertErrorMessagesEqual(
            [banjo_driver.ERROR_NO_S2C_FIELD], result.errors)

    def test_records_error_when_upload_element_is_not_in_dom(self):
        self.mock_elements_by_xpath[
            '//div[@id="lrfactory-internetspeed__upload"]/*[1]'] = None

        result = self.banjo.perform_test()

        self.assertIsNone(result.c2s_result.throughput)
        self.assertErrorMessagesEqual(
            [banjo_driver.ERROR_NO_C2S_FIELD], result.errors)


if __name__ == '__main__':
    unittest.main()
