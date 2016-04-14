from __future__ import absolute_import
import mock
import socket
import unittest

from client_wrapper import ndt_client_http_server


class MockSocketError(socket.error):

    def __init__(self, cause):
        self.cause = cause


class NdtClientHTTPServerTest(unittest.TestCase):

    def setUp(self):
        self.server = ndt_client_http_server.NdtClientHTTPServer(
            'mock/client/path')
        self.mock_handler = mock.Mock(name='mock_handler')
        self.mock_http_server = mock.Mock(name='mock_http_server')

        tcp_server_patch = mock.patch.object(
            ndt_client_http_server.BaseHTTPServer,
            'HTTPServer',
            autospec=True)
        tcp_server_patch.return_value = self.mock_http_server
        self.addCleanup(tcp_server_patch.stop)
        tcp_server_patch.start()

        http_handler_patch = mock.patch.object(
            ndt_client_http_server,
            'create_custom_http_handler_class',
            return_value=self.mock_handler,
            autopsec=True)
        self.addCleanup(http_handler_patch.stop)
        http_handler_patch.start()

        self.mock_http_server.socket.getsockname.return_value = ['', 8888]
        ndt_client_http_server.BaseHTTPServer.HTTPServer.return_value = self.mock_http_server

    def test_ndt_client_http_server_async_start_starts_and_returns_successfully(
            self):
        self.server.async_start()
        self.server.stop()
        self.assertEqual(8888, self.server.port)
        self.assertEqual(self.mock_http_server, self.server._http_server)
        ndt_client_http_server.BaseHTTPServer.HTTPServer.assert_called_with(
            ('', 0), self.mock_handler)
        self.assertTrue(self.mock_http_server.serve_forever.called)
        self.assertTrue(self.mock_http_server.shutdown.called)

    def test_ndt_client_http_server_async_start_fails_when_server_constructor_throws_exception(
            self):
        ndt_client_http_server.BaseHTTPServer.HTTPServer.side_effect = MockSocketError(
            "Mock socket error.")
        with self.assertRaises(MockSocketError):
            self.server.async_start()

    def test_async_start_leaves_ndt_client_http_server_instance_responsive(
            self):
        self.server.async_start()
        self.assertEqual(self.server.port, 8888)
        self.server.stop()
        self.assertTrue(self.mock_http_server.serve_forever.called)
        self.assertTrue(self.mock_http_server.shutdown.called)


if __name__ == '__main__':
    unittest.main()
