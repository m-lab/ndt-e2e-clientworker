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
import contextlib
import json
import socket
import unittest
import urllib2

from client_wrapper import http_response
from client_wrapper import http_server


class ReplayHTTPServerTest(unittest.TestCase):

    def test_server_replays_response_accurately(self):
        response_data = 'mock foo response'
        stored_response = http_response.HttpResponse(200, {'Mock-Header': 'OK'},
                                                     response_data)
        with contextlib.closing(http_server.create_replay_server_manager(
            {'/foo': stored_response}, 'ndt.mock-lab.org')) as server_manager:
            server_manager.start()

            response = urllib2.urlopen('http://localhost:%d/foo' %
                                       server_manager.port)
            self.assertEqual(200, response.getcode())
            self.assertDictEqual({'mock-header': 'OK',
                                  'content-length': str(len(response_data))},
                                 parse_headers(response.info().items()))
            self.assertEqual(response_data, response.read())

    def test_server_rewrites_localhost_ips_in_responses(self):
        stored_response = http_response.HttpResponse(
            200, {}, '<a href="http://127.0.0.1/foo>Click here for foo</a>')
        with contextlib.closing(http_server.create_replay_server_manager(
            {'/bar': stored_response}, 'ndt.mock-lab.org')) as server_manager:
            server_manager.start()

            server_url = 'http://localhost:%d' % server_manager.port
            response = urllib2.urlopen('%s/bar' % server_url)
            self.assertEqual(200, response.getcode())
            # URLs like http://127.0.0.1 should be replaced with something like
            # http://localhost:65432.
            response_expected = '<a href="%s/foo>Click here for foo</a>' % server_url
            self.assertEqual(response_expected, response.read())

    def test_server_rewrites_mlabns_responses(self):
        """Server should rewrite server FQDN in mlab-ns responses."""
        stored_response = http_response.HttpResponse(
            200, {}, '[{"fqdn": "garbage to rewrite"}]')
        with contextlib.closing(http_server.create_replay_server_manager({
                '/ndt_ssl': stored_response
        }, 'mlab1.xyz0t.ndt.mock-lab.org')) as server_manager:
            server_manager.start()

            response = urllib2.urlopen('http://localhost:%d/ndt_ssl' %
                                       server_manager.port)
            self.assertEqual(200, response.getcode())
            self.assertEqual('mlab1.xyz0t.ndt.mock-lab.org',
                             json.loads(response.read())[0]['fqdn'])

    def test_server_manager_shuts_down_server_on_close(self):
        stored_response = http_response.HttpResponse(200, {}, 'dummy response')
        with contextlib.closing(http_server.create_replay_server_manager(
            {'/foo': stored_response}, 'ndt.mock-lab.org')) as server_manager:
            server_manager.start()

            url = 'http://localhost:%d/foo' % server_manager.port
            response = urllib2.urlopen(url)
            self.assertEqual(200, response.getcode())
        # Attempting to query the same URL should time out because the child
        # server should be shut down.
        with self.assertRaises(socket.timeout):
            urllib2.urlopen(url, timeout=0.025).getcode()


def parse_headers(header_items):
    """Parses headers from a list of header two-tuples.

    Parses headers from a list of header two-tuples (which are how they are
    returned from the Message.items() interface). Drops the Server and Date
    headers as they are not useful for the unit tests in this module.

    Args:
        header_items: A list of two-tuples where the first value is a header
            name and the second is the header value.

    Returns:
        The parsed headers as a dictionary of key-value pairs.
    """
    headers = {}
    for key, value in header_items:
        # BaseHTTPServer adds the Server and Date headers to each response. We
        # ignore these because they are not relevant to our testing.
        if key in ['server', 'date']:
            continue
        headers[key] = value
    return headers


if __name__ == '__main__':
    unittest.main()
