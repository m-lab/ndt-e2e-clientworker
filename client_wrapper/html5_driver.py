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
import contextlib
import datetime

import pytz
from selenium import webdriver
from selenium.webdriver.support import ui
from selenium.webdriver.support import expected_conditions
from selenium.common import exceptions

import names
import results

# TODO(mtlynch): Define all error strings as public constants so we're not
# duplicating strings between production code and unit test code.
ERROR_C2S_NEVER_STARTED = 'Timed out waiting for c2s test to begin.'
ERROR_S2C_NEVER_STARTED = 'Timed out waiting for c2s test to begin.'
ERROR_S2C_NEVER_ENDED = 'Timed out waiting for c2s test to end.'


class NdtHtml5SeleniumDriver(object):

    def __init__(self, browser, url, timeout):
        """Creates a NDT HTML5 client driver for the given URL and browser.

        Args:
            url: The URL of an NDT server to test against.
            browser: Can be one of 'firefox', 'chrome', 'edge', or 'safari'.
            timeout: The number of seconds that the driver will wait for each
                element to become visible before timing out.
        """
        self._browser = browser
        self._url = url
        self._timeout = timeout

    def perform_test(self):
        """Performs a full NDT test (both s2c and c2s) with the HTML5 client.

        Returns:
            A populated NdtResult object.
        """
        result = results.NdtResult(start_time=None, end_time=None, errors=[])
        result.client = names.NDT_HTML5
        result.start_time = datetime.datetime.now(pytz.utc)

        with contextlib.closing(_create_browser(self._browser)) as driver:
            result.browser = self._browser
            result.browser_version = driver.capabilities['version']

            _complete_ui_flow(driver, self._url, self._timeout, result)

        result.end_time = datetime.datetime.now(pytz.utc)
        return result


def _create_browser(browser):
    """Creates browser for an NDT test.

    Args:
        browser: Can be one of 'firefox', 'chrome', 'edge', or 'safari'

    Returns:
        An instance of a Selenium webdriver browser class corresponding to
        the specified browser.
    """
    if browser == names.FIREFOX:
        return webdriver.Firefox()
    elif browser == names.CHROME:
        return webdriver.Chrome()
    elif browser == names.EDGE:
        return webdriver.Edge()
    elif browser == names.SAFARI:
        return webdriver.Safari()
    raise ValueError('Invalid browser specified: %s' % browser)


def _load_url(driver, url, result):
    """Loads the URL in a Selenium driver for an NDT test.

    Args:
        driver: An instance of a Selenium webdriver.
        url: The The URL of an NDT server to test against.
        result: An instance of NdtResult.

    Returns:
        True if loading the URL was successful, False if otherwise.
    """
    try:
        driver.get(url)
    except exceptions.WebDriverException:
        result.errors.append(results.TestError('Failed to load test UI.'))
        return False
    return True


def _complete_ui_flow(driver, url, timeout, result):
    """Performs the UI flow for the NDT HTML5 test and records results.

    Args:
        driver: An instance of a Selenium webdriver browser class.
        url: URL to load to start the UI flow.
        timeout: Maximum time (in seconds) to wait for any element to appear in
            the flow.
        result: NdtResult instance to populate with results from proceeding
            through the UI flow.
    """
    if not _load_url(driver, url, result):

        return

    _click_start_button(driver)
    result.c2s_result = results.NdtSingleTestResult()
    result.s2c_result = results.NdtSingleTestResult()

    if _wait_for_c2s_test_to_start(driver, timeout):
        result.c2s_result.start_time = datetime.datetime.now(pytz.utc)
    else:
        result.errors.append(results.TestError(ERROR_C2S_NEVER_STARTED))

    if _wait_for_s2c_test_to_start(driver, timeout):
        result.c2s_result.end_time = datetime.datetime.now(pytz.utc)
        result.s2c_result.start_time = datetime.datetime.now(pytz.utc)
    else:
        result.errors.append(results.TestError(ERROR_S2C_NEVER_STARTED))

    if _wait_for_results_page_to_appear(driver, timeout):
        result.s2c_result.end_time = datetime.datetime.now(pytz.utc)
    else:
        result.errors.append(results.TestError(ERROR_S2C_NEVER_ENDED))

    _populate_metric_values(result, driver)


def _click_start_button(driver):
    """Clicks the "Start Test" button in the web UI.

    Args:
        driver: An instance of a Selenium webdriver browser class.
    """
    driver.find_element_by_id('websocketButton').click()

    start_button = driver.find_elements_by_xpath(
        "//*[contains(text(), 'Start Test')]")[0]
    start_button.click()


