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

from __future__ import division
import datetime
import logging

import pytz

import browser_client_common
import names
import results

logger = logging.getLogger(__name__)

# TODO(mtlynch): Define all error strings as public constants so we're not
# duplicating strings between production code and unit test code.
ERROR_C2S_NEVER_STARTED = 'Timed out waiting for c2s test to begin.'
ERROR_S2C_NEVER_STARTED = 'Timed out waiting for c2s test to begin.'
ERROR_S2C_NEVER_ENDED = 'Timed out waiting for c2s test to end.'
ERROR_START_BUTTON_NOT_IN_DOM = '"Start Test" button does not appear in DOM.'
ERROR_TIMED_OUT_WAITING_FOR_START_BUTTON = (
    'Timed out waiting for "Start Test" button to appear.')


class NdtHtml5SeleniumDriver(object):

    def __init__(self, browser, server_fqdn):
        """Creates a NDT HTML5 client driver for the given URL and browser.

        Args:
            browser: Can be one of 'firefox', 'chrome', 'edge', or 'safari'.
            server_fqdn: The URL of an NDT server to test against.
        """
        self._browser = browser
        self._server_fqdn = server_fqdn

    def perform_test(self):
        """Performs a full NDT test (both s2c and c2s) with the HTML5 client.

        Returns:
            A populated NdtResult object.
        """
        result = results.NdtResult()
        result.client = names.NDT_HTML5
        result.start_time = datetime.datetime.now(pytz.utc)

        logger.info('starting NDT HTML5 test')
        with browser_client_common.create_browser(self._browser) as driver:
            result.browser = self._browser
            result.browser_version = browser_client_common.get_browser_version(
                driver)

            # The NDT HTML5 client is hosted on a web server on port 7123 of the
            # NDT server.
            url = 'http://%s:7123' % self._server_fqdn
            logger.info('loading URL: %s', url)
            if not browser_client_common.load_url(driver, url, result.errors):
                return
            logger.info('page loaded, starting UI flow')
            _NdtHtml5UiFlowWrapper(driver, url, result).complete_ui_flow()

        result.end_time = datetime.datetime.now(pytz.utc)
        logger.info('NDT HTML5 test ended')
        return result


