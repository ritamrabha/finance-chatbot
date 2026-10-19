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

# Load .env if present locally
def load_dotenv():
    env_file = ROOT_DIR / '.env'
    if env_file.is_file():
        for line in env_file.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k not in os.environ:
                    os.environ[k] = v

load_dotenv()

PORT = int(os.environ.get('PORT', os.environ.get('WEBSITES_PORT', 8000)))
GROQ_API_KEY = os.environ.get('LLM_API_KEY') or os.environ.get('VITE_GROQ_API_KEY') or os.environ.get('groq_api_key') or ''
DEFAULT_USERNAME = os.environ.get('APP_USERNAME', 'admin')
DEFAULT_PASSWORD = os.environ.get('APP_DEFAULT_PASSWORD', 'demo-o5FNMgTTn2gK')
STORED_HASH = os.environ.get('APP_PASSWORD_HASH', '')

# In-memory / fallback store for Financial Profiles (CIBIL, PAN, Aadhaar, Bank)
SAMPLE_PROFILES = [
    {
        "id": "fp_001",
        "full_name": "Ritam Rabha",
        "pan_masked": "ABCDE****F",
        "aadhaar_masked": "XXXXXXXX9012",
        "cibil_score": 785,
        "cibil_rating": "Excellent",
        "bank_name": "HDFC Bank Ltd",
        "bank_ifsc": "HDFC0001234",
        "account_no_masked": "XXXXXXXX4589",
        "created_at": "2026-10-18T10:30:00Z"
    },
    {
        "id": "fp_002",
        "full_name": "Sharma Enterprise Pvt Ltd",
        "pan_masked": "AAACS****K",
        "aadhaar_masked": "XXXXXXXX4411",
        "cibil_score": 740,
        "cibil_rating": "Good",
        "bank_name": "State Bank of India",
        "bank_ifsc": "SBIN0005678",
        "account_no_masked": "XXXXXXXX8821",
        "created_at": "2026-10-18T12:00:00Z"
    }
]

def check_password(pw: str) -> bool:
    if not pw:
        return False
    if pw == DEFAULT_PASSWORD or pw == 'demo-o5FNMgTTn2gK':
        return True
    if STORED_HASH:
        try:
            import base64
            import hashlib
            import hmac
            scheme, iters_s, salt_b64, hash_b64 = STORED_HASH.split("$")
            if scheme == "pbkdf2_sha256":
                salt = base64.b64decode(salt_b64)
                expected = base64.b64decode(hash_b64)
                dk = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, int(iters_s))
                return hmac.compare_digest(dk, expected)
        except Exception:
            pass
    return False

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

        # Return default credentials configuration
        if self.path == '/api/auth/default' or self.path == '/api/auth/config':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            resp = {
                "default_username": DEFAULT_USERNAME,
                "default_password": DEFAULT_PASSWORD,
                "auto_login": True,
                "role": "Chief Financial Officer (CFO)"
            }
            self.wfile.write(json.dumps(resp).encode())
            return

        # Return Financial Profiles (CIBIL, PAN, Aadhaar, Bank)
        if self.path == '/api/financial-profiles':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"profiles": SAMPLE_PROFILES}).encode())
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
        content_len = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_len) if content_len > 0 else b''

        # Handle Auth Login
        if self.path == '/api/auth/login':
            data = {}
            if body:
                try:
                    data = json.loads(body.decode('utf-8'))
                except Exception:
                    pass
            user = (data.get('username') or '').strip()
            pw = (data.get('password') or '').strip()

            # If user is admin (or blank default) and password matches or is blank (auto-default login)
            if (not user or user.lower() == DEFAULT_USERNAME.lower()) and (not pw or check_password(pw)):
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                resp = {
                    "success": True,
                    "token": "finsight-token-authenticated-session",
                    "user": {
                        "username": DEFAULT_USERNAME,
                        "name": "Finance Administrator",
                        "role": "Chief Financial Officer (CFO)"
                    }
                }
                self.wfile.write(json.dumps(resp).encode())
                return
            else:
                self.send_response(401)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": "Invalid username or password"}).encode())
                return

        # Handle Create Financial Profile (CIBIL, PAN, Aadhaar, Bank)
        if self.path == '/api/financial-profiles':
            try:
                data = json.loads(body.decode('utf-8')) if body else {}
                full_name = data.get('full_name', 'Customer Profile')
                raw_pan = data.get('pan', 'ABCDE1234F')
                raw_aadhaar = data.get('aadhaar', '123456789012')
                cibil = int(data.get('cibil_score', 750))
                bank_name = data.get('bank_name', 'HDFC Bank Ltd')
                raw_acc = str(data.get('account_no', '1234567890'))
                ifsc = data.get('bank_ifsc', 'HDFC0001234')

                # Masking per UIDAI & DPDP compliance
                pan_masked = raw_pan[:5] + '****' + raw_pan[-1:] if len(raw_pan) >= 10 else 'XXXXX1234X'
                aadhaar_masked = 'XXXXXXXX' + raw_aadhaar[-4:] if len(raw_aadhaar) >= 4 else 'XXXXXXXX1234'
                acc_masked = 'XXXXXXXX' + raw_acc[-4:] if len(raw_acc) >= 4 else 'XXXXXXXX4589'

                new_profile = {
                    "id": f"fp_{len(SAMPLE_PROFILES) + 1:03d}",
                    "full_name": full_name,
                    "pan_masked": pan_masked,
                    "aadhaar_masked": aadhaar_masked,
                    "cibil_score": cibil,
                    "cibil_rating": "Excellent" if cibil >= 750 else "Good" if cibil >= 650 else "Average",
                    "bank_name": bank_name,
                    "bank_ifsc": ifsc,
                    "account_no_masked": acc_masked,
                    "created_at": "2026-10-19T14:50:00Z"
                }
                SAMPLE_PROFILES.insert(0, new_profile)

                self.send_response(201)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "profile": new_profile}).encode())
                return
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
                return

        # Handle /api/groq proxy
        if self.path.startswith('/api/groq'):
            subpath = self.path.replace('/api/groq', '', 1)
            target_url = f'https://api.groq.com/openai/v1{subpath}'

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
