"""Production HTTP server for Azure App Service.
Serves the Vue.js SPA frontend (dist/), handles SPA routing,
and proxies Groq AI requests securely using the server's API key.
"""
import http.server
import json
import mimetypes
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

# Ensure mime types are registered
mimetypes.add_type('application/wasm', '.wasm')
mimetypes.add_type('application/javascript', '.js')
mimetypes.add_type('text/css', '.css')

ROOT_DIR = Path(__file__).resolve().parent
DIST_DIR = ROOT_DIR / 'dist'

PORT = int(os.environ.get('PORT', os.environ.get('WEBSITES_PORT', 8000)))
GROQ_API_KEY = os.environ.get('LLM_API_KEY') or os.environ.get('VITE_GROQ_API_KEY') or os.environ.get('groq_api_key') or ''

class ProductionHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIST_DIR), **kwargs)

    def end_headers(self):
        # Enable CORS for local dev / client flexibility
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
            return

        # Check if the requested file exists in dist
        rel_path = self.path.split('?')[0].lstrip('/')
        file_path = DIST_DIR / rel_path

        if rel_path and file_path.is_file():
            return super().do_GET()

        # SPA routing fallback: serve index.html for all page routes
        index_path = DIST_DIR / 'index.html'
        if index_path.is_file():
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(index_path.read_bytes())
            return

        super().do_GET()

    def do_POST(self):
        # Handle /api/groq proxy
        if self.path.startswith('/api/groq'):
            subpath = self.path.replace('/api/groq', '', 1)
            target_url = f'https://api.groq.com/openai/v1{subpath}'

            content_len = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_len) if content_len > 0 else b''

            # Check authorization header or use server key
            auth_header = self.headers.get('Authorization') or f'Bearer {GROQ_API_KEY}'

            req = urllib.request.Request(
                target_url,
                data=body,
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': auth_header,
                    'User-Agent': 'FinSight-AI/1.0'
                },
                method='POST'
            )

            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    resp_body = resp.read()
                    self.send_response(resp.status)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(resp_body)
            except urllib.error.HTTPError as e:
                err_body = e.read()
                self.send_response(e.code)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(err_body)
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode())
            return

        self.send_response(404)
        self.end_headers()

def run():
    print(f"FinSight AI production server starting on port {PORT}...")
    print(f"Serving static assets from: {DIST_DIR}")
    server_address = ('0.0.0.0', PORT)
    httpd = http.server.HTTPServer(server_address, ProductionHandler)
    print(f"Server live at http://0.0.0.0:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        httpd.server_close()

if __name__ == '__main__':
    run()
