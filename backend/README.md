# NETRA-Guard Backend

This directory contains the Phase 1 local FastAPI foundation. Run commands from the repository root so the default workspace remains at `workspace/`:

```bash
python -m pip install -r backend/requirements.txt
python -m uvicorn app.main:app --app-dir backend --reload --port 8000
python -m pytest backend/tests -q
```

Configuration is available through `NETRA_WORKSPACE_ROOT`, `NETRA_DATABASE_PATH`, `NETRA_MAX_UPLOAD_SIZE_BYTES`, `NETRA_API_VERSION`, and `NETRA_FRONTEND_ORIGIN`. Paths are repository-relative by default and uploaded files are never served as static content.