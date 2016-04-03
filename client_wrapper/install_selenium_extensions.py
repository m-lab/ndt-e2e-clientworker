import argparse
import os
import platform
import urllib

import names

driver_urls = {
    'chrome_os_x':
    'http://chromedriver.storage.googleapis.com/2.21/chromedriver_mac32.zip',
    'chrome_ubuntu':
    'http://chromedriver.storage.googleapis.com/2.21/chromedriver_linux64.zip',
    'chrome_windows_10':
    'http://chromedriver.storage.googleapis.com/2.21/chromedriver_win32.zip',
    'edge_windows_10':
    'https://www.microsoft.com/en-us/download/confirmation.aspx?id=48212',
    'safari_os_x':
    'http://selenium-release.storage.googleapis.com/2.48/SafariDriver.safariextz'
}


def _get_full_path_downloaded_file(driver_name):
    """Gets full path of a file downloaded to a Downloads folder.

    Args:
        driver_name: A string representing the name of the file.
    """
    base_downloads_dir = os.path.join(os.path.expanduser('~'), 'Downloads/')
    return os.path.join(base_downloads_dir, driver_name)


def _download_chrome_drivers():
    """Downloads Chrome drivers for Selenium"""
    # Mac OS X
    if platform.system() == 'Darwin':
        url = driver_urls['chrome_os_x']
        chromedriver_file = 'chromedriver_mac32.zip'
        full_chromedriver_path = _get_full_path_downloaded_file(
            chromedriver_file)
        urllib.URLopener().retrieve(url, full_chromedriver_path)

    elif platform.system() == 'Linux':
        url = driver_urls['chrome_ubuntu']
        chromedriver_file = 'chromedriver_linux64.zip'
        full_chromedriver_path = _get_full_path_downloaded_file(
            chromedriver_file)
        urllib.URLopener().retrieve(url, full_chromedriver_path)

    elif platform.system() == 'Windows':
        url = driver_urls['chrome_windows_10']
        chromedriver_file = 'chromedriver_win32.zip'
        full_chromedriver_path = _get_full_path_downloaded_file(
            chromedriver_file)
        urllib.URLopener().retrieve(url, full_chromedriver_path)
    else:
        raise ValueError('Unsupported OS specified: %s' % (platform.system()))


def _download_edge_drivers():
    """Downloads Edge drivers for Selenium"""
    url = driver_urls['edge_windows_10']
    edgedriver_file = 'MicrosoftWebDriver.msi'
    full_edgedriver_path = _get_full_path_downloaded_file(edgedriver_file)
    urllib.URLopener().retrieve(url, full_edgedriver_path)


def _download_safari_drivers():
    """Downloads Safari drivers for Selenium"""
    url = driver_urls['safari_os_x']
    safaridriver_file = 'SafariDriver.safariextz'
    full_safaridriver_path = _get_full_path_downloaded_file(safaridriver_file)
    urllib.URLopener().retrieve(url, full_safaridriver_path)


def main(args):
    if args.browser == names.CHROME:
        _download_chrome_drivers()
    elif args.browser == names.EDGE:
        _download_edge_drivers()
    elif args.browser == names.SAFARI:
        _download_safari_drivers()
    elif args.browser == names.FIREFOX:
        pass
    else:
        raise ValueError('Unsupported browser specified: %s' % (args.browser))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='NDT E2E Testing Client Selenium Extension Installer',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--browser',
                        help='Browser to run under (for browser-based client)',
                        choices=('chrome', 'firefox', 'safari', 'edge'))
    main(parser.parse_args())
