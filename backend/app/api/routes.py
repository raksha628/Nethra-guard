from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db.database import get_db
from app.db.models import Asset, Evidence, Finding, LedgerEntry, Run, Workspace
from app.schemas.assets import AssetResponse, ModelBaselineRequest, ModelBaselineResponse, WorkspaceResponse
from app.schemas.common import AssetType
from app.schemas.demo import DemoWorkspaceAsset, DemoWorkspaceResponse
from app.schemas.runs import EvidenceResponse, FindingResponse, RunCreateRequest, RunDetailResponse, RunResponse
from app.services.asset_service import register_asset
from app.services.data_integrity import profile_summary, run_data_integrity
from app.services.hash_service import calculate_sha256
from app.services.model_integrity import run_model_integrity
from app.services.distribution_shift import run_distribution_shift
from app.services.canonical import canonical_hash
from app.services.comparator import compare_runs
from app.services.ledger import append_run_entry, verify_ledger
from app.services.report import build_report
from app.services.demo_workspace import ensure_demo_assets

router = APIRouter(prefix="/api")
DbSession = Annotated[Session, Depends(get_db)]


def get_or_create_demo_workspace(db: Session) -> Workspace:
    workspace = db.scalar(select(Workspace).where(Workspace.name == "default-ws-01"))
    if workspace is None:
        workspace = Workspace(name="default-ws-01", metadata_json=json.dumps({"kind": "local_demo", "offline": True}))
        db.add(workspace)
        db.commit()
        db.refresh(workspace)
    return workspace


@router.get("/health")
def health() -> dict[str, object]:
    return {"status": "ok", "version": settings.version, "service": settings.app_name, "offline": True}

import mimetypes
from fastapi.responses import FileResponse

@router.get("/assets/{asset_id}/image/{filename:path}")
def get_evidence_image(asset_id: str, filename: str, db: DbSession):
    if ".." in filename or filename.startswith("/") or filename.startswith("\\"):
        raise HTTPException(status_code=400, detail="Path traversal forbidden")
    
    # We resolve the dataset directory from the asset logic
    # The SIH prototype defines ds_coco128 and ds_demo_01.
    if asset_id == "ds_coco128":
        base_dir = settings.workspace_root / "model_evaluation" / "images"
    elif asset_id == "ds_demo_01" or asset_id == "ds_synthetic":
        base_dir = settings.workspace_root / "synthetic_cv" / "images"
    else:
        # Fallback to the generic database asset lookup if we registered it properly
        asset = db.get(Asset, asset_id)
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        base_dir = Path(asset.safe_path).parent / "images"
    
    file_path = base_dir / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
        
    mime_type, _ = mimetypes.guess_type(file_path.name)
    return FileResponse(file_path, media_type=mime_type or "image/jpeg")


@router.get("/demo/workspace", response_model=DemoWorkspaceResponse)
def demo_workspace(db: DbSession) -> DemoWorkspaceResponse:
    workspace = get_or_create_demo_workspace(db)
    dataset, model = ensure_demo_assets(db, workspace)
    return DemoWorkspaceResponse(
        workspace_id=workspace.id,
        name=workspace.name,
        description="A local workspace for safe NETRA-Guard prototype asset registration.",
        offline=True,
        instructions=["A bundled COCO ZIP dataset and model artifact are registered locally.", "Uploaded files are hashed and stored under controlled local directories."],
        asset_types=[AssetType.DATASET.value, AssetType.MODEL.value],
        dataset=DemoWorkspaceAsset(asset_id=dataset.id, type=dataset.type, original_name=dataset.original_name, format=dataset.format, size=dataset.size_bytes, sha256=dataset.sha256, created_at=dataset.created_at.isoformat()),
        model=DemoWorkspaceAsset(asset_id=model.id, type=model.type, original_name=model.original_name, format=model.format, size=model.size_bytes, sha256=model.sha256, created_at=model.created_at.isoformat()),
    )


