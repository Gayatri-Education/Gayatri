"""Architecture Guard: Ensure model manifest and configuration integrity."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def test_model_manifest_valid_and_complete():
    """Verify that model_manifest.json contains required metadata keys."""
    manifest_path = ROOT / "model_manifest.json"
    assert manifest_path.exists(), "model_manifest.json is missing."

    content = manifest_path.read_text(encoding="utf-8")
    data = json.loads(content)

    required_keys = [
        "model_id",
        "display_name",
        "provider",
        "local_path",
        "quantization",
        "context_length",
        "capabilities",
    ]
    for key in required_keys:
        assert key in data, f"Missing required key '{key}' in model_manifest.json"


def test_core_config_importable():
    """Verify core/config.py can be loaded without runtime exceptions."""
    from core.config import LOCAL_MODEL_FILE, LOCAL_MODEL_DIR
    assert LOCAL_MODEL_FILE is not None
    assert LOCAL_MODEL_DIR is not None
