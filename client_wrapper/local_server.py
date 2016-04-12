import SimpleHTTPServer
import SocketServer
import threading


class LocalServer(object):

    def __init__(self):
        self._port = None
        self._tcp_server = None

    def _create_server(self):
        """Creates a TCPServer instance bound to an assigned port.

        Port is assigned by the OS.
        """
        handler = SimpleHTTPServer.SimpleHTTPRequestHandler
        tcp_server = SocketServer.TCPServer(('', 0), handler)

        self._port = tcp_server.socket.getsockname()[1]
        self._tcp_server = tcp_server

    def _start_server(self):
        self._tcp_server.serve_forever()

    def stop(self):
        self._tcp_server.shutdown()

    def asynch_start(self):
        """Starts a server listening on its own thread."""
        self._create_server()
        serving_thread = threading.Thread(target=self._start_server)
        serving_thread.start()

    @property
    def port(self):
        return self._port
