import json
from pathlib import Path

from assurance.hashing import sha256_file
from assurance.model_integrity import HASH_MISMATCH_LIMITATION, HASH_MISMATCH_TITLE, check_model
from assurance.schemas import ModuleStatus

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
MODELS = FIXTURES / "models"


def _manifest() -> dict:
    return json.loads((FIXTURES / "baseline_manifest.json").read_text(encoding="utf-8"))


def test_baseline_model_matches():
    result = check_model(
        MODELS / "baseline_model.bin",
        baseline_sha256=_manifest()["model_hash"],
        allowed_root=MODELS,
    )
    assert result.status == ModuleStatus.PASS
    assert result.findings == []
    assert result.metrics["sha256"] == _manifest()["model_hash"]
    assert result.metrics["weights_loaded"] is False
    assert result.metrics["metadata"] == {}


def test_altered_model_reports_full_hashes():
    current = sha256_file(MODELS / "altered_model.bin")
    baseline = _manifest()["model_hash"]
    result = check_model(
        MODELS / "altered_model.bin",
        baseline_sha256=baseline,
        allowed_root=MODELS,
    )
    assert result.status == ModuleStatus.FAIL
    assert len(result.findings) == 1
    finding = result.findings[0]
    assert finding.title == HASH_MISMATCH_TITLE
    assert finding.observed_value == current
    assert finding.threshold == baseline
    assert finding.observed_value != finding.threshold
    assert "malicious tampering" in finding.limitations
    assert finding.limitations == HASH_MISMATCH_LIMITATION


def test_missing_baseline_is_not_a_pass(tmp_path: Path):
    model = tmp_path / "model.bin"
    model.write_bytes(b"standalone")
    result = check_model(model, baseline_sha256=None, allowed_root=tmp_path)
    assert result.status == ModuleStatus.NOT_RUN
    assert result.status != ModuleStatus.PASS
    assert result.metrics["sha256"] == sha256_file(model)


def test_missing_file_fails(tmp_path: Path):
    result = check_model(tmp_path / "missing.bin", baseline_sha256="ab" * 32, allowed_root=tmp_path)
    assert result.status == ModuleStatus.FAIL
    assert result.findings[0].title == "Model artifact is unreadable"


def test_path_outside_root_is_rejected(tmp_path: Path):
    root = tmp_path / "models"
    root.mkdir()
    outside = tmp_path / "outside.bin"
    outside.write_bytes(b"do-not-read-me")
    outside_hash = sha256_file(outside)
    result = check_model(outside, baseline_sha256="ab" * 32, allowed_root=root)
    assert result.status == ModuleStatus.FAIL
    assert result.findings[0].title == "Model path is not allowed"
    assert outside_hash not in json.dumps(result.model_dump(mode="json"))


def test_pickle_bytes_are_not_loaded(tmp_path: Path):
    model = tmp_path / "weights.pkl"
    model.write_bytes(b"not-really-a-pickle")
    digest = sha256_file(model)
    result = check_model(model, baseline_sha256=digest, allowed_root=tmp_path)
    assert result.status == ModuleStatus.PASS
    assert result.metrics["weights_loaded"] is False
    assert result.metrics["load_note"] == "Pickle weights were not deserialized."
