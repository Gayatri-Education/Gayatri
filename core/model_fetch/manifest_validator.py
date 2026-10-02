"""Model Manifest Validator & Registry Integration (Phase 09 & Phase 13).

Ensures model deployment consistency by validating model_manifest.json
against runtime configuration, schema definitions, and model artifact health.
"""
from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("gayatri.model.validator")

# Core required keys for Phase 13/16 compatibility
REQUIRED_MANIFEST_KEYS = {
    "model_id",
    "display_name",
    "provider",
    "local_path",
    "download_source",
    "quantization",
    "context_length",
    "architecture",
    "parameter_count",
    "chat_template",
    "capabilities",
    "hardware_requirements",
    "language_support",
    "version",
    "checksum",
    "license",
}

# Extended canonical keys required by Phase 09 specification
PHASE09_CANONICAL_KEYS = {
    "artifact_path",
    "format",
    "prompt_template",
    "context_window",
    "streaming",
    "resource_profile",
}


class ModelManifestValidationError(ValueError):
    """Raised when model manifest is missing, malformed, or inconsistent."""
    pass


def load_and_validate_manifest(manifest_path: Path | str | None = None) -> dict[str, Any]:
    """Load model_manifest.json and validate required keys and consistency.

    Supports both original schema and Phase 09 unified canonical fields.
    """
    if manifest_path is None:
        manifest_path = Path("model_manifest.json")
    else:
        manifest_path = Path(manifest_path)

    if not manifest_path.exists():
        raise ModelManifestValidationError(f"Model manifest file not found at '{manifest_path}'.")

    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as e:
        raise ModelManifestValidationError(f"Failed to parse model manifest JSON: {e}")

    # Validate baseline required keys
    missing = REQUIRED_MANIFEST_KEYS - set(data.keys())
    if missing:
        raise ModelManifestValidationError(f"Model manifest is missing required keys: {missing}")

    # Validate context length / window
    ctx_len = data.get("context_length") or data.get("context_window")
    if not isinstance(ctx_len, int) or ctx_len <= 0:
        raise ModelManifestValidationError(f"Invalid context_length in manifest: {data.get('context_length')}")

    # Normalize canonical alias fields if absent
    if "artifact_path" not in data and "local_path" in data:
        data["artifact_path"] = data["local_path"]
    if "prompt_template" not in data and "chat_template" in data:
        data["prompt_template"] = data["chat_template"]
    if "context_window" not in data and "context_length" in data:
        data["context_window"] = data["context_length"]
    if "resource_profile" not in data and "hardware_requirements" in data:
        data["resource_profile"] = data["hardware_requirements"]
    if "format" not in data:
        data["format"] = "gguf"
    if "streaming" not in data:
        data["streaming"] = True

    logger.info(f"Model manifest validated successfully: {data['model_id']} ({data['architecture']})")
    return data


def get_active_manifest() -> dict[str, Any]:
    """Return the active model manifest parsed from root or config location."""
    from core.config import BASE_DIR
    candidates = [
        Path("model_manifest.json"),
        BASE_DIR / "model_manifest.json",
    ]
    for p in candidates:
        if p.exists():
            return load_and_validate_manifest(p)
    return load_and_validate_manifest()


def verify_model_checksum(file_path: Path | str, expected_sha256: str) -> bool:
    """Verify SHA-256 checksum of a model file."""
    p = Path(file_path)
    if not p.is_file():
        return False
    hasher = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest().lower() == expected_sha256.lower()
