#!/usr/bin/env python3
import json
import os
import datetime
from http.server import SimpleHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

STORAGE_FILE = 'tracking_events.jsonl'
PORT = 8000

class TrackingHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != '/track':
            self.send_error(404, 'Not Found')
            return

        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)

        try:
            data = json.loads(body.decode('utf-8'))
        except json.JSONDecodeError:
            self.send_error(400, 'Invalid JSON')
            return

        event = {
            'received_at': datetime.datetime.utcnow().isoformat() + 'Z',
            'source_ip': self.client_address[0],
            'user_agent': self.headers.get('User-Agent'),
            'event': data.get('event'),
            'page': data.get('page'),
            'metadata': data.get('metadata', {}),
            'client_timestamp': data.get('timestamp'),
        }

        with open(STORAGE_FILE, 'a', encoding='utf-8') as storage:
            storage.write(json.dumps(event, ensure_ascii=False) + '\n')

        self.send_response(204)
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == '/events':
            self.send_events_page()
            return
        return super().do_GET()

    def send_events_page(self):
        events = []
        if os.path.exists(STORAGE_FILE):
            with open(STORAGE_FILE, 'r', encoding='utf-8') as storage:
                for line in storage:
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

        rows = []
        for event in reversed(events[-100:]):
            rows.append(
                '<tr>'
                f'<td>{event.get("received_at","")}</td>'
                f'<td>{event.get("source_ip","")}</td>'
                f'<td>{event.get("event","")}</td>'
                f'<td>{event.get("page","")}</td>'
                f'<td>{json.dumps(event.get("metadata", {}), ensure_ascii=False)}</td>'
                '</tr>'
            )

        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Tracking events</title>
  <style>
    body {{ font-family: Arial, sans-serif; background: #f7f7f7; color: #111; padding: 2rem; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 1rem; }}
    th, td {{ border: 1px solid #ddd; padding: 0.75rem; text-align: left; vertical-align: top; }}
    th {{ background: #eee; }}
    pre {{ white-space: pre-wrap; word-break: break-word; margin: 0; }}
    a {{ color: #c0392b; text-decoration: none; }}
  </style>
</head>
<body>
  <h1>Tracking events</h1>
  <p>This page shows the latest events recorded by the tracking backend.</p>
  <p><a href="/amm.html">Open AMM page</a> · <a href="/">Home</a></p>
  <table>
    <thead>
      <tr><th>Received</th><th>IP</th><th>Event</th><th>Page</th><th>Metadata</th></tr>
    </thead>
    <tbody>
      {''.join(rows)}
    </tbody>
  </table>
</body>
</html>'''

        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))


def run(server_class=HTTPServer, handler_class=TrackingHandler):
    os.makedirs(os.path.dirname(STORAGE_FILE) or '.', exist_ok=True)
    if not os.path.exists(STORAGE_FILE):
        open(STORAGE_FILE, 'a', encoding='utf-8').close()

    server_address = ('', PORT)
    httpd = server_class(server_address, handler_class)
    print(f'Serving site at http://localhost:{PORT}/')
    print('Tracking endpoint: http://localhost:{PORT}/track')
    print('Events page: http://localhost:{PORT}/events')
    httpd.serve_forever()


if __name__ == '__main__':
    run()
