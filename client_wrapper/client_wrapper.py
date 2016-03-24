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

import contextlib
import datetime
import pytz
from selenium import webdriver
from selenium.webdriver.support import ui
from selenium.webdriver.support import expected_conditions as EC
from selenium.common import exceptions


class TestError(object):
    """Log message of an error encountered in the test.

    Attributes:
        timestamp: Datetime of when the error was observed
        message: String message describing the error.
    """

    def __init__(self, timestamp, message):
        self.timestamp = timestamp
        self.message = message


class NdtResult(object):
    """Represents the results of a complete NDT HTML5 client test.

    Attributes:
        start_time: The datetime at which tests were initiated (i.e. the time
            the driver pushed the 'Start Test' button).
        end_time: The datetime at which the tests completed (i.e. the time the
            results page loaded).
        c2s_start_time: The NdtSingleResult for the c2s (upload) test.
        s2c_start_time: The NdtSingleResult for the s2c (download) test.
        latency: The reported latency (in milliseconds).
        c2s_throughput: The reported upload (c2s) throughput (in kb/s).
        s2c_throughput: The reported download (s2c) throughput (in kb/s).
        errors: a list of TestError objects representing any errors encountered
            during the tests (or an empty list if all tests were successful).
    """

    def __init__(self,
                 start_time,
                 end_time,
                 c2s_start_time,
                 s2c_start_time,
                 errors,
                 latency=None,
                 c2s_throughput=None,
                 s2c_throughput=None):
        self.start_time = start_time
        self.end_time = end_time
        self.c2s_start_time = c2s_start_time
        self.s2c_start_time = s2c_start_time
        self.errors = errors
        self.latency = latency
        self.c2s_throughput = c2s_throughput
        self.s2c_throughput = s2c_throughput

    def __str__(self):
        return 'NDT Results:\n Start Time: %s,\n End Time: %s'\
        ',\n Latency: %s, \nErrors: %s' % (
            self.start_time, self.end_time, self.latency, self.errors)


class NdtHtml5SeleniumDriver(object):

    def perform_test(self, url, browser, timeout):
        """Performs an NDT test with the HTML5 client in the specified browser.

        Performs a full NDT test (both s2c and c2s) using the specified
        browser.

        Args:
            url: The URL of an NDT server to test against.
            browser: Can be one of 'firefox', 'chrome', 'edge', or 'safari'.
            timeout: The number of seconds that the driver will wait for
                each element to become visible before timing out.

        Returns:
            A populated NdtResult object.
        """
        result_values = {'start_time': None,
                          'end_time': None,
                          'c2s_start_time': None,
                          's2c_start_time': None,
                          'errors': []}
        with contextlib.closing(_create_browser(browser)) as driver:
            try:
                driver.get(url)
            except exceptions.WebDriverException:
                message = 'Failed to load test UI.'
                result_values['errors'].append(TestError(
                    datetime.datetime.now(pytz.utc), message))
                return NdtResult(**result_values)
            driver.find_element_by_id('websocketButton').click()

            start_button = driver.find_elements_by_xpath(
                "//*[contains(text(), 'Start Test')]")[0]
            start_button.click()
            result_values['start_time'] = datetime.datetime.now(pytz.utc)

            try:
                result_values = _record_test_in_progress_values(
                    result_values, driver, timeout)

                result_values = _populate_metric_values(result_values, driver)

            except exceptions.TimeoutException:
                message = 'Test did not complete within timeout period.'
                result_values['errors'].append(TestError(
                    datetime.datetime.now(pytz.utc), message))
                return NdtResult(**result_values)

            return NdtResult(**result_values)


def _create_browser(browser):
    """Creates browser for an NDT test.

    Args:
        browser: Can be one of 'firefox', 'chrome', 'edge', or 'safari'

    Returns: An instance of a Selenium webdriver browser class corresponding to
        the specified browser.
    """
    if browser == 'firefox':
        return webdriver.Firefox()
    if browser in ['chrome', 'edge', 'safari']:
        raise NotImplementedError
    raise ValueError('Invalid browser specified: %s' % browser)


