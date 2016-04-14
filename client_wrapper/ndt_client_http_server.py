import os
import SimpleHTTPServer
import BaseHTTPServer
import threading


def create_custom_http_handler_class(root_directory):
    """Creates and returns a custom SimpleHTTPRequestHandler subclass.

    Custom handler class handles requests relative to root_directory. Class
    creation takes place within a function to allow for dynamic defining of
    an instance variable to an uninstantiated class passed into the
    BaseHTTPServer.HTTPServer constructor.

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
            # Make sure path is relative
            if path[0] == '/':
                path = path[1:]
            return os.path.join(self._root, path)

    return CustomRootHTTPRequestHandler


class NdtClientHTTPServer(object):
    """A simple HTTP server that listens on a randomly assigned port.

    Serves GET requests for files in a specified directory.

    Attributes:
        client_path: Absolute path to the client files.
        port: Integer of the port number the server is bound to.
    """

    def __init__(self, client_path):
        self._client_path = client_path
        self._port = None
        self._http_server = None

    @property
    def port(self):
        return self._port

    def _create_server(self):
        """Creates a TCPServer instance bound to a random available port.

        Port is assigned by the OS.
        """
        # Create a custom handler class that we pass to the server
        handler = create_custom_http_handler_class(self._client_path)
        http_server = BaseHTTPServer.HTTPServer(('', 0), handler)

        self._port = http_server.socket.getsockname()[1]
        self._http_server = http_server

    def stop(self):
        self._http_server.shutdown()

    def async_start(self):
        """Starts a server listening on its own thread."""
        self._create_server()
        threading.Thread(target=self._http_server.serve_forever).start()
