import pytest
from pathlib import Path
from app.services.model_adapter import select_adapter, ONNXModelAdapter, DeterministicFallbackAdapter

def test_adapter_selection(tmp_path):
    pt_path = tmp_path / "model.pt"
    pt_path.touch()
    
    onnx_path = tmp_path / "model.onnx"
    onnx_path.touch()
    
    assert isinstance(select_adapter(pt_path), DeterministicFallbackAdapter)
    assert isinstance(select_adapter(onnx_path), ONNXModelAdapter)

def test_invalid_onnx_validation(tmp_path):
    onnx_path = tmp_path / "corrupt.onnx"
    onnx_path.write_bytes(b"not a valid onnx file")
    
    adapter = select_adapter(onnx_path)
    assert isinstance(adapter, ONNXModelAdapter)
    
    errors = adapter.validate(onnx_path)
    assert len(errors) > 0
    assert "Invalid ONNX model format" in errors[0]

def test_empty_onnx_validation(tmp_path):
    onnx_path = tmp_path / "empty.onnx"
    onnx_path.touch()
    
    adapter = select_adapter(onnx_path)
    errors = adapter.validate(onnx_path)
    assert len(errors) == 1
    assert errors[0] == "model file is empty"
