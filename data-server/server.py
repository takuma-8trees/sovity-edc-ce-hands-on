"""Local hands-on source/sink; standard library only."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import hashlib
import html

sample = Path('/app/sample.json')
received = Path('/received/latest.bin')

class Handler(BaseHTTPRequestHandler):
    def respond(self, status, content, content_type):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        if self.path == '/sample.json':
            return self.respond(200, sample.read_bytes(), 'application/json')
        if self.path == '/received':
            if not received.exists():
                return self.respond(404, b'No data received yet', 'text/plain')
            return self.respond(200, received.read_bytes(), 'text/plain; charset=utf-8')
        if self.path != '/':
            return self.respond(404, b'Not found', 'text/plain')
        data = received.read_bytes() if received.exists() else None
        body = '<!doctype html><meta charset="utf-8"><title>Consumer received data</title><h1>Consumer received data</h1>'
        if data is None:
            body += '<p>No data received yet. Reload after transfer.</p>'
        else:
            body += '<p>Received bytes: ' + str(len(data)) + '</p>'
            body += '<p>Matches Provider sample: ' + str(data == sample.read_bytes()) + '</p>'
            body += '<p>SHA-256: ' + hashlib.sha256(data).hexdigest() + '</p>'
            body += '<pre>' + html.escape(data.decode('utf-8', errors='replace')) + '</pre>'
        self.respond(200, body.encode(), 'text/html; charset=utf-8')

    def do_POST(self):
        if self.path != '/receive':
            return self.respond(404, b'Not found', 'text/plain')
        try:
            if self.headers.get('Transfer-Encoding', '').lower() == 'chunked':
                chunks = []
                total = 0
                while True:
                    line = self.rfile.readline(128)
                    size = int(line.split(b';', 1)[0].strip(), 16)
                    if size == 0:
                        while self.rfile.readline(8192) not in (b'\r\n', b'\n', b''):
                            pass
                        break
                    total += size
                    if total > 1048576:
                        raise ValueError('Too large')
                    chunk = self.rfile.read(size)
                    if len(chunk) != size or self.rfile.read(2) != b'\r\n':
                        raise ValueError('Invalid chunk')
                    chunks.append(chunk)
                data = b''.join(chunks)
            else:
                size = int(self.headers.get('Content-Length', '0'))
                if not 0 < size <= 1048576:
                    raise ValueError('Invalid length')
                data = self.rfile.read(size)
                if len(data) != size:
                    raise ValueError('Incomplete body')
        except ValueError:
            return self.respond(400, b'Invalid request body (max 1 MiB)', 'text/plain')
        received.write_bytes(data)
        self.respond(200, b'Received', 'text/plain')

ThreadingHTTPServer(('0.0.0.0', 8080), Handler).serve_forever()
