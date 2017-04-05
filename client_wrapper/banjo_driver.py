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
from selenium.webdriver.support import ui
from selenium.webdriver.support import expected_conditions
from selenium.common import exceptions
from selenium.webdriver.common import by

import browser_client_common
import names
import results
import time

logger = logging.getLogger(__name__)

ERROR_FAILED_TO_LOCATE_RUN_TEST_BUTTON = (
    'Failed to locate "Run Speed Test" button.')
# TODO(mtlynch): Refactor the following errors into browser_client_common so that
# banjo_driver and html5_driver use the same error strings.
ERROR_NO_LATENCY_FIELD = 'Could not find latency field.'
ERROR_NO_S2C_FIELD = 'Could not find s2c throughput field.'
ERROR_NO_C2S_FIELD = 'Could not find c2s throughput field.'
ERROR_FORMAT_ILLEGAL_LATENCY = 'Illegal value shown for latency: [%s]'
ERROR_FORMAT_ILLEGAL_S2C_THROUGHPUT = (
    'Illegal value shown for s2c throughput: [%s]')
ERROR_FORMAT_ILLEGAL_C2S_THROUGHPUT = (
    'Illegal value shown for c2s throughput: [%s]')


class BanjoDriver(object):

    def __init__(self, browser, url):
        """Creates a Banjo client driver for the given URL and browser.

        Args:
            url: The URL of an NDT server to test against.
            browser: Can be one of 'firefox', 'chrome', 'edge', or 'safari'.
        """
        self._browser = browser
        self._url = url

    def perform_test(self):
        """Performs a full NDT test (both s2c and c2s) with the Banjo client.

        Returns:
            A populated NdtResult object.
        """
        result = results.NdtResult(client=names.BANJO,
                                   start_time=datetime.datetime.now(pytz.utc))

        logger.info('starting banjo test')
        with browser_client_common.create_browser(self._browser) as driver:
            result.browser = self._browser
            result.browser_version = browser_client_common.get_browser_version(
                driver)

            logger.info('loading URL: %s', self._url)
            if browser_client_common.load_url(driver, self._url, result.errors):
                logger.info('page loaded, starting UI flow')
                _BanjoUiFlowWrapper(driver, self._url,
                                    result).complete_ui_flow()

        result.end_time = datetime.datetime.now(pytz.utc)
        logger.info('banjo test ended')
        return result