def _wait_for_c2s_test_to_start(driver, timeout):
    # Wait until the 'Now Testing your upload speed' banner is displayed.
    upload_speed_text = driver.find_elements_by_xpath(
        "//*[contains(text(), 'your upload speed')]")[0]
    return _wait_until_element_is_visible(driver, upload_speed_text, timeout)


def _wait_for_s2c_test_to_start(driver, timeout):
    # Wait until the 'Now Testing your download speed' banner is displayed.
    download_speed_text = driver.find_elements_by_xpath(
        "//*[contains(text(), 'your download speed')]")[0]
    return _wait_until_element_is_visible(driver, download_speed_text, timeout)


def _wait_for_results_page_to_appear(driver, timeout):
    results_text = driver.find_element_by_id('results')
    return _wait_until_element_is_visible(driver, results_text, timeout)


def _wait_until_element_is_visible(driver, element, timeout):
    """Waits until a DOM element is visible within a given timeout.

    Args:
        driver: An instance of a Selenium webdriver browser class.
        element: A selenium webdriver element.
        timeout: The maximum time to wait (in seconds).

    Returns:
        True if the element became visible within the timeout.
    """
    try:
        ui.WebDriverWait(
            driver,
            timeout=timeout).until(expected_conditions.visibility_of(element))
    except exceptions.TimeoutException:
        return False
    return True


def _populate_metric_values(result, driver):
    """Populates NdtResult with metrics from page, checks values are valid.

    Populates the NdtResult instance with metrics from the NDT test page. Checks
    that the values for upload (c2s) throughput, download (s2c) throughput, and
    latency within the NdtResult instance dict are valid.

    Args:
        result: An instance of NdtResult.
        driver: An instance of a Selenium webdriver browser class.
    """
    c2s_throughput = driver.find_element_by_id('upload-speed').text
    c2s_throughput_units = driver.find_element_by_id('upload-speed-units').text

    result.c2s_result.throughput = _parse_throughput(
        result.errors, c2s_throughput, c2s_throughput_units, 'c2s throughput')

    s2c_throughput = driver.find_element_by_id('download-speed').text

    s2c_throughput_units = driver.find_element_by_id(
        'download-speed-units').text
    result.s2c_result.throughput = _parse_throughput(
        result.errors, s2c_throughput, s2c_throughput_units, 's2c throughput')

    result.latency = driver.find_element_by_id('latency').text
    result.latency = _validate_metric(result.errors, result.latency, 'latency')


def _parse_throughput(errors, throughput, throughput_units,
                      throughput_metric_name):
    """Converts metric into a valid numeric value in Mb/s .

    For a given metric, checks that it is a valid numeric value. If not, an
    error is added to the list contained in the NdtResult instance attribute.
    If it is, it is converted into Mb/s where necessary.

    Args:
        errors: An errors list.
        throughput: The throughput value that is to be evaluated.
        throughput_units: The units for the throughput value that is to be
        evaluated (one of kb/s, Mb/s, Gb/s).
        throughput_metric_name: A string representing the name of the throughput
        metric to validate.

    Returns:
        float representing the converted metric, None if an illegal value
            is given.
    """
    if _convert_metric_to_float(errors, throughput, throughput_metric_name):
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
            errors.append(results.TestError(
                'Invalid throughput unit specified: %s' % throughput_units))
    return None


def _convert_metric_to_float(errors, metric, metric_name):
    """Converts a given metric to a float, otherwise, adds an error object.

    If a given metric can be converted to a float, it is converted. Otherwise,
    a TestError object is added to errors.

    Args:
        errors: An errors list.
        metric: The value of the metric that is to be evaluated.
        metric_name: A string representing the name of the metric to validate.

    Returns:
        True if the validation was successful.
    """

    try:
        float(metric)
    except ValueError:
        errors.append(results.TestError('illegal value shown for %s: %s' % (
            metric_name, metric)))
        return False
    return True


def _validate_metric(errors, metric, metric_name):
    """Checks whether a given metric is a valid numeric value.

    For a given metric, checks that it is a valid numeric value. If not, an
    error is added to the list contained in the NdtResult instance attribute.

    Args:
        errors: An errors list.
        metric: The value of the metric that is to be evaluated.
        metric_name: A string representing the name of the metric to validate.

    Returns:
        A float if the metric was validated, otherwise, returns None.
    """
    if _convert_metric_to_float(errors, metric, metric_name):
        return float(metric)
    return None
