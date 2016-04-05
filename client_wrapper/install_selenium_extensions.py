import argparse
import os
import platform
import urllib
import tempfile

import names

driver_urls = {
    'chrome_os_x': {
        'url':
        'http://chromedriver.storage.googleapis.com/2.21/chromedriver_mac32.zip',
        'file_name': 'chromedriver_mac32.zip'
    },
    'chrome_ubuntu': {
        'url':
        'http://chromedriver.storage.googleapis.com/2.21/chromedriver_linux64.zip',
        'file_name': 'chromedriver_linux64.zip'
    },
    'chrome_windows_10': {
        'url':
        'http://chromedriver.storage.googleapis.com/2.21/chromedriver_win32.zip',
        'file_name': 'chromedriver_win32.zip'
    },
    'edge_windows_10': {
        'url':
        'https://download.microsoft.com/download/8/D/0/8D0D08CF-790D-4586-B726-C6469A9ED49C/MicrosoftWebDriver.msi',
        'file_name': 'edge_windows_10.zip'
    },
    'safari_os_x': {
        'url':
        'http://selenium-release.storage.googleapis.com/2.48/SafariDriver.safariextz',
        'file_name': 'SafariDriver.safariextz',
    }
}


def _download_chrome_drivers():
    """Downloads Chrome drivers for Selenium."""
    # Mac OS X
    if platform.system() == 'Darwin':
        remote_file = driver_urls['chrome_os_x']
        _download_temp_file(remote_file['url'], remote_file['file_name'])

    elif platform.system() == 'Linux':
        remote_file = driver_urls['chrome_ubuntu']
        _download_temp_file(remote_file['url'], remote_file['file_name'])

    elif platform.system() == 'Windows':
        remote_file = driver_urls['chrome_windows_10']
        _download_temp_file(remote_file['url'], remote_file['file_name'])
    else:
        raise ValueError('Unsupported OS specified: %s' % (platform.system()))


def _download_temp_file(url, file_name):
    """Downloads file into temp directory.

    Args:
        url: A string representing the URL the file is to be downloaded from.
        file_name: A string representing the name of the file to be downloaded.
    """
    temp_dir = tempfile.mkdtemp()
    download_path = os.path.join(temp_dir, file_name)
    print('File downloading to %s' % download_path)
    urllib.URLopener().retrieve(url, download_path)


def _download_edge_drivers():
    """Downloads Edge drivers for Selenium."""
    remote_file = driver_urls['edge_windows_10']
    _download_temp_file(remote_file['url'], remote_file['file_name'])


def _download_safari_drivers():
    """Downloads Safari drivers for Selenium."""
    remote_file = driver_urls['safari_os_x']
    _download_temp_file(remote_file['url'], remote_file['file_name'])


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
