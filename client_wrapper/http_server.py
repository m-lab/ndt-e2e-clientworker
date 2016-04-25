import os
import SimpleHTTPServer
import BaseHTTPServer
import threading


class CustomRootHTTPRequestServer(BaseHTTPServer.HTTPServer):
    """HTTP request server that allows for a root directory to be set."""

    def __init__(self, root_directory):
        self.root_directory = root_directory
        BaseHTTPServer.HTTPServer.__init__(self, ('', 0),
                                           _CustomRootHTTPRequestHandler)


class _CustomRootHTTPRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    """HTTP request handler that allows for a root directory to be set."""

    def __init__(self, request, client_address, server):
        self._root = server.root_directory
        SimpleHTTPServer.SimpleHTTPRequestHandler.__init__(
            self, request, client_address, server)

    def translate_path(self, path):
        # Make sure path is relative
        if path[0] == '/':
            path = path[1:]
        return os.path.join(self._root, path)


class StaticFileHTTPServer(object):
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
        """Creates an HTTP server instance bound to a random available port.

        Port is assigned by the OS.
        """
        http_server = CustomRootHTTPRequestServer(self._client_path)
        self._port = http_server.socket.getsockname()[1]
        self._http_server = http_server

    def stop(self):
        self._http_server.shutdown()

    def async_start(self):
        """Starts a server listening on its own thread."""
        self._create_server()
        threading.Thread(target=self._http_server.serve_forever).start()
