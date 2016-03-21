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
from client_wrapper import client_wrapper


class ClientWrapperTest(unittest.TestCase):

    def test_results_page_displays_non_numeric_metrics(self):
        '''
        When latency, upload_speed, and download_speed are
        non-numeric values, corresponding error objects are
        added to the errors list that indicates that the each
        of these values is invalid.
        '''
        with mock.patch(
                'client_wrapper.client_wrapper.NdtHtml5SeleniumDriver.set_test_browser',
                autospec=True) as mock_set_test_browser:
            # mock driver
            mock_set_test_browser.return_value = mock.MagicMock()

            # Set values read from page for latency, upload speed,
            # download speed
            mock_set_test_browser.return_value.find_element_by_id(
                'latency').text = 'Non numeric value'
            mock_set_test_browser.return_value.find_element_by_id(
                'upload_speed').text = 'Non numeric value'
            mock_set_test_browser.return_value.find_element_by_id(
                'download_speed').text = 'Non numeric value'

            # Mock visibility function so shows all elements are
            # always visible
            with mock.patch(
                    'selenium.webdriver.support.expected_conditions.visibility_of') as mock_visibility:
                mock_visibility = mock.Mock()
                mock_visibility.return_value = True

                selenium_driver = client_wrapper.NdtHtml5SeleniumDriver()
                test_results = selenium_driver.perform_test(
                    url=
                    'http://ndt.iupui.mlab4.nuq1t.measurement-lab.org:7123/',
                    browser='firefox',
                    timeout_time=1000)

                # And the appropriate error objects are contained in
                # the list
                self.assertEqual(
                    test_results.errors[0].message,
                    'illegal value shown for latency: Non numeric value')
                self.assertEqual(
                    test_results.errors[1].message,
                    'illegal value shown for download_speed: Non numeric value')
                self.assertEqual(
                    test_results.errors[2].message,
                    'illegal value shown for upload_speed: Non numeric value')

    def test_results_page_displays_numeric_latency(self):
        '''
        When latency is a numeric value, an error object is
        not added to the errors list.
        '''
        with mock.patch(
                'client_wrapper.client_wrapper.NdtHtml5SeleniumDriver.set_test_browser',
                autospec=True) as mock_set_test_browser:
            # mock driver
            mock_set_test_browser.return_value = mock.MagicMock()
            mock_set_test_browser.return_value.find_element_by_id(
                'latency').text = '72'
            with mock.patch(
                    'selenium.webdriver.support.expected_conditions.visibility_of') as mock_visibility:
                mock_visibility = mock.Mock()
                mock_visibility.return_value = True

                selenium_driver = client_wrapper.NdtHtml5SeleniumDriver()
                test_results = selenium_driver.perform_test(
                    url=
                    'http://ndt.iupui.mlab4.nuq1t.measurement-lab.org:7123/',
                    browser='firefox',
                    timeout_time=1000)
                # And an error object is not contained in the list
                self.assertEqual(len(test_results.errors), 0)

    def test_invalid_URL_throws_error(self):
        selenium_driver = client_wrapper.NdtHtml5SeleniumDriver()
        test_results = selenium_driver.perform_test(url='invalid_url',
                                                    browser='firefox')

        # We have one error
        self.assertEqual(len(test_results.errors), 1)

        # And that error is about the test results URL not being
        # well-formed
        self.assertEqual(test_results.errors[0].message,
                         u'Target URL invalid_url is not well-formed.')

    def test_timeout_throws_error(self):
        selenium_driver = client_wrapper.NdtHtml5SeleniumDriver()
        test_results = selenium_driver.perform_test(
            url='http://ndt.iupui.mlab4.nuq1t.measurement-lab.org:7123/',
            browser='firefox',
            timeout_time=1)

        # We have one error
        self.assertEqual(len(test_results.errors), 1)

        # And that is a timout error
        self.assertEqual(test_results.errors[0].message,
                         'Test did not complete within timeout period.')


if __name__ == '__main__':
    unittest.main()
