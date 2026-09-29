from __future__ import annotations

import json
from typing import Any

from app.services.hash_service import calculate_sha256


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def canonical_hash(value: Any) -> str:
    return calculate_sha256(__import__("io").BytesIO(canonical_json(value).encode("utf-8")))
