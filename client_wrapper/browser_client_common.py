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

from selenium import webdriver
from selenium.common import exceptions
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support import ui

import names

# TODO(mtlynch): Define all error strings as public constants so we're not
# duplicating strings between production code and unit test code.
ERROR_C2S_NEVER_STARTED = 'Timed out waiting for c2s test to begin.'
ERROR_S2C_NEVER_STARTED = 'Timed out waiting for s2c test to begin.'
ERROR_C2S_NEVER_ENDED = 'Timed out waiting for c2s test to end.'
ERROR_S2C_NEVER_ENDED = 'Timed out waiting for s2c test to end.'


def create_browser(browser):
    """Creates a Selenium-controlled web browser.

    Args:
        browser: Can be one of 'firefox', 'chrome', 'edge', or 'safari'

    Returns:
        An instance of a Selenium webdriver browser class corresponding to
        the specified browser.
    """
    if browser == names.FIREFOX:
        return webdriver.Firefox()
    elif browser == names.CHROME:
        return webdriver.Chrome()
    elif browser == names.EDGE:
        return webdriver.Edge()
    elif browser == names.SAFARI:
        return webdriver.Safari()
    raise ValueError('Invalid browser specified: %s' % browser)


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
