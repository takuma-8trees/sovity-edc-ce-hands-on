"""Read-only Provider sample and inspection page; standard library only."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import hashlib
import html

sample = Path('/app/sample.json')


class Handler(BaseHTTPRequestHandler):
    def respond(self, status, content, content_type):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        if self.path not in ('/', '/sample.json'):
            return self.respond(404, b'Not found', 'text/plain')
        data = sample.read_bytes()
        if self.path == '/sample.json':
            return self.respond(200, data, 'application/json')
        body = ('<!doctype html><meta charset="utf-8">'
                '<title>Provider source data</title>'
                '<style>body{font-family:system-ui;margin:32px;max-width:960px}'
                'pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#edf5fb;padding:20px}'
                'p{overflow-wrap:anywhere}</style>'
                '<h1>Provider source data</h1>'
                '<p>Compare this JSON and SHA-256 with the Consumer page '
                '(http://localhost:18080/).</p>'
                f'<p>Source bytes: {len(data)}</p>'
                f'<p>SHA-256: {hashlib.sha256(data).hexdigest()}</p>'
                f'<pre>{html.escape(data.decode("utf-8", errors="replace"))}</pre>')
        self.respond(200, body.encode(), 'text/html; charset=utf-8')

    def do_POST(self):
        self.respond(405, b'Provider is read-only', 'text/plain')


ThreadingHTTPServer(('0.0.0.0', 8080), Handler).serve_forever()
