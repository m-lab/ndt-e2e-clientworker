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
"""Defines string constant for different names used throughout the system.

This module defines the constant names of different strings used throughout the
testing system to identify NDT clients, browsers, and operating systems.
"""

# NDT client shortnames
NDT_HTML5 = 'ndt_js'  # Official NDT HTML5 reference client

# Browser name constants
FIREFOX = 'firefox'
CHROME = 'chrome'
EDGE = 'edge'
SAFARI = 'safari'

# OS shortnames
WINDOWS_10 = 'win10'
UBUNTU_14 = 'ubuntu14.04'
OSX_10_11 = 'osx10.11'

EXPECTED_PATHS = {
    'MAC': '/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome',
    'LINUX': '/usr/bin/google-chrome',
}
