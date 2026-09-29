from pathlib import Path

from app.services.hash_service import calculate_sha256


def test_sha256_matches_known_digest(tmp_path: Path) -> None:
    path = tmp_path / "sample.bin"
    path.write_bytes(b"NETRA-Guard")
    assert calculate_sha256(path) == "31292fd8f2e5066ca3672c726d4c9f61ff9eb3308de264a908989aa3003e83ab"
