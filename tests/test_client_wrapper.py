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
import os
import sys
import unittest
import mock
from client_wrapper import client_wrapper
import selenium

sys.path.insert(1, os.path.abspath(os.path.join(
    os.path.dirname(__file__), '../client_wrapper')))
import foo


class ClientWrapperTest(unittest.TestCase):

    def test_run_tests_executes_all_tests_successfully(self):
        """Dummy test to exercise CI setup, not permanent."""
        self.assertTrue(foo.bar())

    def test_invalid_URL_throws_error(self):
        selenium_driver = client_wrapper.NdtHtml5SeleniumDriver()
        test_results = selenium_driver.perform_test(url='invalid_url',
                                                    browser='firefox')

        # We have one error
        self.assertEqual(len(test_results.errors), 1)

        # And that error is about the test results URL not being well-formed
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
