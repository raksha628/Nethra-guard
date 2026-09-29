from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class Settings:
    app_name: str = "NETRA-Guard API"
    version: str = os.getenv("NETRA_API_VERSION", "0.1.0")
    workspace_root: Path = Path(os.getenv("NETRA_WORKSPACE_ROOT", str(PROJECT_ROOT / "workspace"))).resolve()
    database_path: Path = Path(os.getenv("NETRA_DATABASE_PATH", str(PROJECT_ROOT / "workspace" / "netra_guard.sqlite3"))).resolve()
    max_upload_size_bytes: int = int(os.getenv("NETRA_MAX_UPLOAD_SIZE_BYTES", str(500 * 1024 * 1024)))
    frontend_origin: str = os.getenv("NETRA_FRONTEND_ORIGIN", "http://localhost:5173")
    bbox_max_aspect_ratio: float = float(os.getenv("NETRA_BBOX_MAX_ASPECT_RATIO", "20"))
    bbox_min_area_ratio: float = float(os.getenv("NETRA_BBOX_MIN_AREA_RATIO", "0.0001"))
    bbox_max_area_ratio: float = float(os.getenv("NETRA_BBOX_MAX_AREA_RATIO", "0.9"))
    model_confidence_delta_threshold: float = float(os.getenv("NETRA_MODEL_CONFIDENCE_DELTA_THRESHOLD", "0.15"))
    model_iou_threshold: float = float(os.getenv("NETRA_MODEL_IOU_THRESHOLD", "0.5"))
    shift_threshold: float = float(os.getenv("NETRA_SHIFT_THRESHOLD", "1.0"))
    shift_min_samples: int = int(os.getenv("NETRA_SHIFT_MIN_SAMPLES", "2"))

    @property
    def allowed_extensions(self) -> dict[str, frozenset[str]]:
        return {
            "DATASET": frozenset({".zip", ".json", ".jsonl", ".csv", ".tar", ".gz", ".parquet"}),
            "MODEL": frozenset({".pt", ".pth", ".onnx", ".torchscript", ".ts", ".safetensors"}),
        }

    @property
    def supported_classes(self) -> frozenset[str]:
        raw = os.getenv("NETRA_SUPPORTED_CLASSES", "")
        return frozenset(value.strip() for value in raw.split(",") if value.strip())

    @property
    def shift_features(self) -> tuple[str, ...]:
        raw = os.getenv("NETRA_SHIFT_FEATURES", "brightness,contrast,rgb_mean,width,height")
        return tuple(value.strip() for value in raw.split(",") if value.strip())

    @property
    def storage_directories(self) -> tuple[Path, ...]:
        return tuple(self.workspace_root / name for name in ("uploads", "datasets", "models", "previews", "reports", "demo"))

    def initialize_directories(self) -> None:
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        for directory in self.storage_directories:
            directory.mkdir(parents=True, exist_ok=True)


settings = Settings()