class _BanjoUiFlowWrapper(object):

    def __init__(self, driver, url, result):
        """Performs the UI flow for the Banjo client test and records results.

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
        if not self._click_run_test_button():
            return
        logger.info('clicked "Run Test" button')
        self._record_event_times()
        self._parse_results_page()

    def _record_event_times(self):
        if self._wait_for_download_test_to_start():
            self._result.s2c_result.start_time = datetime.datetime.now(pytz.utc)
            logger.info('s2c test started')
        else:
            self._add_test_error(browser_client_common.ERROR_S2C_NEVER_STARTED)

        if self._wait_for_download_test_to_end():
            self._result.s2c_result.end_time = datetime.datetime.now(pytz.utc)
            logger.info('s2c test finished')
        else:
            self._add_test_error(browser_client_common.ERROR_S2C_NEVER_ENDED)

        if self._wait_for_upload_test_to_start():
            self._result.c2s_result.start_time = datetime.datetime.now(pytz.utc)
            logger.info('c2s test started')
        else:
            self._add_test_error(browser_client_common.ERROR_C2S_NEVER_STARTED)

        # When the latency field becomes visible in the web UI, the C2S test is
        # complete.
        if self._wait_for_upload_test_to_end():
            self._result.c2s_result.end_time = datetime.datetime.now(pytz.utc)
            logger.info('c2s test ended')
        else:
            self._add_test_error(browser_client_common.ERROR_C2S_NEVER_ENDED)

    def _parse_results_page(self):
        latency = self._parse_latency()
        if latency is not None:
            self._result.latency = latency

        download_throughput = self._parse_download_throughput()
        if download_throughput is not None:
            self._result.s2c_result.throughput = download_throughput

        upload_throughput = self._parse_upload_throughput()
        if upload_throughput is not None:
            self._result.c2s_result.throughput = upload_throughput

    def _click_run_test_button(self):
        wait = ui.WebDriverWait(self._driver,
                                browser_client_common.UI_WAIT_TIMEOUT)
        try:
            # Apparently checks for an element's visibility are broken in Safari 10.
            # For addtional (though not much) information, see:
            # http://stackoverflow.com/questions/40635371/selenium-3-0-1-with-safaridriver-failing-on-waitforelementvisible
            # https://groups.google.com/forum/#!msg/selenium-users/xEGcK92rzVg/IboybWUPAAAJ
            #
            # To get around this for now, check the browser name and version (WebKit
            # version , really), and if they seem to indicate Safari 10, then do a
            # dumb wait of 10 seconds to give the page time to render and the
            # elements to become visible, etc.
            if (self._result.browser == 'safari' and
                    self._result.browser_version ==
                    browser_client_common.SAFARI10_VERSION):
                time.sleep(10)
                start_button = self._driver.find_element_by_id(
                    'lrfactory-internetspeed__test_button')
            else:
                start_button = wait.until(
                    expected_conditions.element_to_be_clickable((
                        by.By.ID, 'lrfactory-internetspeed__test_button')))

        except exceptions.TimeoutException:
            self._add_test_error(ERROR_FAILED_TO_LOCATE_RUN_TEST_BUTTON)
            return False

        start_button.click()
        return True

    def _wait_for_download_test_to_start(self):
        return self._wait_for_status_banner_text(
            'Testing download...',
            browser_client_common.NDT_TEST_NEGOTIATION_TIMEOUT)

    def _wait_for_download_test_to_end(self):
        return self._wait_for_status_banner_text(
            'Waiting for upload to start...',
            browser_client_common.NDT_TEST_RUN_TIMEOUT)

    def _wait_for_upload_test_to_start(self):
        return self._wait_for_status_banner_text(
            'Testing upload...',
            browser_client_common.NDT_TEST_NEGOTIATION_TIMEOUT)

    def _wait_for_upload_test_to_end(self):
        # The appearance of the latency field in the results page indicates that
        # the test is complete.
        return browser_client_common.wait_until_element_is_visible(
            self._driver,
            self._driver.find_element_by_id('lrfactory-internetspeed__latency'),
            browser_client_common.NDT_TEST_RUN_TIMEOUT)

    def _wait_for_status_banner_text(self, status_text, timeout):
        """Wait until specified text appears in the status banner of the web UI.

        Args:
            status_text: The text in the web UI banner for which to wait.
            timeout: Amount of time (in seconds) to wait for specified text.

        Returns:
            True if the status banner displayed the specified within the
            timeout period.
        """
        try:
            ui.WebDriverWait(self._driver, timeout).until(
                expected_conditions.text_to_be_present_in_element((
                    by.By.CLASS_NAME,
                    'lrfactory-internetspeed__status-indicator'), status_text))
        except exceptions.TimeoutException:
            return False
        return True

    def _parse_latency(self):
        """Parses the latency field of the results page.

        Finds the latency field in the results page DOM and parses the value.
        The human-readable "latency" label is actually on the parent element of
        the latency field, so we create an XPath to find the parent element by
        ID, then parse the value from the parent element's second child tag.

        Returns:
            The parsed latency value (as a float, in milliseconds) if the
            latency field was found and in valid format, or None if the latency
            field could not be parsed.
        """
        latency_element = self._driver.find_element_by_xpath(
            '//div[@id="lrfactory-internetspeed__latency"]/*[2]')
        if not latency_element:
            self._add_test_error(ERROR_NO_LATENCY_FIELD)
            return None
        # The latency is stored as "[value] ms" like "12 ms" so we split the
        # string and use the numeric portion.
        latency_text = latency_element.text
        if not latency_text:
            self._add_test_error(ERROR_FORMAT_ILLEGAL_LATENCY %
                                 latency_element.text)
            return None
        latency_value_parts = latency_text.split()
        latency_value = latency_value_parts[0]
        try:
            return float(latency_value)
        except ValueError:
            self._add_test_error(ERROR_FORMAT_ILLEGAL_LATENCY %
                                 latency_element.text)
            return None

    def _parse_download_throughput(self):
        """Parses the download throughput field of the results page.

        Finds the download throughput field in the results page DOM and parses
        the value. The human-readable "download" element ID is actually on the
        parent element of the download throughput field, so we create an XPath
        to find the parent element by ID, then parse the value from the parent's
        first child.

        Returns:
            The parsed download throughput value (as a float, in Mbps) if the
            download throughput field was found and in valid format, or None if
            the download throughput field could not be parsed.
        """
        throughput = self._driver.find_element_by_xpath(
            '//div[@id="lrfactory-internetspeed__download"]/*[1]')
        if not throughput:
            self._add_test_error(ERROR_NO_S2C_FIELD)
            return None
        try:
            return float(throughput.text)
        except ValueError:
            self._add_test_error(ERROR_FORMAT_ILLEGAL_S2C_THROUGHPUT %
                                 throughput.text)
            return None

    def _parse_upload_throughput(self):
        """Parses the upload throughput field of the results page.

        Finds the upload throughput field in the results page DOM and parses the
        value. The human-readable "upload" element ID is actually on the parent
        element of the upload throughput field, so we create an XPath to find
        the parent element by ID, then parse the value from the parent's first
        child.

        Returns:
            The parsed upload throughput value (as a float, in Mbps) if the
            upload throughput field was found and in valid format, or None if
            the upload throughput field could not be parsed.
        """
        throughput = self._driver.find_element_by_xpath(
            '//div[@id="lrfactory-internetspeed__upload"]/*[1]')
        if not throughput:
            self._add_test_error(ERROR_NO_C2S_FIELD)
            return None
        try:
            return float(throughput.text)
        except ValueError:
            self._add_test_error(ERROR_FORMAT_ILLEGAL_C2S_THROUGHPUT %
                                 throughput.text)
            return None

    def _add_test_error(self, error_message):
        self._result.errors.append(results.TestError(error_message))
        logger.error(error_message)
