"""File storage: Azure Blob Storage if configured, otherwise a local folder.

Files are stored under a name we generate (date + content hash), never the
user's original filename, so a crafted filename like '../../app.py' can't
overwrite anything.
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.config import settings

CONTENT_TYPES = {"pdf": "application/pdf", "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}


def save_file(data: bytes, sha256: str, ext: str) -> str:
    """Store the file and return its storage path (blob name or local path)."""
    name = f"{datetime.now(timezone.utc):%Y/%m}/{sha256[:32]}.{ext}"
    if settings.use_blob:
        from azure.storage.blob import BlobServiceClient, ContentSettings

        service = BlobServiceClient.from_connection_string(settings.storage_conn_str)
        container = service.get_container_client(settings.storage_container)
        if not container.exists():
            container.create_container()  # private by default: no public access
        container.upload_blob(name, data, overwrite=True,
                              content_settings=ContentSettings(content_type=CONTENT_TYPES.get(ext)))
        return f"blob://{settings.storage_container}/{name}"
    path = settings.local_upload_dir / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return f"local://{name}"
