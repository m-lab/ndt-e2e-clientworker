from __future__ import absolute_import
import mock
import socket
import unittest

from client_wrapper import local_server


class MockSocketError(socket.error):

    def __init__(self, cause):
        self.cause = cause


class LocalServer(unittest.TestCase):

    def setUp(self):
        self.server = local_server.LocalServer()
        self.mock_handler = mock.Mock(name='mock_handler')
        self.mock_tcp_server = mock.Mock(name='mock_tcp_server')

        tcp_server_patch = mock.patch.object(local_server.SocketServer,
                                             'TCPServer',
                                             autospec=True)
        tcp_server_patch.return_value = self.mock_tcp_server
        self.addCleanup(tcp_server_patch.stop)
        tcp_server_patch.start()

        http_handler_patch = mock.patch.object(
            local_server,
            'SimpleHTTPServer',
            SimpleHTTPRequestHandler=self.mock_handler,
            autopsec=True)
        self.addCleanup(http_handler_patch.stop)
        http_handler_patch.start()

        self.mock_tcp_server.socket.getsockname.return_value = ['', 8888]
        local_server.SocketServer.TCPServer.return_value = self.mock_tcp_server

    def test_local_server_create_server_returns_successfully(self):
        self.server._create_server()
        self.assertEqual(8888, self.server.port)
        self.assertEqual(self.mock_tcp_server, self.server._tcp_server)
        local_server.SocketServer.TCPServer.assert_called_with(
            ('', 0), self.mock_handler)

    def test_local_server_create_server_fails_when_server_constructor_throws_exceptions(
            self):
        local_server.SocketServer.TCPServer.side_effect = MockSocketError(
            "Mock socket error.")
        with self.assertRaises(MockSocketError):
            self.server._create_server()

    def test_assures_that_asynch_start_leaves_the_local_server_instance_responsive(
            self):
        self.server.asynch_start()
        self.assertEqual(self.server.port, 8888)
        self.server.stop()


if __name__ == '__main__':
    unittest.main()
