from assurance.hashing import canonical_json, sha256_text
from assurance.ledger import GENESIS_HASH, append_entry, compute_entry_hash, entry_payload, verify_ledger
from assurance.scenarios import HANDOFF_TIMESTAMP, run_scenario


def test_canonical_json_and_sha256_are_stable():
    assert canonical_json({"b": 1, "a": 2}) == '{"a":2,"b":1}'
    assert sha256_text("abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_intact_chain_verifies_and_tampered_copy_fails():
    ledger = []
    run_scenario("NONE", ledger=ledger, timestamp=HANDOFF_TIMESTAMP)
    run_scenario("DATA_ANOMALY", ledger=ledger, timestamp="2026-01-01T00:00:01Z")
    assert verify_ledger(ledger).status == "VALID"
    assert ledger[0].previous_hash == GENESIS_HASH
    assert ledger[1].previous_hash == ledger[0].current_hash
    assert compute_entry_hash(entry_payload(ledger[0]), ledger[0].previous_hash) == ledger[0].current_hash

    tampered = [entry.model_copy(deep=True) for entry in ledger]
    tampered[1].dataset_hash = "0" * 64
    result = verify_ledger(tampered)
    assert result.status == "FAILED"
    assert result.first_invalid_sequence == 2
    assert verify_ledger(ledger).status == "VALID"


def test_append_uses_the_spec_formula():
    ledger = []
    entry = append_entry(
        ledger,
        run_id="RUN-TEST-001",
        timestamp=HANDOFF_TIMESTAMP,
        dataset_hash="a" * 64,
        model_hash="b" * 64,
        config_hash="c" * 64,
        summary_hash="d" * 64,
    )
    payload = entry_payload(entry)
    assert "currentHash" not in payload
    assert entry.current_hash == sha256_text(canonical_json(payload) + entry.previous_hash)