@router.get("/workspace", response_model=WorkspaceResponse)
def workspace(db: DbSession) -> WorkspaceResponse:
    item = get_or_create_demo_workspace(db)
    return WorkspaceResponse(id=item.id, name=item.name, created_at=item.created_at, asset_count=len(item.assets), metadata=json.loads(item.metadata_json), baseline_model_asset_id=item.baseline_model_asset_id, baseline_model_sha256=item.baseline_model_sha256)


@router.post("/workspace/baseline-model", response_model=ModelBaselineResponse)
def set_baseline_model(request: ModelBaselineRequest, db: DbSession) -> ModelBaselineResponse:
    workspace = db.get(Workspace, request.workspace_id) if request.workspace_id else get_or_create_demo_workspace(db)
    asset = db.get(Asset, request.asset_id)
    if workspace is None or asset is None or asset.workspace_id != workspace.id:
        raise HTTPException(status_code=404, detail="Workspace or model asset not found")
    if asset.type != AssetType.MODEL.value:
        raise HTTPException(status_code=400, detail="Only model assets can be registered as a model baseline")
    workspace.baseline_model_asset_id = asset.id
    workspace.baseline_model_sha256 = asset.sha256
    db.commit()
    return ModelBaselineResponse(workspace_id=workspace.id, asset_id=asset.id, sha256=asset.sha256, message="Model registered as the workspace baseline. A later hash difference indicates artifact change, not malicious tampering.")


@router.get("/workspace/baseline-model", response_model=ModelBaselineResponse | None)
def get_baseline_model(db: DbSession) -> ModelBaselineResponse | None:
    workspace = get_or_create_demo_workspace(db)
    if not workspace.baseline_model_asset_id or not workspace.baseline_model_sha256:
        return None
    return ModelBaselineResponse(workspace_id=workspace.id, asset_id=workspace.baseline_model_asset_id, sha256=workspace.baseline_model_sha256, message="Registered model baseline")


@router.post("/assets", response_model=AssetResponse, status_code=201)
def create_asset(
    db: DbSession,
    file: Annotated[UploadFile, File(...)],
    asset_type: Annotated[AssetType, Form(alias="type")],
    workspace_id: Annotated[str | None, Form()] = None,
) -> AssetResponse:
    item = db.get(Workspace, workspace_id) if workspace_id else get_or_create_demo_workspace(db)
    if item is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return register_asset(db, file, asset_type, item)


def create_fixed_asset(asset_type: AssetType):
    def endpoint(
        db: DbSession,
        file: Annotated[UploadFile, File(...)],
        workspace_id: Annotated[str | None, Form()] = None,
    ) -> AssetResponse:
        item = db.get(Workspace, workspace_id) if workspace_id else get_or_create_demo_workspace(db)
        if item is None:
            raise HTTPException(status_code=404, detail="Workspace not found")
        return register_asset(db, file, asset_type, item)

    return endpoint


router.add_api_route("/assets/dataset", create_fixed_asset(AssetType.DATASET), methods=["POST"], response_model=AssetResponse, status_code=201)
router.add_api_route("/assets/model", create_fixed_asset(AssetType.MODEL), methods=["POST"], response_model=AssetResponse, status_code=201)


def _asset_path(asset: Asset) -> Path:
    root = settings.workspace_root.resolve()
    path = (root / asset.safe_path).resolve()
    if path.parent == root or root not in path.parents or not path.is_file():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Registered asset file is unavailable")
    return path


def _run_status(findings: list[Finding]) -> str:
    if any(finding.severity == "CRITICAL" for finding in findings):
        return "FAIL"
    if any(finding.severity == "WARNING" for finding in findings):
        return "WARNING"
    return "PASS"


def _finding_response(finding: Finding) -> FindingResponse:
    details = json.loads(finding.details_json or "{}")
    return FindingResponse(
        id=finding.id,
        run_id=finding.run_id,
        category=finding.category,
        severity=finding.severity,
        status=finding.status,
        title=finding.title,
        description=finding.description,
        method=finding.method,
        observed_value=finding.observed_value,
        threshold=finding.threshold,
        confidence_note=finding.confidence_note,
        limitations=finding.limitations,
        evidence_refs=details.get("evidence_refs", []),
        affected_asset=details.get("affected_asset", ""),
        affected_sample=finding.affected_sample,
        remediation=finding.remediation,
        created_at=finding.created_at,
    )


