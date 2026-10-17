"""Create a password hash for APP_PASSWORD_HASH.

    python scripts/hash_password.py

You type the password (it is not shown); paste the printed hash into .env
(locally) or into Key Vault (on Azure). The plain password is never stored.
"""
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.security import hash_password  # noqa: E402

pw = getpass.getpass("New app password: ")
if len(pw) < 10:
    sys.exit("Use at least 10 characters.")
if pw != getpass.getpass("Repeat password: "):
    sys.exit("Passwords did not match.")
print("\nAPP_PASSWORD_HASH=" + hash_password(pw))
