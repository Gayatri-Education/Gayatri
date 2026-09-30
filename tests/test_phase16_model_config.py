"""Tests for Phase 16: Model Manifest & Config Re-Audit (P13-T01 to P13-T03)."""
import json
import pytest
from core.model_fetch.manifest_validator import load_and_validate_manifest, ModelManifestValidationError


def test_root_model_manifest_valid():
    """Test that the root model_manifest.json is valid."""
    data = load_and_validate_manifest("model_manifest.json")
    assert data["model_id"] == "gayatri-chem-qwen2.5-0.5b-v4"
    assert data["context_length"] == 8192
    assert "checksum" in data


def test_missing_manifest_file(tmp_path):
    """Test raising error when manifest file is missing."""
    missing_path = tmp_path / "non_existent_manifest.json"
    with pytest.raises(ModelManifestValidationError, match="not found"):
        load_and_validate_manifest(missing_path)


def test_malformed_json_manifest(tmp_path):
    """Test raising error on malformed JSON content."""
    bad_json_path = tmp_path / "bad_manifest.json"
    bad_json_path.write_text("{invalid_json: true", encoding="utf-8")

    with pytest.raises(ModelManifestValidationError, match="Failed to parse"):
        load_and_validate_manifest(bad_json_path)


def test_missing_required_keys(tmp_path):
    """Test raising error when required manifest keys are missing."""
    incomplete_manifest = {
        "model_id": "gayatri-chem-v4",
        "display_name": "Gayatri Tutor"
        # Missing many keys
    }
    path = tmp_path / "incomplete_manifest.json"
    path.write_text(json.dumps(incomplete_manifest), encoding="utf-8")

    with pytest.raises(ModelManifestValidationError, match="missing required keys"):
        load_and_validate_manifest(path)


def test_invalid_context_length(tmp_path):
    """Test raising error when context_length is non-integer or <= 0."""
    manifest = {
        "model_id": "gayatri-chem-v4",
        "display_name": "Gayatri Tutor",
        "provider": "local",
        "local_path": "models/qwen.gguf",
        "download_source": "https://huggingface.co/something",
        "quantization": "Q4_K_M",
        "context_length": -1,
        "architecture": "Qwen2.5",
        "parameter_count": "0.5B",
        "chat_template": "chatml",
        "capabilities": ["text-generation"],
        "hardware_requirements": "1GB RAM, CPU",
        "language_support": ["en"],
        "version": "v4.0",
        "checksum": "abcdef123456",
        "license": "MIT"
    }
    path = tmp_path / "invalid_context.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ModelManifestValidationError, match="Invalid context_length"):
        load_and_validate_manifest(path)
