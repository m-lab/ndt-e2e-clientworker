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

from datetime import datetime
import pytz
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException


class TestError(object):
    '''Log message of an error encountered in the test.

    Attributes:
        timestamp: Datetime of when the error was observed
        message: String message describing the error.
    '''

    def __init__(self, timestamp, message):
        self.timestamp = timestamp
        self.message = message


class NdtResult(object):
    '''Represents the results of a complete NDT HTML5 client
    test.

    Attributes:
        start_time: The datetime at which tests were initiated
            (i.e. the time the driver pushed the 'Start Test' button).
        end_time: The datetime at which the tests completed (i.e. the time
            the results page loaded).
        c2s_start_time: The datetime when the c2s (upload) test began (
            or none if the test never began).
        s2c_start_time: The datetime when the s2c (download) test began (
            or None if the test never began).
        latency: The reported latency (in milliseconds)
        upload_speed: The reported upload speed (in kb/s)
        download_speed: The reported download speed (in kb/s)
        errors: a list of TestError objects representing any errors
            encountered during the tests (or an empty list if all
            tests were successful).
    '''

    def __init__(self,
                 start_time,
                 end_time,
                 c2s_start_time,
                 s2c_start_time,
                 errors,
                 latency=None,
                 upload_speed=None,
                 download_speed=None):
        self.start_time = start_time
        self.end_time = end_time
        self.c2s_start_time = c2s_start_time
        self.s2c_start_time = s2c_start_time
        self.errors = errors

        if latency:
            self.latency = latency
        if upload_speed:
            self.upload_speed = upload_speed
        if download_speed:
            self.download_speed = download_speed

    def __str__(self):
        return 'NDT Results:\n Start Time: %s,\n End Time: %s'\
        ',\n Latency: %s, \nErrors: %s' % (
            self.start_time, self.end_time, self.latency, self.errors)


class NdtHtml5SeleniumDriver(object):
    '''
    Attributes:
        result_values: A dictionary containing the results of
            an NDT test.
    '''

    def __init__(self):
        self.result_values = {'start_time': None,
                              'end_time': None,
                              'c2s_start_time': None,
                              's2c_start_time': None,
                              'errors': []}

    def set_test_browser(self, browser):
        '''
        Sets browser for an NDT test.

        Args:
            browser: Can be one of 'firefox', 'chrome', 'edge', or
                'safari'
        Returns: An instance of a Selenium webdriver browser class
            corresponding to the specified browser.
        '''
        if browser == 'firefox':
            return webdriver.Firefox()

    def check_result_metrics(self):
        '''
        Checks that the values for upload speed, download
        speed, and latency within the result_values dict are valid.
        '''
        self.test_indiv_metric_is_valid('latency')
        self.test_indiv_metric_is_valid('download_speed')
        self.test_indiv_metric_is_valid('upload_speed')

    def test_indiv_metric_is_valid(self, metric):
        '''
        For a given metric in result_values, checks that it is
        a valid numeric value. If not, an error is added to
        result_values' errors list.

        Args:
            metric: One of 'latency', 'download_speed', or
                'upload_speed'.
        '''
        try:
            float(self.result_values[metric])
        except ValueError:
            message = 'illegal value shown for ' + \
                metric + ': ' + str(self.result_values[metric])
            self.result_values['errors'].append(TestError(
                datetime.now(pytz.utc), message))

    def perform_test(self, url, browser, timeout_time=20):
        '''
        Performs an NDT test with the HTML5 client in the specified
        browser.

        Performs a full NDT test (both s2c and c2s) using the specified
        browser.

        Args:
            url: The URL of an NDT server to test against.
            browser: Can be one of 'firefox', 'chrome', 'edge', or
                'safari'.

        Returns:
            A populated NdtResult object
        '''
        self.driver = self.set_test_browser(browser)

        try:
            self.driver.get(url)
        except WebDriverException as e:
            if e.msg == u'Target URL invalid_url is not well-formed.':
                self.result_values['errors'].append(TestError(
                    datetime.now(pytz.utc), e.msg))
                self.driver.close()
                return NdtResult(**self.result_values)
        self.driver.find_element_by_id('websocketButton').click()

        start_button = self.driver.find_elements_by_xpath(
            "//*[contains(text(), 'Start Test')]")[0]
        start_button.click()
        self.result_values['start_time'] = datetime.now(pytz.utc)

        try:
            # wait until 'Now Testing your upload speed' is displayed
            upload_speed_text = self.driver.find_elements_by_xpath(
                "//*[contains(text(), 'your upload speed')]")[0]
            WebDriverWait(
                self.driver,
                timeout=timeout_time).until(EC.visibility_of(upload_speed_text))
            self.result_values['c2s_start_time'] = datetime.now(pytz.utc)

            # wait until 'Now Testing your download speed' is displayed
            download_speed_text = self.driver.find_elements_by_xpath(
                "//*[contains(text(), 'your download speed')]")[0]
            WebDriverWait(self.driver,
                          timeout=timeout_time).until(EC.visibility_of(
                              download_speed_text))
            self.result_values['s2c_start_time'] = datetime.now(pytz.utc)

            # wait until the results page appears
            results_text = self.driver.find_element_by_id('results')
            WebDriverWait(
                self.driver,
                timeout=timeout_time).until(EC.visibility_of(results_text))
            self.result_values['end_time'] = datetime.now(pytz.utc)

            # Find metric values
            self.result_values['upload_speed'] = self.driver.find_element_by_id(
                'upload-speed').text
            self.result_values[
                'download_speed'] = self.driver.find_element_by_id(
                    'download-speed').text
            self.result_values['latency'] = self.driver.find_element_by_id(
                'latency').text

        except TimeoutException as e:
            message = 'Test did not complete within timeout period.'
            self.result_values['errors'].append(TestError(
                datetime.now(pytz.utc), message))
            self.driver.close()
            return NdtResult(**self.result_values)

        self.check_result_metrics()

        self.driver.close()

        return NdtResult(**self.result_values)


def main():
    selenium_driver = NdtHtml5SeleniumDriver()
    test_results = selenium_driver.perform_test(
        url='http://ndt.iupui.mlab4.nuq1t.measurement-lab.org:7123/',
        browser='firefox')
    print(test_results)


if __name__ == '__main__':
    main()
