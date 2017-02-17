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

import names


class Error(Exception):
    pass


class UnsupportedPlatformError(Error):
    """Indicates an unrecognized OS platform."""
    pass


class UnrecognizedVersionStringError(Error):
    """Indicates an unrecognized version string."""
    pass


def os_to_shortname(os, os_version):
    """Converts an OS name and version to its shortname.

    Given an OS name and OS version, return the OS shortname (e.g. 'win10').

    Args:
        os: The OS platform name (e.g. "Windows" or "Ubuntu").
        os_version: The version string for the platform in the form x.y where x
            is the major version and y is the minor version.

    Returns:
        The os shortname for the OS and version.

    Raises:
        UnsupportedPlatformError if the caller specifies an OS and version
        combination that does not have a known shortname.
    """
    if os == 'Windows' and os_version == '10':
        return names.WINDOWS_10
    if os == 'Windows' and os_version == '2012ServerR2':
        return names.WINDOWS_SERVER_2012_R2
    elif os == 'Ubuntu' and os_version == '14.04':
        return names.UBUNTU_14
    elif os == 'Ubuntu' and os_version == '16.04':
        return names.UBUNTU_16
    elif os == 'OSX' and os_version.startswith('10.11'):
        return names.OSX_10_11
    elif os == 'OSX' and os_version.startswith('10.12'):
        return names.OSX_10_12
    else:
        raise UnsupportedPlatformError('Unsupported OS platform: %s v%s' %
                                       (os, os_version))


def browser_to_canonical_name(browser, browser_version):
    """Converts a browser and version to its canonical name.

    Converts a browser to the format of "[name][major version]", e.g.
    "firefox49".

    Args:
        browser: Browser name to convert to canonical name (e.g. "firefox" or
            "edge").
        browser_version: Browser version string. This must contain at least one
            dot separator to separate the major version number from the rest of
            the version string (e.g. "1.56").

    Returns:
        Returns the browser in shortname form, e.g. "firefox49".
    """
    version_parts = browser_version.split('.')
    if len(version_parts) < 2:
        raise UnrecognizedVersionStringError(
            'Version string in unrecognized format: %s', browser_version)
    return browser + version_parts[0]
