from pydantic import BaseModel


class DemoWorkspaceAsset(BaseModel):
    asset_id: str
    type: str
    original_name: str
    format: str
    size: int
    sha256: str
    created_at: str


class DemoWorkspaceResponse(BaseModel):
    workspace_id: str
    name: str
    description: str
    offline: bool
    instructions: list[str]
    asset_types: list[str]
    dataset: DemoWorkspaceAsset | None = None
    model: DemoWorkspaceAsset | None = None