class _NdtHtml5UiFlowWrapper(object):

    def __init__(self, driver, url, result):
        """Performs the UI flow for the NDT HTML5 test and records results.

        Args:
            driver: An instance of a Selenium webdriver browser class.
            url: URL to load to start the UI flow.
            result: NdtResult instance to populate with results from proceeding
                through the UI flow.
        """
        self._driver = driver
        self._url = url
        self._result = result

    def complete_ui_flow(self):
        """Performs the UI flow for the NDT HTML5 test and records results."""
        self._click_websocket_button()
        # If we can't click the start button, nothing left to do, so bail out.
        if not self._click_start_button():
            return
        logger.info('clicked "Start Test" button')
        self._record_event_times()
        self._parse_results_page()

    def _click_websocket_button(self):
        # TODO(mtlynch): Handle case when element is not found.
        self._driver.find_element_by_id('websocketButton').click()

    def _click_start_button(self):
        """Clicks the "Start Test" button in the web UI.

        Returns:
            True if the "Start Test" button could be successfully located
            and clicked.
        """
        start_button = browser_client_common.find_element_containing_text(
            self._driver, 'Start Test')
        if not start_button:
            self._add_test_error(ERROR_START_BUTTON_NOT_IN_DOM)
            return False
        if not browser_client_common.wait_until_element_is_visible(
                self._driver, start_button,
                browser_client_common.UI_WAIT_TIMEOUT):
            self._add_test_error(ERROR_TIMED_OUT_WAITING_FOR_START_BUTTON)
            return False
        start_button.click()
        return True

    def _record_event_times(self):
        if self._wait_for_c2s_test_to_start():
            self._result.c2s_result.start_time = datetime.datetime.now(pytz.utc)
            logger.info('c2s test started')
        else:
            self._add_test_error(browser_client_common.ERROR_C2S_NEVER_STARTED)

        if self._wait_for_s2c_test_to_start():
            self._result.c2s_result.end_time = datetime.datetime.now(pytz.utc)
            logger.info('c2s test finished')
            self._result.s2c_result.start_time = datetime.datetime.now(pytz.utc)
            logger.info('s2c test started')
        else:
            self._add_test_error(browser_client_common.ERROR_S2C_NEVER_STARTED)

        if self._wait_for_results_page_to_appear():
            self._result.s2c_result.end_time = datetime.datetime.now(pytz.utc)
            logger.info('s2c test finished')
        else:
            self._add_test_error(browser_client_common.ERROR_S2C_NEVER_ENDED)

    def _wait_for_c2s_test_to_start(self):
        # Wait until the 'Now Testing your upload speed' banner is displayed.
        upload_speed_element = (
            browser_client_common.find_element_containing_text(
                self._driver, 'your upload speed'))
        return browser_client_common.wait_until_element_is_visible(
            self._driver, upload_speed_element,
            browser_client_common.NDT_TEST_NEGOTIATION_TIMEOUT)

    def _wait_for_s2c_test_to_start(self):
        # Wait until the 'Now Testing your download speed' banner is displayed.
        download_speed_element = (
            browser_client_common.find_element_containing_text(
                self._driver, 'your download speed'))
        return browser_client_common.wait_until_element_is_visible(
            self._driver, download_speed_element,
            browser_client_common.NDT_TEST_RUN_TIMEOUT)

    def _wait_for_results_page_to_appear(self):
        results_element = self._driver.find_element_by_id('results')
        return browser_client_common.wait_until_element_is_visible(
            self._driver, results_element,
            browser_client_common.NDT_TEST_RUN_TIMEOUT)

    def _parse_results_page(self):
        """Populates NdtResult with metrics from page, checks values are valid.

        Populates the NdtResult instance with metrics from the NDT test page.
        Checks that the values for upload (c2s) throughput, download (s2c)
        throughput, and latency within the NdtResult instance dict are valid.
        """
        c2s_throughput = self._driver.find_element_by_id('upload-speed').text
        c2s_throughput_units = self._driver.find_element_by_id(
            'upload-speed-units').text

        self._result.c2s_result.throughput = self._parse_throughput(
            c2s_throughput, c2s_throughput_units, 'c2s throughput')

        s2c_throughput = self._driver.find_element_by_id('download-speed').text

        s2c_throughput_units = self._driver.find_element_by_id(
            'download-speed-units').text
        self._result.s2c_result.throughput = self._parse_throughput(
            s2c_throughput, s2c_throughput_units, 's2c throughput')

        latency = self._driver.find_element_by_id('latency').text
        self._result.latency = self._validate_metric(latency, 'latency')

    def _parse_throughput(self, throughput, throughput_units,
                          throughput_metric_name):
        """Converts metric into a valid numeric value in Mb/s .

        For a given metric, checks that it is a valid numeric value. If not, an
        error is added to the list contained in the NdtResult instance
        attribute. If it is, it is converted into Mb/s where necessary.

        Args:
            throughput: The throughput value that is to be evaluated.
            throughput_units: The units for the throughput value that is to be
            evaluated (one of kb/s, Mb/s, Gb/s).
            throughput_metric_name: A string representing the name of the
                throughput metric to validate.

        Returns:
            float representing the converted metric, None if an illegal value
                is given.
        """
        if self._convert_metric_to_float(throughput, throughput_metric_name):
            throughput = float(throughput)
            if throughput_units == 'kb/s':
                converted_throughput = throughput / 1000
                return converted_throughput
            elif throughput_units == 'Gb/s':
                converted_throughput = throughput * 1000
                return converted_throughput
            elif throughput_units == 'Mb/s':
                return throughput
            else:
                self._add_test_error('Invalid throughput unit specified: %s' %
                                     throughput_units)
        return None

    def _convert_metric_to_float(self, metric, metric_name):
        """Converts a given metric to a float, otherwise, adds an error object.

        If a given metric can be converted to a float, it is converted.
        Otherwise, a TestError object is added to errors.

        Args:
            metric: The value of the metric that is to be evaluated.
            metric_name: A string representing the name of the metric to
                validate.

        Returns:
            True if the validation was successful.
        """
        try:
            float(metric)
        except ValueError:
            self._add_test_error('illegal value shown for %s: %s' %
                                 (metric_name, metric))
            return False
        return True

    def _validate_metric(self, metric, metric_name):
        """Checks whether a given metric is a valid numeric value.

        For a given metric, checks that it is a valid numeric value. If not, an
        error is added to the list contained in the NdtResult instance
        attribute.

        Args:
            metric: The value of the metric that is to be evaluated.
            metric_name: A string representing the name of the metric to
                validate.

        Returns:
            A float if the metric was validated, otherwise, returns None.
        """
        if self._convert_metric_to_float(metric, metric_name):
            return float(metric)
        return None

    def _add_test_error(self, error_message):
        self._result.errors.append(results.TestError(error_message))
        logger.error(error_message)
