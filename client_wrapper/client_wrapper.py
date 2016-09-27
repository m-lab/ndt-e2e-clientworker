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

import argparse
import contextlib
import logging
import os

import banjo_driver
import filename
import html5_driver
import http_response
import http_server
import names
import result_encoder
import os_metadata

logger = logging.getLogger(__name__)


def main(args):
    _configure_logging(args.verbose)
    if args.client == names.BANJO:
        with open(args.client_path) as replay_file:
            replays = http_response.parse_yaml(replay_file.read())
        with contextlib.closing(http_server.create_replay_server_manager(
                replays, args.server)) as replay_server_manager:
            replay_server_manager.start()
            logger.info('replay server replaying %s on port %d',
                        args.client_path, replay_server_manager.port)
            url = 'http://localhost:%d/search?q=internet+speed+test' % \
                replay_server_manager.port
            logger.info('starting tests against %s', url)
            driver = banjo_driver.BanjoDriver(args.browser, url)
            _run_test_iterations(driver, args.iterations, args.output)
    elif args.client == names.NDT_HTML5:
        driver = html5_driver.NdtHtml5SeleniumDriver(args.browser, args.server)
        _run_test_iterations(driver, args.iterations, args.output)
    else:
        raise ValueError('unsupported NDT client: %s' % args.client)


def _configure_logging(verbose):
    """Configure the root logger for log output."""
    root_logger = logging.getLogger()
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    if verbose:
        root_logger.setLevel(logging.INFO)
    else:
        root_logger.setLevel(logging.WARNING)


def _run_test_iterations(driver, iterations, output_dir):
    """Use the given client driver to run the specified number of iterations.

    Given an NDT client driver, run NDT tests for the given number of
    iterations. On completion of each test, save the result to disk and print
    the result to the console.

    Args:
        driver: An NDT client driver that supports the perform_test API.
        iterations: The total number of test iterations to run.
        output_dir: Directory in which to result file.
    """
    for i in range(iterations):
        logger.info('starting iteration %d...', (i + 1))
        print 'starting iteration %d...' % (i + 1)
        result = driver.perform_test()
        result.os, result.os_version = os_metadata.get_os_metadata()
        print _jsonify_result(result)
        _save_result(result, output_dir)


def _save_result(result, output_dir):
    """Saves an NdtResult instance to a file in output_dir.

    Serializes an NdtResult to JSON format, automatically generates a
    filename based on the NdtResult metadata, then saves it to output_dir.

    Args:
        result: NdtResult instance to save.
        output_dir: Directory in which to result file.
    """
    output_filename = filename.create_result_filename(result)
    output_path = os.path.join(output_dir, output_filename)
    with open(output_path, 'w') as output_file:
        output_file.write(_jsonify_result(result))


def _jsonify_result(result):
    return result_encoder.NdtResultEncoder(indent=2,
                                           sort_keys=True).encode(result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='NDT E2E Testing Client Wrapper',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--client',
                        help='NDT client implementation to run',
                        choices=(names.NDT_HTML5, names.BANJO),
                        required=True)
    parser.add_argument('--browser',
                        help='Browser to run under (for browser-based client)',
                        choices=('chrome', 'firefox', 'safari', 'edge'))
    parser.add_argument('--client_path',
                        help=('Path to client files. Depending on the type of '
                              'client, these can be replay files, static HTML '
                              'files (not implemented), or a client binary '
                              '(not implemented)'))
    parser.add_argument('--server', help='FQDN of NDT server to test against')
    parser.add_argument('--output',
                        help='Directory in which to write output',
                        required=True)
    parser.add_argument('-v',
                        '--verbose',
                        action='store_true',
                        help='Use verbose logging')
    parser.add_argument('--iterations',
                        help='Number of iterations to run',
                        type=int,
                        default=1)
    main(parser.parse_args())
