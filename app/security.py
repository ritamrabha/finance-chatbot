"""Security helpers: upload validation and password checking."""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import re
from dataclasses import dataclass

from app.config import settings

ALLOWED_EXT = {"pdf", "png", "jpg", "jpeg"}
# "Magic bytes": the first bytes of a real file of each type. Checking them
# stops someone renaming malware.exe to invoice.pdf.
MAGIC = {
    "pdf": [b"%PDF-"],
    "png": [b"\x89PNG\r\n\x1a\n"],
    "jpg": [b"\xff\xd8\xff"],
    "jpeg": [b"\xff\xd8\xff"],
}


@dataclass
class UploadCheck:
    ok: bool
    reason: str
    ext: str = ""
    sha256: str = ""
    safe_name: str = ""


def validate_upload(filename: str, data: bytes) -> UploadCheck:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXT:
        return UploadCheck(False, "Only PDF, PNG or JPG files are allowed.")
    if len(data) == 0:
        return UploadCheck(False, "The file is empty.")
    size_mb = len(data) / (1024 * 1024)
    if size_mb > settings.max_upload_mb:
        return UploadCheck(False, f"File is {size_mb:.1f} MB; the limit is {settings.max_upload_mb} MB.")
    if not any(data.startswith(sig) for sig in MAGIC[ext]):
        return UploadCheck(False, "The file contents don't match its extension.")
    if ext == "pdf" and (b"/JavaScript" in data or b"/Launch" in data):
        return UploadCheck(False, "PDFs with embedded scripts are not accepted.")
    safe = re.sub(r"[^A-Za-z0-9._ -]", "_", os.path.basename(filename))[:120]
    return UploadCheck(True, "OK", ext, hashlib.sha256(data).hexdigest(), safe)


# ---- Passwords: PBKDF2-SHA256 (built into Python, no extra library) --------
ITERATIONS = 310_000


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS)
    return f"pbkdf2_sha256${ITERATIONS}${base64.b64encode(salt).decode()}${base64.b64encode(dk).decode()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, iters, salt_b64, hash_b64 = stored.split("$")
        if algo != "pbkdf2_sha256":
            return False
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), base64.b64decode(salt_b64), int(iters))
        return hmac.compare_digest(dk, base64.b64decode(hash_b64))  # constant-time comparison
    except Exception:
        return False


def check_login(username: str, password: str) -> bool:
    if not settings.app_password_hash:
        return False
    user_ok = hmac.compare_digest(username.strip().lower(), settings.app_username.lower())
    return verify_password(password, settings.app_password_hash) and user_ok
