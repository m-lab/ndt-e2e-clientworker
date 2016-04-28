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
import os
import socket
import subprocess
import unittest
import urllib2

import mock

from client_wrapper import fake_mlabns
from client_wrapper import http_server

MOCK_LISTEN_PORT = 8123
MOCK_MLABNS_PORT = 8321
MOCK_REPLAY_FILENAME = 'mock-file.replay'


class ReplayHTTPServerTest(unittest.TestCase):

    def setUp(self):
        # Mock out calls to subprocess.Popen.
        subprocess_popen_patch = mock.patch.object(subprocess,
                                                   'Popen',
                                                   autospec=True)
        self.addCleanup(subprocess_popen_patch.stop)
        subprocess_popen_patch.start()

        self.mock_mlabns_server = mock.Mock(spec=fake_mlabns.FakeMLabNsServer,
                                            port=MOCK_MLABNS_PORT)

    def make_server(self):
        """Convenience method to create server under test."""
        return http_server.ReplayHTTPServer(
            MOCK_LISTEN_PORT, self.mock_mlabns_server, MOCK_REPLAY_FILENAME)

    def test_creating_server_creates_correct_threads_and_processes(self):
        mock_mitmdump_proc = mock.Mock()
        subprocess.Popen.return_value = mock_mitmdump_proc

        with contextlib.closing(self.make_server()):
            # Verify that mitmdump was spawned correctly
            subprocess.Popen.assert_called_once_with(
                ['mitmdump', '--no-http2', '--no-pop', '--port=8123',
                 '--reverse=http://ignored.ignored', '--replay-ignore-host',
                 '--server-replay=mock-file.replay',
                 '--replace=/~s/mlab\\-ns\\.appspot\\.com/localhost\\:8321'],
                stdout=subprocess.PIPE)
            # Verify that mlab-ns server is serving
            self.assertTrue(self.mock_mlabns_server.serve_forever.called)
            # Verify that the internal workers are not killed before we exit
            # the context handler.
            self.assertFalse(mock_mitmdump_proc.kill.called)
            self.assertFalse(self.mock_mlabns_server.shutdown.called)

        # After exiting the context handler, the internal workers should be
        # terminated.
        self.assertTrue(mock_mitmdump_proc.kill.called)
        self.assertTrue(self.mock_mlabns_server.shutdown.called)

    def test_raises_error_when_mitmproxy_is_not_installed(self):
        """If we can't execute mitmproxy, show a helpful error."""
        # Cause a mock error when spawning the mitmproxy process.
        subprocess.Popen.side_effect = OSError('mock OSError')

        with self.assertRaises(http_server.MitmProxyNotInstalledError):
            with contextlib.closing(self.make_server()):
                pass


class StaticFileHTTPServerTest(unittest.TestCase):

    def setUp(self):
        # Build an absolute path to the test data from the current working
        # directory and constant relative path to test data
        test_directory = os.path.join(os.getcwd(),
                                      'tests/testdata/static_file_server')
        self.server = http_server.StaticFileHTTPServer(test_directory)

    def test_http_server_serves_correct_file(self):
        self.server.async_start()
        self.assertIsNotNone(self.server.port)

        actual_response = urllib2.urlopen('http://127.0.0.1:%d/foo.html' %
                                          self.server.port).read()
        expected_response = '<!DOCTYPE html><html>foo</html>\n'

        self.assertEqual(actual_response, expected_response)
        self.server.close()

    @mock.patch.object(http_server, '_CustomRootHTTPRequestServer')
    def test_http_server_async_start_fails_when_server_constructor_throws_a_socket_error(
            self, mock_server):

        class MockSocketError(socket.error):

            def __init__(self, cause):
                self.cause = cause

        mock_server.side_effect = (MockSocketError('Mock socket error.'))
        with self.assertRaises(MockSocketError):
            self.server.async_start()


if __name__ == '__main__':
    unittest.main()
