#!/usr/bin/env bash
# Direct HTTP smoke test. This does not replace the EDC UI transfer check.
set -euo pipefail
cd "$(dirname "$0")/.."
docker compose exec -T provider-data-server python - <<'PY'
import hashlib
import re
import time
import urllib.request as http
from urllib.error import HTTPError, URLError

source = 'http://provider-data-server:8080'
sink = 'http://consumer-data-server:8080'

def get(url):
    with http.urlopen(url, timeout=5) as response:
        return response.read()

def expect_error(request, status):
    try:
        http.urlopen(request, timeout=5)
    except HTTPError as error:
        assert error.code == status, (error.code, status)
    else:
        raise AssertionError(f'Expected HTTP {status}')

for attempt in range(30):
    try:
        get(source + '/'); get(sink + '/')
        break
    except URLError:
        if attempt == 29:
            raise
        time.sleep(1)

data = get(source + '/sample.json')
expect_error(sink + '/sample.json', 404)
expect_error(http.Request(source + '/receive', data=b'x'), 405)
expect_error(http.Request(sink + '/receive', data=b''), 400)
changed = b'{"message":"Different data"}\n'
with http.urlopen(http.Request(sink + '/receive', data=changed), timeout=5):
    pass
assert hashlib.sha256(changed).hexdigest() in get(sink + '/').decode()
assert hashlib.sha256(data).hexdigest() not in get(sink + '/').decode()
assert get(source + '/sample.json') == data
for chunked in (False, True):
    body = iter([data[:17], data[17:]]) if chunked else data
    with http.urlopen(http.Request(sink + '/receive', data=body), timeout=5) as response:
        assert response.status == 200
    assert get(sink + '/received') == data
    for endpoint in (source, sink):
        page = get(endpoint + '/').decode()
        assert hashlib.sha256(data).hexdigest() == re.search(r'SHA-256: ([0-9a-f]{64})', page)[1]
        assert 'Hello from Provider' in page
print('PASS: separate roles, Content-Length/chunked POST, received bytes and both SHA-256 values')
print('NOTE: Consumer now contains data sent directly by this smoke test, not through EDC.')
PY
