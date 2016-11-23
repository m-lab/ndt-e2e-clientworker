# NDT Client HTTP Replay Generator

## Overview

The HTTP replay generator is an HTTP proxy that saves HTTP request and response
information and processes it so that all requests made during a capture session
can be reproduced with a single web server replaying the replay file.

Specifically, the replay generator:

* Saves the relative URL (path) of each HTTP request and its corresponding
  HTTP response information.
* Replaces all domains found in the traffic with the IP address `127.0.0.1` to
  facilitate local playback.
* Decompresses all gzipped HTTP responses

## Replay file

The generator creates an HTTP replay file, which is a simple YAML file
containing a dictionary or relative URLs mapped to their corresponding HTTP
response information. All response data is decompressed and saved with UTF-8
encoding.

## Domain replacement

The replay generator replaces remote domains with the localhost address to
facilitate local replays. For example, if we capture requests to the following
URLs

* http://foo.com/abc
* http://bar.com/def

The replay generator will create a replay file that allows us to replay the
traffic locally so that the responses are available via a local server like:

* http://127.0.0.1/abc
* http://127.0.0.1/def

To do this, we need to replace references to `href`s to actual domains with
`127.0.0.1` in HTTP response data, so the replay generator processes the
responses to replace these references.

For example a request to http://example.com/welcome with the response:

```html
<html><body><a href="example.com/bar">Go to Bar!</a></body></html>
```
would be saved as:

```html
<html><body><a href="127.0.0.1/bar">Go to Bar!</a></body></html>
```

## Limitations

* Replay generator does not preserve any information about relative ordering of
  requests.
* Replay generator can only save one response per relative URL.
  * If the captured traffic includes requests to different URLs with the same
    relative path (e.g. http://foo.com/abc and http://bar.com/abc) we only save
    the most recent response for a given relative path.
* Replay generator only captures traffic for HTTP `GET` requests.
* Domain replacement is a very naïve string replacement
  * Domains may be replaced if they're just text and not actual `href`s
  * We will fail to replace domains if they're constructed dynamically in
    JavaScript, like

      ```javascript
      var url = 'performance' + '.example.com';
      ```

## Example

This example assumes you've cloned this repository and installed all requirements using ```pip install -i requirements.txt```

To capture traffic for an NDT client at http://www.example.com/foo/ndt:

1. Configure Firefox to use a manually set HTTP proxy at address 127.0.0.1 on
   port 8888.

   * Open the Firefox GUI and go to Edit > Preferences > Advanced > Network
   * Under **Connection**, click the _Settings_ button, select _Manual proxy configuration_, enter _127.0.0.1_ for **HTTP Proxy** and _8888_ for **Port**, and in the box labeled **No Proxy for** add _localhost, 127.0.0.1, measurement-lab.org_
   * Click **Ok** and then close the Firefox GUI

1. Open a terminal window and start the replay generator:
    ```bash
    python replay_generator/replay_generator.py \
      --port 8888 \
      --output example.com-replay.yaml
    ```

1. Then open a second terminal window and run Firefox in private mode against the target client URL:
    ```bash
    firefox -private http://www.example.com/foo/ndt
    ```
  A FireFox window should open and should load the test URL.

1. Run the NDT client in the Firefox browser window for a single test until the test is complete.
1. When the test has completed, return to the first terminal window running the replay generator, and type ```Ctrl+C``` to stop capturing traffic and save output.

The output file `example.com-replay.yaml` can then be used as the
`--client_path` parameter to `client_wrapper` to replay the HTTP traffic
locally.

### OneBox Example
To capture traffic for the Google OneBox client, follow the same instructions as
above, but when launching Firefox use this target URL instead:
```
http://www.google.com/search?q=internet+speed+test&ie=utf-8&oe=utf-8
```

NOTE: Google Search generally forces HTTPS. However, the simple HTTP proxy
provided by replay_generator.py only supports HTTP. When loading the above URL
into Firefox (through the proxy), it for some reason works unencrypted. Getting
this replay generation to work in Chrome has so far been unsuccessful, but it
may be unnecessary as long as it continues to work with Firefox.
