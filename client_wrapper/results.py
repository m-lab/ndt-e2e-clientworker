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

import datetime

import pytz


class NdtSingleTestResult(object):
    """Result of a single NDT test.

    Attributes:
        throughput: The final recorded throughput (in Mbps).
        start_time: The datetime when the test began (or None if the test
            never began).
        end_time: The datetime when the test competed (or None if the test
            never completed).
    """

    def __init__(self, throughput=None, start_time=None, end_time=None):
        self.throughput = throughput
        self.start_time = start_time
        self.end_time = end_time


class TestError(object):
    """Log message of an error encountered in the test.

    Attributes:
        message: String describing the error.
        timestamp: Datetime of when the error was observed.
    """

    def __init__(self, message, timestamp=datetime.datetime.now(pytz.utc)):
        self._message = message
        self._timestamp = timestamp

    @property
    def message(self):
        return self._message

    @property
    def timestamp(self):
        return self._timestamp


class NdtResult(object):
    """Represents the results of a complete NDT HTML5 client test.

    Attributes:
        start_time: The datetime at which the NDT client was launched. This is
            time at which the client wrapper begins running a particular client,
            but is not necessarily the time at which the client itself initiated
            a test.
        end_time: The datetime at which the NDT client completed. This should be
            equal to the end_time of the client's last test or the time of a
            fatal error in the client.
        errors: A list of TestError objects representing any errors encountered
            during the tests (or an empty list if all tests were successful).
        c2s_result: The NdtSingleResult for the c2s (upload) test (or None if no
            result was recorded).
        s2c_result: The NdtSingleResult for the s2c (download) test (or None if
            no result was recorded).
        latency: The reported latency (in milliseconds) or None if the test did
            not complete.
        os: Name of OS in which the test ran (e.g. "Windows").
        os_version: OS version string (e.g. "10.0").
        client: Shortname of the NDT client (e.g. "ndt_js").
        client_version: Version string of the NDT client (e.g. "4.0.1").
        browser: Name of browser through which the test was performed (or None
            for a non-browser test).
        browser_version: Browser's version string (or None for a non-browser
            test).
    """

    def __init__(self,
                 start_time=None,
                 end_time=None,
                 errors=[],
                 c2s_result=None,
                 s2c_result=None,
                 latency=None):
        self.start_time = start_time
        self.end_time = end_time
        self.c2s_result = c2s_result
        self.s2c_result = s2c_result
        self.errors = errors
        self.latency = latency
        self.os = None
        self.os_version = None
        self.client = None
        self.client_version = None
        self.browser = None
        self.browser_version = None

    def __str__(self):
        return 'NDT Results:\n Start Time: %s,\n End Time: %s'\
        ',\n Latency: %s, \nErrors: %s' % (
            self.start_time, self.end_time, self.latency, self.errors)
