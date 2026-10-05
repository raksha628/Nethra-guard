"""Append-only hash chain for assurance runs.

current_hash = SHA256(canonical_json(entry_without_current_hash) + previous_hash)
The first entry's previous hash is 64 zero characters. Verification recomputes
every link and reports the first broken sequence. Tamper tests must use a copy.
"""

from __future__ import annotations

from typing import Any

from .hashing import canonical_json, sha256_text
from .schemas import LedgerEntry, LedgerVerification

GENESIS_HASH = "0" * 64


def entry_payload(entry: LedgerEntry) -> dict[str, Any]:
    return {
        "actorLabel": entry.actor_label,
        "baselineRunId": entry.baseline_run_id,
        "configHash": entry.config_hash,
        "datasetHash": entry.dataset_hash,
        "modelHash": entry.model_hash,
        "previousHash": entry.previous_hash,
        "runId": entry.run_id,
        "sequence": entry.sequence,
        "summaryHash": entry.summary_hash,
        "timestamp": entry.timestamp,
    }


def compute_entry_hash(payload: dict[str, Any], previous_hash: str) -> str:
    return sha256_text(canonical_json(payload) + previous_hash)


def append_entry(
    ledger: list[LedgerEntry],
    *,
    run_id: str,
    timestamp: str,
    dataset_hash: str,
    model_hash: str,
    config_hash: str,
    summary_hash: str,
    actor_label: str = "local-demo",
    baseline_run_id: str | None = None,
) -> LedgerEntry:
    previous = ledger[-1].current_hash if ledger else GENESIS_HASH
    sequence = len(ledger) + 1
    draft = LedgerEntry(
        sequence=sequence,
        runId=run_id,
        timestamp=timestamp,
        actorLabel=actor_label,
        datasetHash=dataset_hash,
        modelHash=model_hash,
        configHash=config_hash,
        summaryHash=summary_hash,
        previousHash=previous,
        currentHash="",
        baselineRunId=baseline_run_id,
    )
    payload = entry_payload(draft)
    current = compute_entry_hash(payload, previous)
    entry = draft.model_copy(update={"current_hash": current})
    ledger.append(entry)
    return entry


def verify_ledger(entries: list[LedgerEntry]) -> LedgerVerification:
    previous = GENESIS_HASH
    for entry in entries:
        if entry.previous_hash != previous:
            return LedgerVerification(
                status="FAILED",
                firstInvalidSequence=entry.sequence,
                reason="previous hash does not match the prior entry",
            )
        expected = compute_entry_hash(entry_payload(entry), entry.previous_hash)
        if expected != entry.current_hash:
            return LedgerVerification(
                status="FAILED",
                firstInvalidSequence=entry.sequence,
                reason="entry hash does not match the payload",
            )
        previous = entry.current_hash
    return LedgerVerification(status="VALID", firstInvalidSequence=None, reason=None)
