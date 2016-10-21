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
"""Defines HTTP servers for web-based NDT clients.

Defines various HTTP server classes meant for hosting web-based NDT client
implementations.
"""

import BaseHTTPServer
import datetime
import json
import logging
import SimpleHTTPServer
import threading
import urllib

import pytz

import http_response

logger = logging.getLogger(__name__)


class Error(Exception):
    pass


class HttpWaitTimeoutError(Error):
    """Error raised when waiting for an HTTP response timed out."""

    def __init__(self, port):
        super(HttpWaitTimeoutError, self).__init__(
            'Wait timeout exceeded when waiting for a response on local port ' +
            str(port))


def create_replay_server_manager(replays, ndt_server_fqdn):
    """Creates a replay server wrapped in a server manager."""
    return HttpServerManager(ReplayHTTPServer(replays, ndt_server_fqdn))


class ReplayHTTPServer(BaseHTTPServer.HTTPServer):
    """HTTP server that replays saved HTTP responses.

    Attributes:
        port: Port on which the server is listening for connections.
        replays: A dictionary of HttpResponse instances, keyed by relative URL.
    """

    def __init__(self, replays, ndt_server_fqdn):
        """Creates a new ReplayHTTPServer.

        Args:
            replays: A dictionary of HttpResponse instances, keyed by relative
                URL.
            ndt_server_fqdn: FQDN of target NDT server.
        """
        BaseHTTPServer.HTTPServer.__init__(self, ('', 0), _ReplayRequestHandler)
        self._port = self.server_address[1]
        self._replays = replays
        self._rewrite_mlabns_replays(ndt_server_fqdn)
        self._rewrite_localhost_ips()

    @property
    def port(self):
        return self._port

    @property
    def replays(self):
        return self._replays

    def _rewrite_mlabns_replays(self, ndt_server_fqdn):
        """Rewrites mlab-ns responses to point to a custom NDT server.

        Finds all mlab-ns responses in the replays and replaces the responses
        with a synthetic mlab-ns response that points to an NDT server with the
        given FQDN.

        Args:
            ndt_server_fqdn: Target NDT server to use in rewritten mlab-ns
                responses.
        """
        for path in self._replays:
            if path.startswith('/ndt'):
                original_response = self._replays[path]
                data = json.loads(original_response.data)
                for i in range(len(data)):
                    data[i]['fqdn'] = ndt_server_fqdn
                rewritten_data = json.dumps(data)
                self._replays[path] = http_response.HttpResponse(
                    original_response.response_code, original_response.headers,
                    rewritten_data)

    def _rewrite_localhost_ips(self):
        for path, original_response in self._replays.iteritems():
            # Replace all instances of 127.0.0.1 with localhost and the port that
            # our parent server is listening on.
            rewritten_data = original_response.data.replace(
                '127.0.0.1', 'localhost:%d' % self._port)
            # Update the Content-Length header since we have changed the
            # content.
            headers = original_response.headers
            headers['content-length'] = len(rewritten_data)
            self._replays[path] = http_response.HttpResponse(
                original_response.response_code, headers, rewritten_data)


class _ReplayRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    """Request handler for replaying saved HTTP responses."""

    def __init__(self, request, client_address, server):
        self._replays = server.replays
        self._server_port = server.port
        SimpleHTTPServer.SimpleHTTPRequestHandler.__init__(
            self, request, client_address, server)

    def do_GET(self):
        """Handle an HTTP GET request.

        Serve an HTTP GET request by replaying a stored response. If there is
        no matching response, serve a 404 and log a message.
        """
        try:
            response = self._replays[self.path]
        except KeyError:
            logger.info('No stored result for %s', self.path)
            self.send_error(404, 'File not found')
            return

        self.send_response(response.response_code)
        for header, value in response.headers.iteritems():
            self.send_header(header, value)
        self.end_headers()
        self.wfile.write(response.data)

    def log_message(self, format, *args):
        # Don't log messages because it creates too much logging noise.
        pass


class HttpServerManager(object):
    """A wrapper for HTTP server instances to support asynchronous running.

    Wraps HTTP server instances so that callers can easily start the server
    asynchronously with assurance that the server has begun serving.

    Attributes:
        port: The local TCP port on which the child server is listening for
            connections.
    """

    def __init__(self, http_server):
        """Creates a new HttpServerManager.

        Args:
            http_server: An HTTP server instance that has a "port" attribute and
                a "serve_forever" function.
        """
        self._http_server = http_server
        self._http_server_thread = None

    @property
    def port(self):
        return self._http_server.port

    def start(self):
        """Starts the child HTTP server.

        Starts the child HTTP server and blocks until the server begins serving
        HTTP requests. After calling start(), the owner of the instance is
        responsible for calling close() to release the child server's resources.
        """
        self._start_http_server_async()
        _wait_for_local_http_response(self._http_server.port)

    def _start_http_server_async(self):
        """Starts the child HTTP server in a background thread."""
        self._http_server_thread = threading.Thread(
            target=self._http_server.serve_forever)
        self._http_server_thread.daemon = True
        self._http_server_thread.start()

    def close(self):
        """Shut down the child HTTP server."""
        if self._http_server_thread:
            self._http_server.shutdown()
            self._http_server_thread.join()


def _wait_for_local_http_response(port):
    """Wait for a local port to begin responding to HTTP requests."""
    # Maximum number of seconds to wait for a port to begin responding to
    # HTTP requests.
    max_wait_seconds = 5
    start_time = datetime.datetime.now(tz=pytz.utc)
    while (datetime.datetime.now(tz=pytz.utc) - start_time
          ).total_seconds() < max_wait_seconds:
        try:
            urllib.urlopen('http://localhost:%d/' % port)
            return
        except IOError:
            pass
    raise HttpWaitTimeoutError(port)
