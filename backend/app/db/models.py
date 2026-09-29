from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(default=utc_now, nullable=False)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    baseline_model_asset_id: Mapped[str | None] = mapped_column(String(64), index=True)
    baseline_model_sha256: Mapped[str | None] = mapped_column(String(64))
    assets: Mapped[list[Asset]] = relationship(back_populates="workspace", cascade="all, delete-orphan", foreign_keys="Asset.workspace_id")


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid4()))
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    safe_path: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    format: Mapped[str] = mapped_column(String(32), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(default=utc_now, nullable=False)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    workspace: Mapped[Workspace] = relationship(back_populates="assets", foreign_keys=[workspace_id])


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid4()))
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(32), default="NOT_RUN", nullable=False)
    dataset_asset_id: Mapped[str | None] = mapped_column(ForeignKey("assets.id"), index=True)
    reference_dataset_asset_id: Mapped[str | None] = mapped_column(ForeignKey("assets.id"), index=True)
    current_dataset_asset_id: Mapped[str | None] = mapped_column(ForeignKey("assets.id"), index=True)
    model_asset_id: Mapped[str | None] = mapped_column(ForeignKey("assets.id"), index=True)
    configuration_hash: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(default=utc_now, nullable=False)
    completed_at: Mapped[datetime | None]
    configuration_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    summary_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)


class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid4()))
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"), nullable=False, index=True)
    asset_id: Mapped[str | None] = mapped_column(ForeignKey("assets.id"), index=True)
    category: Mapped[str] = mapped_column(String(64), default="DATA_INTEGRITY", nullable=False)
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    method: Mapped[str] = mapped_column(Text, default="", nullable=False)
    observed_value: Mapped[str] = mapped_column(Text, default="", nullable=False)
    threshold: Mapped[str] = mapped_column(Text, default="", nullable=False)
    confidence_note: Mapped[str] = mapped_column(Text, default="", nullable=False)
    limitations: Mapped[str] = mapped_column(Text, default="", nullable=False)
    remediation: Mapped[str] = mapped_column(Text, default="", nullable=False)
    affected_sample: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(default=utc_now, nullable=False)
    details_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid4()))
    sequence: Mapped[int] = mapped_column(Integer, nullable=False, unique=True, index=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id"), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(default=utc_now, nullable=False)
    actor_label: Mapped[str] = mapped_column(String(128), nullable=False)
    dataset_hash: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    model_hash: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    config_hash: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    summary_hash: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    previous_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    current_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    entry_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=utc_now, nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid4()))
    finding_id: Mapped[str] = mapped_column(ForeignKey("findings.id"), nullable=False, index=True)
    sample_id: Mapped[str] = mapped_column(String(255), nullable=False)
    metric: Mapped[str] = mapped_column(String(128), nullable=False)
    expected_value: Mapped[str | None] = mapped_column(Text)
    observed_value: Mapped[str | None] = mapped_column(Text)
    reference: Mapped[str | None] = mapped_column(String(128))
    asset_reference: Mapped[str | None] = mapped_column(String(255))
    details_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
