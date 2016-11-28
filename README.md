# NDT End-to-End Client Worker

[![Build
Status](https://travis-ci.org/m-lab/ndt-e2e-clientworker.svg?branch=master)](https://travis-ci.org/m-lab/ndt-e2e-clientworker)
[![Coverage
Status](https://coveralls.io/repos/m-lab/ndt-e2e-clientworker/badge.svg?branch=master&service=github)](https://coveralls.io/github/m-lab/ndt-e2e-clientworker?branch=master)

## Pre-Requisites

To install pre-requisites, run the following command:

```bash
pip install -r requirements.txt
```

## Creating an HTTP replay file

For clients that are difficult to host as static files, the operator must use
the `replay_generator.py` script to capture traffic for the client, then use the
replay filename as the `--client_path` parameter to `client_wrapper`. See
[replay_generator/README.md](replay_generator/README.md) for details on generating a replay file.