def _record_test_in_progress_values(result_values, driver, timeout):
    """Records values that are measured while the NDT test is in progress.

    Measures s2c_start_time, c2s_end_time, and end_time, which are stored in
    result_values. These times are measured while the NDT test is in progress.

    Args:
        driver: An instance of a Selenium webdriver browser class.
        result_values: A dictionary that stores the results of the NDT test.
        timeout: The number of seconds that the driver will wait for
            each element to become visible before timing out.

    Returns:
        result_values
    """
    # wait until 'Now Testing your upload speed' is displayed
    upload_speed_text = driver.find_elements_by_xpath(
        "//*[contains(text(), 'your upload speed')]")[0]
    result_values['c2s_start_time'] = _record_time_when_element_displayed(
        upload_speed_text,
        driver,
        timeout=timeout)

    # wait until 'Now Testing your download speed' is displayed
    download_speed_text = driver.find_elements_by_xpath(
        "//*[contains(text(), 'your download speed')]")[0]
    result_values['s2c_start_time'] = _record_time_when_element_displayed(
        download_speed_text,
        driver,
        timeout=timeout)

    # wait until the results page appears
    results_text = driver.find_element_by_id('results')
    result_values['end_time'] = _record_time_when_element_displayed(
        results_text,
        driver,
        timeout=timeout)
    return result_values


def _record_time_when_element_displayed(element, driver, timeout):
    """Return the time when the specified element is displayed.

    The Selenium WebDriver checks whether the specified element is visible. If
    it becomes visible before the request has timed out, the timestamp of the
    time when the element becomes visible is returned.

    Args:
        element: A selenium webdriver element.
        timeout: The number of seconds that the driver will wait for
            each element to become visible before timing out.

    Returns: A datetime object with a timezone information attribute.

    Raises:
        TimeoutException: If the element does not become visible before the
            timeout time passes.
    """
    ui.WebDriverWait(driver, timeout=timeout).until(EC.visibility_of(element))
    return datetime.datetime.now(pytz.utc)


def _populate_metric_values(result_values, driver):
    """Populates result_values with metrics from page, checks values are valid.

    Populdates result_values with metrics from the NDT test page. Checks that
    the values for upload (c2s) throughput, download (s2c) throughput, and
    latency within the result_values dict are valid.

    Args:
        driver: An instance of a Selenium webdriver browser class.
        result_values:  A dictionary that stores the results of the NDT test.

    Returns:
        result_values
    """
    result_values['c2s_throughput'] = driver.find_element_by_id(
        'upload-speed').text
    result_values = _validate_metric(result_values,
                                                 'c2s_throughput')
    result_values['s2c_throughput'] = driver.find_element_by_id(
        'download-speed').text
    result_values = _validate_metric(result_values,
                                                 's2c_throughput')
    result_values['latency'] = driver.find_element_by_id('latency').text
    result_values = _validate_metric(result_values, 'latency')
    return result_values


def _validate_metric(result_values, metric):
    """Checks whether a given metric is a valid numeric value.

    For a given metric in result_values, checks that it is a valid numeric
    value. If not, an error is added to result_values' errors list.

    Args:
        result_values: A dictionary that stores the results of the NDT test.
        metric: The name of the metric to validate.

    Returns:
        A dictionary that stores the results of the NDT test.
    """
    try:
        float(result_values[metric])
    except ValueError:
        message = 'illegal value shown for ' + metric + ': ' + \
            str(result_values[metric])
        result_values['errors'].append(TestError(
            datetime.datetime.now(pytz.utc), message))
    return result_values


def main():
    selenium_driver = NdtHtml5SeleniumDriver()
    test_results = selenium_driver.perform_test(
        url='http://ndt.iupui.mlab4.nuq1t.measurement-lab.org:7123/',
        browser='firefox',
        timeout=20)
    print(test_results)


if __name__ == '__main__':
    main()
