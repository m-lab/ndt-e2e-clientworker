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
import datetime
import mock
import pytz
import freezegun
import selenium.webdriver.support.expected_conditions as selenium_expected_conditions
from selenium.common import exceptions
from client_wrapper import html5_driver


class NdtHtml5SeleniumDriverGeneralTest(unittest.TestCase):

    def setUp(self):
        self.mock_browser = mock.MagicMock()
        self.mock_driver = mock.patch.object(html5_driver.webdriver,
                                             'Firefox',
                                             autospec=True,
                                             return_value=self.mock_browser)
        self.addCleanup(self.mock_driver.stop)
        self.mock_driver.start()

        self.mock_visibility = mock.patch.object(selenium_expected_conditions,
                                                 'visibility_of',
                                                 autospec=True)
        self.addCleanup(self.mock_visibility.stop)
        self.mock_visibility.start()
        self.mock_visibility.return_value = True

    def test_invalid_URL_throws_error(self):
        self.mock_browser.get.side_effect = exceptions.WebDriverException(
            u'Failed to load test UI.')

        test_results = html5_driver.NdtHtml5SeleniumDriver(
            browser='firefox',
            url='invalid_url',
            timeout=1).perform_test()

        # We have one error
        self.assertEqual(len(test_results.errors), 1)

        # And that error is about test UI loading failure
        self.assertEqual(test_results.errors[0].message,
                         'Failed to load test UI.')

    def test_test_in_progress_timeout_throws_error(self):
        # Call to webdriverwait throws timeout exception
        with mock.patch.object(html5_driver.ui,
                               'WebDriverWait',
                               side_effect=exceptions.TimeoutException,
                               autospec=True):
            test_results = html5_driver.NdtHtml5SeleniumDriver(
                browser='firefox',
                url='http://ndt.mock-server.com:7123/',
                timeout=1).perform_test()

        # We have one error
        self.assertEqual(len(test_results.errors), 1)

        # And that is a timout error
        self.assertEqual(test_results.errors[0].message,
                         'Test did not complete within timeout period.')

    def test_unrecognized_browser_raises_error(self):
        selenium_driver = html5_driver.NdtHtml5SeleniumDriver(
            browser='not_a_browser',
            url='http://ndt.mock-server.com:7123',
            timeout=1)
        with self.assertRaises(ValueError):
            selenium_driver.perform_test()


