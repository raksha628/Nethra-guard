from __future__ import annotations

import hashlib
from pathlib import Path
from typing import BinaryIO

_CHUNK_SIZE = 1024 * 1024


def calculate_sha256(source: str | Path | BinaryIO) -> str:
    digest = hashlib.sha256()
    if hasattr(source, "read"):
        stream = source
        try:
            stream.seek(0)
        except (AttributeError, OSError):
            pass
        while chunk := stream.read(_CHUNK_SIZE):
            digest.update(chunk)
        return digest.hexdigest()

    with Path(source).open("rb") as stream:
        while chunk := stream.read(_CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()
