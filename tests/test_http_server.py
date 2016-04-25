<<<<<<< 31a7565a55aed162f5806e42ad87e6bb3398fa9c
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
<<<<<<< 202d231b747f930f373efb7c9bd89e52365aa1af
import re
=======
import socket
import subprocess
>>>>>>> Removed the function that created a custom http handler, replaced it with creating a custom server class
import unittest

import mock

from client_wrapper import fake_mlabns
from client_wrapper import http_server

MOCK_LISTEN_PORT = 8123
MOCK_MLABNS_PORT = 8321
MOCK_REPLAY_FILENAME = 'mock-file.replay'


class ReplayHTTPServerTest(unittest.TestCase):

    def setUp(self):
        # Mock out calls to subprocess.Popen.
        subprocess_popen_patch = mock.patch.object(http_server.subprocess,
                                                   'Popen',
                                                   autospec=True)
        self.addCleanup(subprocess_popen_patch.stop)
        subprocess_popen_patch.start()

        # Mock out calls to urllib.urlopen.
        urllib_urlopen_patch = mock.patch.object(http_server.urllib,
                                                 'urlopen',
                                                 autospec=True)
        self.addCleanup(urllib_urlopen_patch.stop)
        urllib_urlopen_patch.start()

        # Create a set of mock ports that we will simulate opening. Any port in
        # the set is a port we're simulating a listen on.
        self.mock_listening_ports = set()

        # Create a mock implementation of urlopen that raises IOError unless the
        # requested port is one that has been set to listen.
        def mock_urlopen(url):
            # Parse the port number from the URL.
            match = re.search(r'localhost:(\d+)', url)
            if not match:
                raise ValueError('test error: url in unexpected format: %s' %
                                 url)
            port = int(match.group(1))

            # If the requested port is one we're simulating a listen on, return
            # a dummy response. Otherwise, raise an IOError.
            if port in self.mock_listening_ports:
                return 'mock HTTP response'
            else:
                raise IOError('mock error from urlopen')

        http_server.urllib.urlopen.side_effect = mock_urlopen

        self.mock_mlabns_server = mock.Mock(spec=fake_mlabns.FakeMLabNsServer,
                                            port=MOCK_MLABNS_PORT)

        # Simulate listening on the mlab-ns listen port when the serve_forever
        # method is called.
        self.mock_mlabns_server.serve_forever.side_effect = (
            lambda: self.mock_listening_ports.add(MOCK_MLABNS_PORT))

    def make_server(self):
        """Convenience method to create server under test."""
        return http_server.ReplayHTTPServer(
            MOCK_LISTEN_PORT, self.mock_mlabns_server, MOCK_REPLAY_FILENAME)

    def test_creating_server_creates_correct_threads_and_processes(self):
        mock_mitmdump_proc = mock.Mock()

        # Mock the effect of launching mitmdump in a subprocess. Simulate a
        # listen on the port that mitmdump would listen on.
        #
        # Note: stdout is unused, but it must be named "stdout" because the code
        # under test calls the function with a keyword parameter.
        def mock_mitmdump_popen(unused_args, stdout):
            self.mock_listening_ports.add(MOCK_LISTEN_PORT)
            return mock_mitmdump_proc

        http_server.subprocess.Popen.side_effect = mock_mitmdump_popen

        with contextlib.closing(self.make_server()):
            # Verify that mitmdump was spawned correctly.
            http_server.subprocess.Popen.assert_called_once_with(
                ['mitmdump', '--no-http2', '--no-pop', '--port=8123',
                 '--reverse=http://ignored.ignored', '--replay-ignore-host',
                 '--server-replay=mock-file.replay',
                 '--replace=/~s/mlab\\-ns\\.appspot\\.com/localhost\\:8321'],
                stdout=http_server.subprocess.PIPE)
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
        http_server.subprocess.Popen.side_effect = OSError('mock OSError')

        with self.assertRaises(http_server.MitmProxyNotInstalledError):
            with contextlib.closing(self.make_server()):
                pass


class StaticFileHTTPServerTest(unittest.TestCase):

    def setUp(self):
        self.server = http_server.StaticFileHTTPServer('mock/client/path')
        self.mock_handler = mock.Mock()
        self.mock_http_server = mock.Mock()

        http_server_patch = mock.patch.object(http_server,
                                              'CustomRootHTTPRequestServer',
                                              autospec=True)
        self.addCleanup(http_server_patch.stop)
        http_server_patch.start()

    def test_http_server_async_start_starts_and_returns_successfully(self):
        self.mock_http_server.socket.getsockname.return_value = ['', 8888]
        http_server.CustomRootHTTPRequestServer.return_value = (
            self.mock_http_server)

        self.server.async_start()
        self.assertEqual(8888, self.server.port)
        http_server.CustomRootHTTPRequestServer.assert_called_with(
            'mock/client/path')
        self.assertTrue(self.mock_http_server.serve_forever.called)
        self.assertFalse(self.mock_http_server.shutdown.called)

        self.server.stop()
        self.assertTrue(self.mock_http_server.shutdown.called)

    def test_http_server_async_start_fails_when_server_constructor_throws_exception(
            self):
        class MockSocketError(socket.error):

            def __init__(self, cause):
                self.cause = cause

        http_server.CustomRootHTTPRequestServer.side_effect = (
            MockSocketError("Mock socket error."))
        with self.assertRaises(MockSocketError):
            self.server.async_start()


if __name__ == '__main__':
    unittest.main()
