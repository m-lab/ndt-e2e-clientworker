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

import re
import subprocess
import threading


class Error(Exception):
    pass


class MitmProxyNotInstalledError(Error):
    """Error raised when mitmproxy seems to not be installed."""

    def __init__(self):
        super(MitmProxyNotInstalledError, self).__init__(
            'Failed to execute mitmdump utility. Is mitmproxy installed? '
            'http://docs.mitmproxy.org/en/stable/install.html')


class ReplayHTTPServer(object):
    """HTTP server that replays saved HTTP traffic to facilitate an NDT test.

    This replays HTTP traffic from a mitmdump file in order to replicate a
    remote web application that hosts a web-based NDT client.

    This is a more complex NDT HTTP server host that is meant to host NDT
    clients that cannot be represented easily with static HTML files. In
    general, most NDT clients can be hosted with StaticHTTPServer (not yet
    implemented) and should prefer that class to ReplayHTTPServer.

    Caller is responsible for cleaning up the replay server's resources by
    calling close() on the instance.
    """

    def __init__(self, listen_port, mlabns_server, replay_filename):
        """Create a new ReplayHTTPServer instance and listen for connections.

        Args:
            listen_port: The local port on which to listen on to replay traffic.
                This will allow HTTP clients to connect to this port as if were
                a normal web server.
            mlabns_server: An instance of FakeMLabNsServer to use as the fake
                mlab-ns server for traffic replays.
            replay_filename: Path to filename that contains a mitmdump/mitmproxy
                traffic capture file. The replay server will use this file to
                replay HTTP traffic.
        """
        self._listen_port = listen_port
        self._mlabns_server = mlabns_server
        self._replay_filename = replay_filename
        self._mlabns_thread = None
        self._server_proc = None
        self._start_async()

    def _start_async(self):
        """Start the replay HTTP traffic server asynchronously.

        Starts the replay HTTP server in a separate process and the fake mlab-ns
        server in a separate thread.

        Note that it is in theory possible to launch mitmdump in pure Python
        using the mitmproxy package. We choose not to because those APIs are
        not documented, whereas the command line parameters are. We therefore
        run mitmdump in a separate process even though it's a bit uglier to do
        so.
        """
        cmd_params = ['mitmdump']
        # Suppress warning about lack of HTTP/2 support. We don't need HTTP/2.
        cmd_params.append('--no-http2')
        # Allow server to re-use responses for particular requests (default is
        # to pop responses from the replay queue after the first matching
        # request).
        cmd_params.append('--no-pop')
        # Set up local port to listen for connections.
        cmd_params.append('--port=%d' % self._listen_port)
        # Run in reverse proxy mode, but the original hostname no longer
        # matters, so we set it to a garbage value and signal to ignore the
        # hostname.
        cmd_params.append('--reverse=http://ignored.ignored')
        cmd_params.append('--replay-ignore-host')
        # Specify the mitmdump file to replay.
        cmd_params.append('--server-replay=%s' % self._replay_filename)
        # Replace references to production mlab-ns in HTTP traffic with a
        # our own fake mlab-ns server.
        mlabns_original = re.escape('mlab-ns.appspot.com')
        mlabns_replaced = re.escape('localhost:%d' % self._mlabns_server.port)
        cmd_params.append('--replace=/~s/%s/%s' % (mlabns_original,
                                                   mlabns_replaced))

        # Start the fake mlab-ns server in a background thread.
        self._mlabns_thread = threading.Thread(
            target=self._mlabns_server.serve_forever)
        self._mlabns_thread.start()

        # Launch mitmdump in a subprocess.
        try:
            self._server_proc = subprocess.Popen(cmd_params,
                                                 stdout=subprocess.PIPE)
        except OSError:
            raise MitmProxyNotInstalledError()

    def close(self):
        """Close the replay server by terminating all background workers.

        Terminates all background processes and threads to shut down the replay
        server. Caller is responsible for calling this method when it is
        finished with a ReplayHTTPServer instance.
        """
        if self._server_proc:
            self._server_proc.kill()
        if self._mlabns_thread:
            self._mlabns_server.shutdown()
            self._mlabns_thread.join()
