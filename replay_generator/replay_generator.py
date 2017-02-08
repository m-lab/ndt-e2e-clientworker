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
"""Utility script to capture HTTP traffic.

Runs an HTTP proxy that captures traffic, modifies it for local replay, then
saves it to an output YAML file. See replay_generator/README.md for additional
details.
"""
import argparse
import BaseHTTPServer
import io
import gzip
import os
import SimpleHTTPServer
import sys
import urllib2
import urlparse
import yaml

sys.path.insert(1, os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..')))

from client_wrapper import http_response


class ResponseSavingHTTPProxy(BaseHTTPServer.HTTPServer):
    """An HTTP proxy that saves a copy of all HTTP responses in memory.

    An HTTP proxy specifically for HTTP GET requests that saves in memory all
    responses received from upstream server.

    Attributes:
        responses: A dictionary where each key is an absolute URL and each value
            is an HttpResponse instance representing the last response received
            for a request to that URL.
    """

    def __init__(self, port):
        """Creates a new ResponseSavingHTTPProxy.

        Args:
            port: The local TCP port to listen on for connections.
        """
        BaseHTTPServer.HTTPServer.__init__(self, ('', port),
                                           ResponseSavingRequestHandler)
        self.responses = {}


class ResponseSavingRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    """An HTTP request handler that saves all responses to its parent server."""

    def do_GET(self):
        """Process an HTTP GET request."""
        # Forward the client's request to the actual server.
        opener = urllib2.build_opener()
        opener.addheaders = self.headers.items()
        response = opener.open(self.path)

        headers = {}
        for header, value in response.info().items():
            headers[header] = value
        # Decompress any gzipped HTTP response back to plaintext.
        if 'content-encoding' in headers and headers[
                'content-encoding'] == 'gzip':
            buf = io.BytesIO(response.read())
            # TODO(mtlynch): Don't assume encoding is ISO-8859-1. Parse it from
            # the appropriate HTTP header.
            data = gzip.GzipFile(
                fileobj=buf).read().decode('iso-8859-1').encode('utf-8')
            headers.pop('content-encoding', None)
        else:
            data = response.read()
        # Don't use the Transfer-Encoding header because it seems to create
        # complexities in modifying and replaying traffic. Instead, use the
        # simpler Content-Length header to indicate the payload size to the
        # client.
        if 'transfer-encoding' in headers:
            headers.pop('transfer-encoding', None)
        headers['content-length'] = len(data)

        # Send the response to the client.
        self.send_response(response.getcode())
        for header, value in headers.iteritems():
            self.send_header(header, value)
        self.end_headers()
        self.wfile.write(data)

        # Save the response.
        self.server.responses[self.path] = http_response.HttpResponse(
            response.getcode(), headers, data)


def _process_responses(original):
    """Processes HTTP responses so that they are replayable locally.

    Processes HTTP responses to build a set of all domains that gave HTTP
    responses, then replaces all references to those domains in the responses
    with the string 127.0.0.1 so that the responses can be replayed locally.

    Args:
        original: A dictionary where each key is an absolute URL and each value
            is an HttpResponse instance.

    Returns:
        A dictionary where each key is a relative URL and each value is an
        HttpResponse instance that has been modified to replace hrefs to remote
        domains with the string 127.0.0.1.
    """
    # Build a set of all domains from the URLs that appear in the responses
    # dictionary.
    domains = set()

    # There are some domains that we want to replace that are not necessarily
    # URLs that will show up as a key in dict 'original' (likely because the
    # request was over HTTPS). In such cases, manually add lines below for
    # additional domains which should be replaced with '127.0.0.1'.
    domains.add('apis.google.com')

    for url in original:
        domains.add(urlparse.urlparse(url).netloc)

    processed = {}
    for url, response in original.iteritems():
        # Convert each absolute URL to a relative URL
        url_parsed = urlparse.urlparse(url)
        relative_url = url_parsed.path
        if url_parsed.query:
            relative_url += '?' + url_parsed.query
        # Replace all the domains in the response with 127.0.0.1 so that the
        # responses can be played back locally.
        data_processed = response.data
        for domain in domains:
            data_processed = data_processed.replace(domain, '127.0.0.1')

        if relative_url in processed:
            print 'warning: multiple responses for relative URL: %s' % relative_url
        processed[relative_url] = http_response.HttpResponse(
            response.response_code, response.headers, data_processed)
    return processed


def main(args):
    proxy_server = ResponseSavingHTTPProxy(args.port)
    print 'response capturing proxy listening on port %d, press Ctrl+C to stop' % args.port
    try:
        proxy_server.serve_forever()
    except KeyboardInterrupt:
        pass
    print 'done collecting HTTP traffic, saving results to %s' % args.output
    with open(args.output, 'w') as output_file:
        output_file.write(yaml.dump(_process_responses(proxy_server.responses)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='HTTP Replay Generator',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--port',
                        help='Port to listen on',
                        type=int,
                        default=8888)
    parser.add_argument('--output',
                        help='Directory in which to write output',
                        required=True)
    main(parser.parse_args())
