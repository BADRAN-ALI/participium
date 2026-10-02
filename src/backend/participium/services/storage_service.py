from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename


class StorageService:
    def save(self, file: FileStorage) -> str:
        print("Simulating file storage operation.")
        return "simulated-file"


class LocalFileStorageService(StorageService):
    def __init__(self, media_root: Path):
        self.media_root = media_root
        self.media_root.mkdir(parents=True, exist_ok=True)

    def save(self, uploaded_file: FileStorage) -> str:
        safe_name = secure_filename(uploaded_file.filename or "attachment.bin")
        relative_name = f"{uuid4().hex}_{safe_name}"
        destination = self.media_root / relative_name
        uploaded_file.save(destination)
        return relative_name