class NdtHtml5SeleniumDriverCustomClassTest(unittest.TestCase):

    def setUp(self):
        self.mock_visibility = mock.patch.object(selenium_expected_conditions,
                                                 'visibility_of',
                                                 autospec=True)
        self.addCleanup(self.mock_visibility.stop)
        self.mock_visibility.return_value = True
        self.mock_visibility.start()

    def test_results_page_displays_non_numeric_latency(self):

        class NewDriver(object):

            def get(self, url):
                pass

            def close(self):
                pass

            def find_element_by_id(self, id):
                if id == 'upload-speed-units':
                    return mock.Mock(text='kb/s', autospec=True)
                elif id == 'download-speed-units':
                    return mock.Mock(text='Mb/s', autospec=True)
                elif id == 'latency':
                    return mock.Mock(text='Non-numeric value', autospec=True)
                else:
                    return mock.Mock(text='34', autospec=True)

            def find_elements_by_xpath(self, xpath):
                return [mock.Mock(autospec=True)]

        with mock.patch.object(html5_driver.webdriver,
                               'Firefox',
                               autospec=True,
                               return_value=NewDriver()):

            test_results = html5_driver.NdtHtml5SeleniumDriver(
                browser='firefox',
                url='http://ndt.mock-server.com:7123/',
                timeout=1000).perform_test()

        # And the appropriate error object is contained in the list
        self.assertEqual(len(test_results.errors), 1)
        self.assertEqual(test_results.errors[0].message,
                         'illegal value shown for latency: Non-numeric value')

    def test_results_page_displays_non_numeric_c2s_throughput(self):

        class NewDriver(object):

            def get(self, url):
                pass

            def close(self):
                pass

            def find_element_by_id(self, id):
                if id == 'upload-speed-units':
                    return mock.Mock(text='kb/s', autospec=True)
                elif id == 'download-speed-units':
                    return mock.Mock(text='Mb/s', autospec=True)
                elif id == 'upload-speed':
                    return mock.Mock(text='Non-numeric value', autospec=True)
                else:
                    return mock.Mock(text='34', autospec=True)

            def find_elements_by_xpath(self, xpath):
                return [mock.Mock(autospec=True)]

        with mock.patch.object(html5_driver.webdriver,
                               'Firefox',
                               autospec=True,
                               return_value=NewDriver()):

            test_results = html5_driver.NdtHtml5SeleniumDriver(
                browser='firefox',
                url='http://ndt.mock-server.com:7123/',
                timeout=1000).perform_test()

        # And only the appropriate error object is contained in the list
        self.assertEqual(len(test_results.errors), 1)
        self.assertEqual(
            test_results.errors[0].message,
            'illegal value shown for c2s throughput: Non-numeric value')

    def test_results_page_displays_non_numeric_s2c_throughput(self):

        class NewDriver(object):

            def get(self, url):
                pass

            def close(self):
                pass

            def find_element_by_id(self, id):
                if id == 'upload-speed-units':
                    return mock.Mock(text='kb/s', autospec=True)
                elif id == 'download-speed-units':
                    return mock.Mock(text='Mb/s', autospec=True)
                elif id == 'download-speed':
                    return mock.Mock(text='Non-numeric value', autospec=True)
                else:
                    return mock.Mock(text='34', autospec=True)

            def find_elements_by_xpath(self, xpath):
                return [mock.Mock(autospec=True)]

        with mock.patch.object(html5_driver.webdriver,
                               'Firefox',
                               autospec=True,
                               return_value=NewDriver()):

            test_results = html5_driver.NdtHtml5SeleniumDriver(
                browser='firefox',
                url='http://ndt.mock-server.com:7123/',
                timeout=1000).perform_test()

        # And only the appropriate error object is contained in the list
        self.assertEqual(len(test_results.errors), 1)
        self.assertEqual(
            test_results.errors[0].message,
            'illegal value shown for s2c throughput: Non-numeric value')

    def test_results_page_displays_non_numeric_metrics(self):
        """A results page with non-numeric metrics results in error list errors.

        When latency, c2s_throughput, and s2c_throughput are all non-numeric values,
        corresponding error objects are added to the errors list that indicate
        that each of these values is invalid.
        """

        # We patch selenium's web driver so it always has a non numeric
        # value as a WebElement.text attribute
        class NewWebElement(object):

            def __init__(self):
                self.text = 'Non numeric value'

            def click(self):
                pass

        class NewDriver(object):

            def get(self, url):
                pass

            def close(self):
                pass

            def find_element_by_id(self, id):
                return NewWebElement()

            def find_elements_by_xpath(self, xpath):
                return [NewWebElement()]

        with mock.patch.object(html5_driver.webdriver,
                               'Firefox',
                               autospec=True,
                               return_value=NewDriver()):

            test_results = html5_driver.NdtHtml5SeleniumDriver(
                browser='firefox',
                url='http://ndt.mock-server.com:7123/',
                timeout=1000).perform_test()

        # And the appropriate error objects are contained in
        # the list
        self.assertEqual(
            test_results.errors[0].message,
            'illegal value shown for c2s throughput: Non numeric value')
        self.assertEqual(
            test_results.errors[1].message,
            'illegal value shown for s2c throughput: Non numeric value')
        self.assertEqual(test_results.errors[2].message,
                         'illegal value shown for latency: Non numeric value')

    def test_results_page_displays_numeric_latency(self):
        """A valid (numeric) latency results in an empty errors list."""

        # Mock so always returns a numeric value for a WebElement.text attribute

        class NewDriver(object):

            def get(self, url):
                pass

            def close(self):
                pass

            def find_element_by_id(self, id):
                if id == 'download-speed-units':
                    return mock.Mock(text='Mb/s', autospec=True)
                elif id == 'upload-speed-units':
                    return mock.Mock(text='Mb/s', autospec=True)
                return mock.Mock(text='72', autospec=True)

            def find_elements_by_xpath(self, xpath):
                return [mock.Mock(autospec=True)]

        with mock.patch.object(html5_driver.webdriver,
                               'Firefox',
                               autospec=True,
                               return_value=NewDriver()):

            test_results = html5_driver.NdtHtml5SeleniumDriver(
                browser='firefox',
                url='http://ndt.mock-server.com:7123/',
                timeout=1000).perform_test()

        self.assertEqual(test_results.latency, 72.0)
        # And an error object is not contained in the list
        self.assertEqual(len(test_results.errors), 0)

    def test_s2c_gbps_speed_conversion(self):
        """Test s2c speed converts from Gb/s to Mb/s correctly."""

        # If s2c speed is 72 Gb/s and c2s is speed is 34 in the browser

        class NewDriver(object):

            def get(self, url):
                pass

            def close(self):
                pass

            def find_element_by_id(self, id):
                if id == 'download-speed-units':
                    return mock.Mock(text='Gb/s', autospec=True)
                elif id == 'download-speed':
                    return mock.Mock(text='72', autospec=True)
                elif id == 'upload-speed-units':
                    return mock.Mock(text='Mb/s', autospec=True)
                else:
                    return mock.Mock(text='34', autospec=True)

            def find_elements_by_xpath(self, xpath):
                return [mock.Mock(autospec=True)]

        with mock.patch.object(html5_driver.webdriver,
                               'Firefox',
                               autospec=True,
                               return_value=NewDriver()):

            test_results = html5_driver.NdtHtml5SeleniumDriver(
                browser='firefox',
                url='http://ndt.mock-server.com:7123/',
                timeout=1000).perform_test()

        # Then s2c is converted from Gb/s to Mb/s
        self.assertEqual(test_results.s2c_result.throughput, 72000)
        # And c2s is not
        self.assertEqual(test_results.c2s_result.throughput, 34)
        # And an error object is not contained in the list
        self.assertEqual(len(test_results.errors), 0)

    def test_invalid_throughput_unit_raises_error(self):

        class NewDriver(object):

            def get(self, url):
                pass

            def close(self):
                pass

            def find_element_by_id(self, id):
                if id == 'download-speed-units':
                    return mock.Mock(text='Gb/s', autospec=True)
                elif id == 'download-speed':
                    return mock.Mock(text='72', autospec=True)
                elif id == 'upload-speed-units':
                    return mock.Mock(text='not a unit', autospec=True)
                else:
                    return mock.Mock(text='34', autospec=True)

            def find_elements_by_xpath(self, xpath):
                return [mock.Mock(autospec=True)]

        with mock.patch.object(html5_driver.webdriver,
                               'Firefox',
                               autospec=True,
                               return_value=NewDriver()):

            # And a value error is raised because the c2s throughput
            # unit was invalid.
            with self.assertRaises(ValueError):
                html5_driver.NdtHtml5SeleniumDriver(
                    browser='firefox',
                    url='http://ndt.mock-server.com:7123/',
                    timeout=1000).perform_test()

    def test_reading_in_result_page_timeout_throws_error(self):

        # If a timeout exception occurs when the driver attempts to
        # read the metric page
        class NewDriver(object):

            def get(self, url):
                pass

            def close(self):
                pass

            def find_element_by_id(self, id):
                if id == 'upload-speed':
                    raise exceptions.TimeoutException
                else:
                    return mock.Mock(text='34', autospec=True)

            def find_elements_by_xpath(self, xpath):
                return [mock.Mock(autospec=True)]

        with mock.patch.object(html5_driver.webdriver,
                               'Firefox',
                               autospec=True,
                               return_value=NewDriver()):

            test_results = html5_driver.NdtHtml5SeleniumDriver(
                browser='firefox',
                url='http://ndt.mock-server.com:7123/',
                timeout=1000).perform_test()

        # The appropriate error object is contained in the list.
        self.assertEqual(test_results.errors[0].message,
                         'Test did not complete within timeout period.')

    def test_chrome_driver_can_be_used_for_test(self):

        class NewDriver(object):

            def get(self, url):
                pass

            def close(self):
                pass

            def find_elements_by_xpath(self, xpath):
                return [mock.Mock(autospec=True)]

            def find_element_by_id(self, id):
                if id == 'download-speed-units':
                    return mock.Mock(text='Gb/s', autospec=True)
                elif id == 'download-speed':
                    return mock.Mock(text='72', autospec=True)
                elif id == 'upload-speed-units':
                    return mock.Mock(text='Mb/s', autospec=True)
                else:
                    return mock.Mock(text='34', autospec=True)

        with mock.patch.object(html5_driver.webdriver,
                               'Chrome',
                               autospec=True,
                               return_value=NewDriver()):

            test_results = html5_driver.NdtHtml5SeleniumDriver(
                browser='chrome',
                url='http://ndt.mock-server.com:7123/',
                timeout=1000).perform_test()

        # Then s2c is converted from Gb/s to Mb/s
        self.assertEqual(test_results.s2c_result.throughput, 72000)
        # And c2s is not
        self.assertEqual(test_results.c2s_result.throughput, 34)
        # And an error object is not contained in the list
        self.assertEqual(len(test_results.errors), 0)

    def test_edge_driver_can_be_used_for_test(self):

        class NewDriver(object):

            def get(self, url):
                pass

            def close(self):
                pass

            def find_elements_by_xpath(self, xpath):
                return [mock.Mock(autospec=True)]

            def find_element_by_id(self, id):
                if id == 'download-speed-units':
                    return mock.Mock(text='Gb/s', autospec=True)
                elif id == 'download-speed':
                    return mock.Mock(text='72', autospec=True)
                elif id == 'upload-speed-units':
                    return mock.Mock(text='Mb/s', autospec=True)
                else:
                    return mock.Mock(text='34', autospec=True)

        with mock.patch.object(html5_driver.webdriver,
                               'Edge',
                               autospec=True,
                               return_value=NewDriver()):

            test_results = html5_driver.NdtHtml5SeleniumDriver(
                browser='edge',
                url='http://ndt.mock-server.com:7123/',
                timeout=1000).perform_test()

        # Then s2c is converted from Gb/s to Mb/s
        self.assertEqual(test_results.s2c_result.throughput, 72000)
        # And c2s is not
        self.assertEqual(test_results.c2s_result.throughput, 34)
        # And an error object is not contained in the list
        self.assertEqual(len(test_results.errors), 0)

    def test_safari_driver_can_be_used_for_test(self):

        class NewDriver(object):

            def get(self, url):
                pass

            def close(self):
                pass

            def find_elements_by_xpath(self, xpath):
                return [mock.Mock(autospec=True)]

            def find_element_by_id(self, id):
                if id == 'download-speed-units':
                    return mock.Mock(text='Gb/s', autospec=True)
                elif id == 'download-speed':
                    return mock.Mock(text='72', autospec=True)
                elif id == 'upload-speed-units':
                    return mock.Mock(text='Mb/s', autospec=True)
                else:
                    return mock.Mock(text='34', autospec=True)

        with mock.patch.object(html5_driver.webdriver,
                               'Safari',
                               autospec=True,
                               return_value=NewDriver()):

            test_results = html5_driver.NdtHtml5SeleniumDriver(
                browser='safari',
                url='http://ndt.mock-server.com:7123/',
                timeout=1000).perform_test()

        # Then s2c is converted from Gb/s to Mb/s
        self.assertEqual(test_results.s2c_result.throughput, 72000)
        # And c2s is not
        self.assertEqual(test_results.c2s_result.throughput, 34)
        # And an error object is not contained in the list
        self.assertEqual(len(test_results.errors), 0)

    def test_c2s_kbps_speed_conversion(self):
        """Test c2s speed converts from kb/s to Mb/s correctly."""

        # If c2s speed is 72 kb/s and s2c speed is 34 in the browser

        class NewDriver(object):

            def get(self, url):
                pass

            def close(self):
                pass

            def find_element_by_id(self, id):
                if id == 'upload-speed-units':
                    return mock.Mock(text='kb/s', autospec=True)
                elif id == 'upload-speed':
                    return mock.Mock(text='72', autospec=True)
                elif id == 'download-speed-units':
                    return mock.Mock(text='Mb/s', autospec=True)
                else:
                    return mock.Mock(text='34', autospec=True)

            def find_elements_by_xpath(self, xpath):
                return [mock.Mock(autospec=True)]

        with mock.patch.object(html5_driver.webdriver,
                               'Firefox',
                               autospec=True,
                               return_value=NewDriver()):

            test_results = html5_driver.NdtHtml5SeleniumDriver(
                browser='firefox',
                url='http://ndt.mock-server.com:7123/',
                timeout=1000).perform_test()

        # Then c2s is converted from kb/s to Mb/s
        self.assertEqual(test_results.c2s_result.throughput, 0.072)
        # And s2c is not
        self.assertEqual(test_results.s2c_result.throughput, 34)
        # And an error object is not contained in the list
        self.assertEqual(len(test_results.errors), 0)

    @freezegun.freeze_time('2016-01-01', tz_offset=0)
    def test_ndt_test_results_records_todays_times(self):

        class NewDriver(object):

            def get(self, url):
                pass

            def close(self):
                pass

            def find_element_by_id(self, id):
                if id == 'upload-speed-units':
                    return mock.Mock(text='kb/s', autospec=True)
                elif id == 'download-speed-units':
                    return mock.Mock(text='Mb/s', autospec=True)
                elif id == 'upload-speed' or 'download-speed':
                    return mock.Mock(text='72', autospec=True)
                else:
                    return mock.Mock(autospec=True)

            def find_elements_by_xpath(self, xpath):
                return [mock.Mock(autospec=True)]
        # When we patch datetime so it shows our current date as 2016-01-01
        self.assertEqual(datetime.datetime.now(), datetime.datetime(2016, 1, 1))

        with mock.patch.object(html5_driver.webdriver,
                               'Firefox',
                               autospec=True,
                               return_value=NewDriver()):

            test_results = html5_driver.NdtHtml5SeleniumDriver(
                browser='firefox',
                url='http://ndt.mock-server.com:7123/',
                timeout=1000).perform_test()

        # Then the readings for our test start and end times occur within
        # today's date
        self.assertEqual(test_results.start_time,
                         datetime.datetime(2016,
                                           1,
                                           1,
                                           tzinfo=pytz.utc))
        self.assertEqual(test_results.end_time,
                         datetime.datetime(2016,
                                           1,
                                           1,
                                           tzinfo=pytz.utc))

    def test_ndt_test_results_increments_time_correctly(self):
        # Create a list of times every minute starting at 2016-1-1 8:00:00
        # and ending at 2016-1-1 8:04:00. These will be the values that our
        # mock datetime.now() function returns.
        base_date = datetime.datetime(2016, 1, 1, 8, 0, 0, tzinfo=pytz.utc)
        dates = [base_date + datetime.timedelta(0, 60) * x for x in range(6)]

        class NewDriver(object):

            def get(self, url):
                pass

            def close(self):
                pass

            def find_element_by_id(self, id):
                if id == 'upload-speed-units':
                    return mock.Mock(text='kb/s', autospec=True)
                elif id == 'upload-speed':
                    return mock.Mock(text='72', autospec=True)
                elif id == 'download-speed-units':
                    return mock.Mock(text='Mb/s', autospec=True)
                else:
                    return mock.Mock(text='34', autospec=True)

            def find_elements_by_xpath(self, xpath):
                return [mock.Mock(autospec=True)]

        mock_driver = mock.patch.object(html5_driver.webdriver,
                                        'Firefox',
                                        autospec=True,
                                        return_value=NewDriver())
        mock_driver.start()
        with mock.patch.object(html5_driver.datetime,
                               'datetime',
                               autospec=True) as mocked_datetime:
            mocked_datetime.now.side_effect = dates

            test_results = html5_driver.NdtHtml5SeleniumDriver(
                browser='firefox',
                url='http://ndt.mock-server.com:7123/',
                timeout=1).perform_test()
        mock_driver.stop()

        # And the sequence of returned values follows the expected timeline
        # that the readings are taken in.
        self.assertEqual(test_results.start_time,
                         datetime.datetime(2016,
                                           1,
                                           1,
                                           8,
                                           0,
                                           0,
                                           tzinfo=pytz.utc))
        self.assertEqual(test_results.c2s_result.start_time,
                         datetime.datetime(2016,
                                           1,
                                           1,
                                           8,
                                           1,
                                           0,
                                           tzinfo=pytz.utc))
        self.assertEqual(test_results.s2c_result.start_time,
                         datetime.datetime(2016,
                                           1,
                                           1,
                                           8,
                                           3,
                                           0,
                                           tzinfo=pytz.utc))
        self.assertEqual(test_results.end_time,
                         datetime.datetime(2016,
                                           1,
                                           1,
                                           8,
                                           5,
                                           0,
                                           tzinfo=pytz.utc))


if __name__ == '__main__':
    unittest.main()