def _run_response(db: Session, run: Run) -> RunResponse:
    summary = json.loads(run.summary_json or "{}")
    findings = db.scalars(select(Finding).where(Finding.run_id == run.id)).all()
    return RunResponse(
        id=run.id,
        workspace_id=run.workspace_id,
        dataset_asset_id=run.dataset_asset_id,
        reference_dataset_asset_id=run.reference_dataset_asset_id,
        current_dataset_asset_id=run.current_dataset_asset_id,
        model_asset_id=run.model_asset_id,
        state=run.state,
        created_at=run.created_at,
        completed_at=run.completed_at,
        selected_checks=json.loads(run.configuration_json or "{}").get("checks", []),
        summary=summary,
        configuration=json.loads(run.configuration_json or "{}").get("configuration", {}),
        findings_count=len(findings),
        status=summary.get("status", "NOT_RUN"),
    )


@router.post("/runs", response_model=RunResponse, status_code=201)
def create_run(request: RunCreateRequest, db: DbSession) -> RunResponse:
    workspace = db.get(Workspace, request.workspace_id) if request.workspace_id else get_or_create_demo_workspace(db)
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    dataset_id = request.dataset_asset_id or request.asset_id
    selected_checks = [value.upper() for value in request.checks]
    data_selected = "DATA_INTEGRITY" in selected_checks or "CHK_DATA" in selected_checks
    model_selected = "MODEL_INTEGRITY" in selected_checks or "CHK_MODEL" in selected_checks
    shift_selected = "DISTRIBUTION_SHIFT" in selected_checks or "CHK_SHIFT" in selected_checks
    comparator_selected = "COMPARATOR" in selected_checks or "CHK_COMP" in selected_checks
    reference_id = request.reference_dataset_asset_id or dataset_id
    current_id = request.current_dataset_asset_id or dataset_id or reference_id
    dataset = db.get(Asset, reference_id) if reference_id else db.scalar(select(Asset).where(Asset.workspace_id == workspace.id, Asset.type == AssetType.DATASET.value).order_by(Asset.created_at.desc()))
    current_dataset = db.get(Asset, current_id) if current_id else dataset
    if data_selected and (dataset is None or dataset.workspace_id != workspace.id or dataset.type != AssetType.DATASET.value):
        raise HTTPException(status_code=400, detail="A registered dataset asset is required")
    if shift_selected and (dataset is None or current_dataset is None or current_dataset.workspace_id != workspace.id or current_dataset.type != AssetType.DATASET.value):
        raise HTTPException(status_code=400, detail="Reference and current dataset assets are required")
    model_id = request.model_asset_id
    model = db.get(Asset, model_id) if model_id else db.scalar(select(Asset).where(Asset.workspace_id == workspace.id, Asset.type == AssetType.MODEL.value).order_by(Asset.created_at.desc()))
    if model_selected and (model is None or model.workspace_id != workspace.id or model.type != AssetType.MODEL.value):
        raise HTTPException(status_code=400, detail="A registered model asset is required")
    run = Run(
        id=f"run_{uuid4().hex}",
        workspace_id=workspace.id,
        dataset_asset_id=dataset.id if dataset else None,
        reference_dataset_asset_id=dataset.id if dataset else None,
        current_dataset_asset_id=current_dataset.id if current_dataset else None,
        model_asset_id=model.id if model else None,
        state="CONFIGURED",
        configuration_hash=canonical_hash({"checks": selected_checks, "configuration": request.configuration}),
        configuration_json=json.dumps({"checks": selected_checks, "configuration": request.configuration}),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    run.state = "RUNNING"
    db.commit()

    try:
        profile = None
        generated = []
        model_summary = None
        model_generated = []
        shift_summary = None
        shift_generated = []
        check_statuses = {"DATA_INTEGRITY": "NOT_RUN", "MODEL_INTEGRITY": "NOT_RUN", "DISTRIBUTION_SHIFT": "NOT_RUN", "COMPARATOR": "NOT_RUN"}
        if data_selected and dataset:
            profile, generated = run_data_integrity(_asset_path(dataset), run.id, request.configuration)
            check_statuses["DATA_INTEGRITY"] = "PASS" if len(generated) == 1 and generated[0].severity == "INFO" else "WARNING" if not any(item.severity == "CRITICAL" for item in generated) else "FAIL"
        if model_selected and model:
            baseline_asset = db.get(Asset, workspace.baseline_model_asset_id) if workspace.baseline_model_asset_id else None
            baseline_path = _asset_path(baseline_asset) if baseline_asset else None
            model_summary, model_generated = run_model_integrity(model, _asset_path(model), baseline_asset, baseline_path, workspace, request.configuration)
            
            from app.config import MODEL_EVALUATION_DATASET
            from app.services.model_evaluation import evaluate_model_behaviour
            eval_summary = evaluate_model_behaviour(_asset_path(model), MODEL_EVALUATION_DATASET)
            model_summary["semantic_evaluation"] = eval_summary.metrics["semantic"]
            
            check_statuses["MODEL_INTEGRITY"] = "WARNING" if model_generated else "PASS"
        if shift_selected and dataset and current_dataset:
            shift_summary, shift_finding = run_distribution_shift(_asset_path(dataset), _asset_path(current_dataset), request.configuration, dataset.original_name, current_dataset.original_name)
            check_statuses["DISTRIBUTION_SHIFT"] = shift_summary["status"]
            if shift_finding:
                shift_generated = [shift_finding]
        persisted: list[Finding] = []
        for item in [*generated, *model_generated, *shift_generated]:
            item_category = getattr(item, "category", "DATA_INTEGRITY")
            item_asset = dataset if item_category == "DATA_INTEGRITY" and dataset else model if item_category == "MODEL_INTEGRITY" and model else current_dataset
            finding = Finding(
                id=f"finding_{uuid4().hex}",
                run_id=run.id,
                asset_id=item_asset.id if item_asset else None,
                category=item_category,
                severity=item.severity,
                status=item.status,
                title=item.title,
                description=item.description,
                method=item.method,
                observed_value=item.observed_value,
                threshold=item.threshold,
                confidence_note=item.confidence_note,
                limitations=item.limitations,
                remediation=item.remediation,
                affected_sample=item.affected_sample,
                details_json=json.dumps({"affected_asset": item_asset.original_name if item_asset else "", "evidence_refs": []}),
            )
            db.add(finding)
            db.flush()
            refs: list[str] = []
            for evidence_item in item.evidence:
                evidence = Evidence(
                    id=f"evidence_{uuid4().hex}",
                    finding_id=finding.id,
                    sample_id=evidence_item.sample_id,
                    metric=evidence_item.metric,
                    expected_value=evidence_item.expected_value,
                    observed_value=evidence_item.observed_value,
                    reference=evidence_item.reference,
                    asset_reference=item_asset.id if item_asset else "",
                    details_json=json.dumps(getattr(evidence_item, "details", {})),
                )
                db.add(evidence)
                refs.append(evidence.id)
            finding.details_json = json.dumps({"affected_asset": item_asset.original_name if item_asset else "", "evidence_refs": refs})
            persisted.append(finding)
        comparison = None
        if comparator_selected:
            previous = db.scalar(select(Run).where(Run.workspace_id == workspace.id, Run.id != run.id, Run.state == "COMPLETED").order_by(Run.created_at.desc()))
            if previous:
                comparison = compare_runs(db, previous, run)
                meaningful = [item for item in comparison["finding_changes"] if item["type"] in {"NEW", "CLEARED", "STATUS_CHANGE"}]
                check_statuses["COMPARATOR"] = "WARNING" if meaningful or comparison.get("model_hash_changed") else "PASS"
            else:
                check_statuses["COMPARATOR"] = "NOT_RUN"
        status_value = _run_status(persisted)
        if status_value == "PASS" and not data_selected and not model_selected and (not shift_selected or check_statuses["DISTRIBUTION_SHIFT"] == "NOT_RUN") and check_statuses["COMPARATOR"] == "NOT_RUN":
            status_value = "NOT_RUN"
        if check_statuses["COMPARATOR"] == "WARNING" and status_value == "PASS":
            status_value = "WARNING"
        run.state = "COMPLETED"
        run.completed_at = datetime.now(timezone.utc)
        summary: dict[str, object] = {"status": status_value, "checks": check_statuses}
        if profile is not None:
            summary["profile"] = profile_summary(profile, request.configuration)
        if model_summary is not None:
            summary["model"] = model_summary
        if shift_summary is not None:
            summary["distribution_shift"] = shift_summary
        if comparison is not None:
            summary["comparator"] = comparison
        run.summary_json = json.dumps(summary)
        db.commit()
        append_run_entry(db, run)
    except HTTPException as exc:
        run.state = "FAILED"
        run.completed_at = datetime.now(timezone.utc)
        run.summary_json = json.dumps({"status": "FAIL", "error": str(exc.detail), "checks": {"DATA_INTEGRITY": "FAIL"}})
        db.commit()
        raise
    except Exception as exc:
        run.state = "FAILED"
        run.completed_at = datetime.now(timezone.utc)
        run.summary_json = json.dumps({"status": "FAIL", "error": f"{exc.__class__.__name__}: {exc}", "checks": {"DATA_INTEGRITY": "FAIL"}})
        db.commit()
        return _run_response(db, run)
    return _run_response(db, run)


@router.get("/runs", response_model=list[RunResponse])
def list_runs(db: DbSession) -> list[RunResponse]:
    return [_run_response(db, run) for run in db.scalars(select(Run).order_by(Run.created_at.desc())).all()]


@router.get("/runs/{run_id}", response_model=RunDetailResponse)
def get_run(run_id: str, db: DbSession) -> RunDetailResponse:
    run = db.get(Run, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    response = _run_response(db, run)
    return RunDetailResponse(**response.model_dump(), findings=[_finding_response(item) for item in db.scalars(select(Finding).where(Finding.run_id == run.id)).all()])


@router.get("/runs/{run_id}/findings", response_model=list[FindingResponse])
def get_findings(run_id: str, db: DbSession) -> list[FindingResponse]:
    if db.get(Run, run_id) is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return [_finding_response(item) for item in db.scalars(select(Finding).where(Finding.run_id == run_id).order_by(Finding.created_at)).all()]


@router.get("/runs/{run_id}/evidence", response_model=list[EvidenceResponse])
def get_evidence(run_id: str, db: DbSession) -> list[EvidenceResponse]:
    if db.get(Run, run_id) is None:
        raise HTTPException(status_code=404, detail="Run not found")
    query = select(Evidence).join(Finding, Evidence.finding_id == Finding.id).where(Finding.run_id == run_id)
    return [EvidenceResponse(id=item.id, finding_id=item.finding_id, sample_id=item.sample_id, metric=item.metric, expected_value=item.expected_value, observed_value=item.observed_value, reference=item.reference, asset_reference=item.asset_reference, details=json.loads(item.details_json or "{}")) for item in db.scalars(query).all()]


@router.get("/runs/{run_id}/evidence/{evidence_id}", response_model=EvidenceResponse)
def get_evidence_item(run_id: str, evidence_id: str, db: DbSession) -> EvidenceResponse:
    run = db.get(Run, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    item = db.get(Evidence, evidence_id)
    finding = db.get(Finding, item.finding_id) if item else None
    if item is None or finding is None or finding.run_id != run_id:
        raise HTTPException(status_code=404, detail="Evidence not found")

    details = json.loads(item.details_json or "{}")
    
    # 1. Provide Provenance info
    model = db.get(Asset, run.model_asset_id) if run.model_asset_id else None
    dataset = db.get(Asset, item.asset_reference) if item.asset_reference else None
    if not dataset and run.current_dataset_asset_id:
        dataset = db.get(Asset, run.current_dataset_asset_id)

    details["provenance"] = {
        "finding": finding.title,
        "evidence": item.metric,
        "dataset": dataset.original_name if dataset else item.asset_reference,
        "model": model.original_name if model else "N/A",
        "run": run_id
    }

    # 2. Extract Predictions & Ground Truth for the single image if possible
    details["predictions"] = []
    details["ground_truth"] = []
    
    try:
        if dataset and model and item.sample_id:
            dataset_path = Path(dataset.safe_path).parent if dataset.type == "DATASET" else settings.workspace_root / "model_evaluation"
            if dataset.id == "ds_coco128":
                dataset_path = settings.workspace_root / "model_evaluation"
            elif dataset.id == "ds_demo_01" or dataset.id == "ds_synthetic":
                dataset_path = settings.workspace_root / "synthetic_cv"

            # Parse COCO GT
            ann_path = dataset_path / "annotations" / "instances.json"
            if ann_path.exists():
                with open(ann_path, "r") as f:
                    coco = json.load(f)
                img = next((i for i in coco.get("images", []) if i["file_name"] == item.sample_id), None)
                if img:
                    cats = {c["id"]: c["name"] for c in coco.get("categories", [])}
                    anns = [a for a in coco.get("annotations", []) if a["image_id"] == img["id"]]
                    for a in anns:
                        x, y, w, h = a["bbox"]
                        details["ground_truth"].append({
                            "class": cats.get(a["category_id"], "unknown"),
                            "bbox": [x, y, x + w, y + h]
                        })

            # Get Model Predictions
            from app.services.model_adapter import select_adapter, EvaluationSample
            model_path = Path(model.safe_path)
            if model_path.exists():
                adapter = select_adapter(model_path)
                adapter.load(model_path)
                sample = EvaluationSample(sample_id=item.sample_id)
                preds = adapter.run_inference([sample], dataset_images_path=dataset_path / "images")
                for p in preds:
                    details["predictions"].append({
                        "class": p.class_name,
                        "confidence": p.confidence,
                        "bbox": p.bbox
                    })
    except Exception as e:
        import logging
        logging.error(f"Failed to load image dynamic predictions: {e}")

    return EvidenceResponse(
        id=item.id,
        finding_id=item.finding_id,
        sample_id=item.sample_id,
        metric=item.metric,
        expected_value=item.expected_value,
        observed_value=item.observed_value,
        reference=item.reference,
        asset_reference=item.asset_reference,
        details=details
    )


@router.get("/runs/{run_id}/compare")
def compare_run(run_id: str, baseline_run_id: str, db: DbSession) -> dict[str, object]:
    current = db.get(Run, run_id)
    baseline = db.get(Run, baseline_run_id)
    if current is None or baseline is None:
        raise HTTPException(status_code=404, detail="Baseline or current run not found")
    return compare_runs(db, baseline, current)


@router.get("/runs/{run_id}/report")
def run_report(run_id: str, db: DbSession, baseline_run_id: str | None = None) -> dict[str, object]:
    run = db.get(Run, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    comparator = None
    if baseline_run_id:
        baseline = db.get(Run, baseline_run_id)
        if baseline is None:
            raise HTTPException(status_code=404, detail="Baseline run not found")
        comparator = compare_runs(db, baseline, run)
    report, report_hash = build_report(db, run, comparator)
    return {"report": report, "report_hash": report_hash}


@router.get("/ledger")
def get_ledger(db: DbSession) -> dict[str, object]:
    entries = db.scalars(select(LedgerEntry).order_by(LedgerEntry.sequence)).all()
    return {"entries": [{"sequence": item.sequence, "run_id": item.run_id, "timestamp": item.timestamp, "previous_hash": item.previous_hash, "current_hash": item.current_hash, "dataset_hash": item.dataset_hash, "model_hash": item.model_hash, "config_hash": item.config_hash, "summary_hash": item.summary_hash, "actor_label": item.actor_label} for item in entries], "verification": verify_ledger(db)}


@router.post("/ledger/verify")
def verify_ledger_endpoint(db: DbSession) -> dict[str, object]:
    return verify_ledger(db)
