from __future__ import absolute_import
import mock
import socket
import unittest

from client_wrapper import http_server


class MockSocketError(socket.error):

    def __init__(self, cause):
        self.cause = cause


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
        http_server.CustomRootHTTPRequestServer.side_effect = (
            MockSocketError("Mock socket error."))
        with self.assertRaises(MockSocketError):
            self.server.async_start()


if __name__ == '__main__':
    unittest.main()
