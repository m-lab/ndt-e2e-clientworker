import os
import SimpleHTTPServer
import SocketServer
import threading


def get_custom_handler_and_set_root_directory(root_directory):
    """Creates and returns a custom SimpleHTTPRequestHandler subclass.

    Custom handler class handles requests relative to root_directory.

    Args:
        root_directory: Absolute path to directory used as root for handler.
    """

    class CustomRootHTTPRequestHandler(
            SimpleHTTPServer.SimpleHTTPRequestHandler):
        """HTTP request handler that allows for a root directory to be set."""

        def __init__(self, request, client_address, server):
            self._root = root_directory
            SimpleHTTPServer.SimpleHTTPRequestHandler.__init__(
                self, request, client_address, server)

        def translate_path(self, path):
            return os.path.join(path, self._root)

    return CustomRootHTTPRequestHandler


class NdtClientHTTPServer(object):
    """Represents a SimpleHTTPServer listening on a randomly assigned port.

    Attributes:
        port: Integer of the port number the server is bound to.
        client_path: Absolute path to the client files.
    """

    def __init__(self, client_path):
        self.client_path = client_path
        self._port = None
        self._tcp_server = None

    @property
    def port(self):
        return self._port

    def _create_server(self):
        """Creates a TCPServer instance bound to a random available port.

        Port is assigned by the OS.
        """
        handler = get_custom_handler_and_set_root_directory(self.client_path)
        tcp_server = SocketServer.TCPServer(('', 0), handler)

        self._port = tcp_server.socket.getsockname()[1]
        self._tcp_server = tcp_server

    def _start_server(self):
        self._tcp_server.serve_forever()

    def stop(self):
        self._tcp_server.shutdown()

    def async_start(self):
        """Starts a server listening on its own thread."""
        self._create_server()
        serving_thread = threading.Thread(target=self._start_server)
        serving_thread.start()
