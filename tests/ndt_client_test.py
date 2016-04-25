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
import unittest


class NdtClientTest(unittest.TestCase):
    """Base class for unit tests of NDT clients.

    Defines common functions needed in unit tests of NDT clients.
    """

    def assertErrorMessagesEqual(self, expected_messages, actual_errors):
        """Verifies that a list of TestErrors have the expected error messages.

        Note that this compares just by message text and ignores timestamp.
        """
        actual_messages = [e.message for e in actual_errors]
        self.assertListEqual(expected_messages, actual_messages)
