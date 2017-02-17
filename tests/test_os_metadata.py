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
import platform
import unittest

import mock

from client_wrapper import os_metadata


class OsMetadataTest(unittest.TestCase):

    def setUp(self):
        system_patcher = mock.patch.object(platform, 'system')
        self.addCleanup(system_patcher.stop)
        system_patcher.start()

        release_patcher = mock.patch.object(platform, 'release')
        self.addCleanup(release_patcher.stop)
        release_patcher.start()

        mac_ver_patcher = mock.patch.object(platform, 'mac_ver')
        self.addCleanup(mac_ver_patcher.stop)
        mac_ver_patcher.start()

        distribution_patcher = mock.patch.object(platform, 'linux_distribution')
        self.addCleanup(distribution_patcher.stop)
        distribution_patcher.start()

    def test_detects_osx_el_sierra(self):
        platform.system.return_value = 'Darwin'
        platform.mac_ver.return_value = ('10.12.3', ('', '', ''), 'i386')
        os_name, os_version = os_metadata.get_os_metadata()
        self.assertEqual('OSX', os_name)
        self.assertEqual('10.12.3', os_version)

    def test_detects_ubuntu_14_04(self):
        platform.system.return_value = 'Linux'
        platform.linux_distribution.return_value = ('Ubuntu', '14.04',
                                                    'ignored value')
        os_name, os_version = os_metadata.get_os_metadata()
        self.assertEqual('Ubuntu', os_name)
        self.assertEqual('14.04', os_version)

    def test_detects_windows_10(self):
        platform.system.return_value = 'Windows'
        platform.release.return_value = '10'
        os_name, os_version = os_metadata.get_os_metadata()
        self.assertEqual('Windows', os_name)
        self.assertEqual('10', os_version)

    def test_detects_unknown_os(self):
        platform.system.return_value = 'Imaginary OS'
        platform.release.return_value = '54.23'
        os_name, os_version = os_metadata.get_os_metadata()
        self.assertEqual('Imaginary OS', os_name)
        self.assertEqual('54.23', os_version)
