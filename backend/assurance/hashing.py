"""SHA-256 helpers and canonical JSON used by fingerprints and the ledger."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 64), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json(payload: Mapping[str, Any]) -> str:
    """Stable JSON: sorted keys, no insignificant whitespace, UTF-8 text."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
