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
        self.mock_tcp_server = mock.Mock(name='mock_tcp_server')

        tcp_server_patch = mock.patch.object(
            ndt_client_http_server.SocketServer,
            'TCPServer',
            autospec=True)
        tcp_server_patch.return_value = self.mock_tcp_server
        self.addCleanup(tcp_server_patch.stop)
        tcp_server_patch.start()

        http_handler_patch = mock.patch.object(
            ndt_client_http_server,
            'get_custom_handler_and_set_root_directory',
            return_value=self.mock_handler,
            autopsec=True)
        self.addCleanup(http_handler_patch.stop)
        http_handler_patch.start()

        self.mock_tcp_server.socket.getsockname.return_value = ['', 8888]
        ndt_client_http_server.SocketServer.TCPServer.return_value = self.mock_tcp_server

    def test_ndt_client_http_server_async_start_starts_and_returns_successfully(
            self):
        self.server.async_start()
        self.server.stop()
        self.assertEqual(8888, self.server.port)
        self.assertEqual(self.mock_tcp_server, self.server._tcp_server)
        ndt_client_http_server.SocketServer.TCPServer.assert_called_with(
            ('', 0), self.mock_handler)
        self.assertTrue(self.mock_tcp_server.serve_forever.called)
        self.assertTrue(self.mock_tcp_server.shutdown.called)

    def test_ndt_client_http_server_async_start_fails_when_server_constructor_throws_exception(
            self):
        ndt_client_http_server.SocketServer.TCPServer.side_effect = MockSocketError(
            "Mock socket error.")
        with self.assertRaises(MockSocketError):
            self.server.async_start()

    def test_assures_that_asynch_start_leaves_ndt_client_http_server_instance_responsive(
            self):
        self.server.async_start()
        self.assertEqual(self.server.port, 8888)
        self.server.stop()
        self.assertTrue(self.mock_tcp_server.serve_forever.called)
        self.assertTrue(self.mock_tcp_server.shutdown.called)


if __name__ == '__main__':
    unittest.main()
