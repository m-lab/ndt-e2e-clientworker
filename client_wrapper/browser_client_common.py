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

from selenium import webdriver
from selenium.common import exceptions
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support import ui

import names
import results

# Number of seconds to wait for any particular event to occur in the browser UI
# (e.g. page load, element becomes clickable).
UI_WAIT_TIMEOUT = 2

# Number of seconds to wait for the test negotiation phase to complete and the
# test to begin.
NDT_TEST_NEGOTIATION_TIMEOUT = 8

# Number of seconds to wait for an NDT c2s or s2c test to complete (test is ten
# seconds, plus four seconds of fudge factor).
NDT_TEST_RUN_TIMEOUT = 10 + 4

ERROR_FAILED_TO_LOAD_URL_FORMAT = 'Failed to load URL: %s'
ERROR_TIMED_OUT_WAITING_FOR_PAGE_LOAD = 'Timed out waiting for page to load.'

# TODO(mtlynch): Define all error strings as public constants so we're not
# duplicating strings between production code and unit test code.
ERROR_C2S_NEVER_STARTED = 'Timed out waiting for c2s test to begin.'
ERROR_S2C_NEVER_STARTED = 'Timed out waiting for s2c test to begin.'
ERROR_C2S_NEVER_ENDED = 'Timed out waiting for c2s test to end.'
ERROR_S2C_NEVER_ENDED = 'Timed out waiting for s2c test to end.'


class Error(Exception):
    pass


class BrowserVersionMissing(Error):
    """Error raised when a browser version does not apper in Selenium driver."""
    pass


@contextlib.contextmanager
def create_browser(browser):
    """Creates a context manager for a Selenium-controlled web browser.

    Creates a context manager to produce a Selenium-driven web browser. The
    Caller should call this function from within a with block so that the
    Selenium resources are freed properly when the browser is no longer needed.

    Args:
        browser: Can be one of 'firefox', 'chrome', 'edge', or 'safari'

    Yields:
        An instance of a Selenium webdriver browser class corresponding to
        the specified browser.
    """
    if browser == names.FIREFOX:
        driver = webdriver.Firefox()
    elif browser == names.CHROME:
        driver = webdriver.Chrome()
    elif browser == names.EDGE:
        driver = webdriver.Edge()
    elif browser == names.SAFARI:
        driver = webdriver.Safari()
    else:
        raise ValueError('Invalid browser specified: %s' % browser)

    # currently ignored by the Chrome driver
    driver.set_page_load_timeout(10)

    yield driver
    driver.quit()


def get_browser_version(driver):
    """Determine the browser version for a Selenium WebDriver instance.

    Args:
        driver: A Selenium WebDriver instance.

    Returns:
        A version string for the browser, e.g. "45.0.3".

    Raises:
        BrowserVersionMissing: Browser version could not be determined.
    """
    # Most drivers put the version information in the 'version' field.
    if 'version' in driver.capabilities and driver.capabilities['version']:
        return driver.capabilities['version']
    # Drivers like Edge's WebDriver lack a 'version' field and instead have a
    # 'browserVersion' field.
    elif 'browserVersion' in driver.capabilities:
        return driver.capabilities['browserVersion']
    else:
        raise BrowserVersionMissing(
            'Could not identify browser version from driver.')


def load_url(driver, url, errors):
    """Loads the URL in a Selenium driver for an NDT test.

    Args:
        driver: An instance of a Selenium webdriver.
        url: The URL to load.
        errors: A list of errors that will be appended to if the URL cannot be
            loaded.

    Returns:
        True if loading the URL was successful.
    """
    try:
        driver.get(url)
    except (exceptions.WebDriverException, exceptions.TimeoutException) as e:
        if type(e) is exceptions.TimeoutException:
            errors.append(results.TestError(
                ERROR_TIMED_OUT_WAITING_FOR_PAGE_LOAD))
        errors.append(results.TestError(ERROR_FAILED_TO_LOAD_URL_FORMAT % url))
        return False
    return True


def wait_until_element_is_visible(driver, element, timeout):
    """Waits until a DOM element is visible within a given timeout.

    Args:
        driver: An instance of a Selenium webdriver browser class.
        element: A Selenium webdriver element.
        timeout: The maximum time to wait (in seconds).

    Returns:
        True if the element became visible within the timeout.
    """
    try:
        ui.WebDriverWait(
            driver, timeout).until(expected_conditions.visibility_of(element))
    except exceptions.TimeoutException:
        return False
    return True


def find_element_containing_text(driver, text):
    """Finds the element that contains the specified text in the browser DOM.

    Args:
        driver: An instance of a Selenium webdriver browser class.
        text: Text to search for within elements.

    Returns:
        The first element in the DOM that contains the specified text, or None
        if there are no matches.
    """
    return driver.find_element_by_xpath('//*[contains(text(), \'%s\')]' % text)
