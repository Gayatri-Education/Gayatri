"""Architecture Guard: Ensure active code does not import from legacy (Phase 09).

BUG-ARCH-002: Completely decommission legacy import dependencies.
Enforces zero legacy imports across core/, central_platform/, and app/.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

LEGACY_IMPORT_REGEX = re.compile(r"^\s*(?:from\s+legacy\b|import\s+legacy\b)", re.MULTILINE)


def test_central_platform_zero_legacy_imports():
    """Assert that central_platform has zero imports from legacy."""
    cp_dir = ROOT / "central_platform"
    assert cp_dir.exists()

    violations = []
    for py_file in cp_dir.rglob("*.py"):
        content = py_file.read_text(encoding="utf-8", errors="ignore")
        if LEGACY_IMPORT_REGEX.search(content):
            violations.append(str(py_file.relative_to(ROOT)))

    assert not violations, f"Found legacy imports in central_platform: {violations}"


def test_zero_legacy_imports_in_active_codebase():
    """Assert that core, central_platform, and app have zero imports from legacy.

    Decommissioning completed in Phase 09 (BUG-ARCH-002).
    """
    all_legacy_callers = set()
    for directory in [ROOT / "core", ROOT / "central_platform", ROOT / "app"]:
        if not directory.exists():
            continue
        for py_file in directory.rglob("*.py"):
            content = py_file.read_text(encoding="utf-8", errors="ignore")
            if LEGACY_IMPORT_REGEX.search(content):
                rel = str(py_file.relative_to(ROOT)).replace("\\", "/")
                all_legacy_callers.add(rel)

    assert not all_legacy_callers, f"Forbidden legacy imports found in active codebase: {all_legacy_callers}"


def test_legacy_guard_negative_synthetic_detection():
    """Negative test: verify that synthetic legacy import is detected."""
    synthetic_line = "from legacy.agents.default_agents import _local_chat_stream"
    assert LEGACY_IMPORT_REGEX.search(synthetic_line) is not None


def test_legacy_directory_eliminated():
    """Phase 20 Guard: Assert that legacy/ directory has been completely deleted."""
    legacy_dir = ROOT / "legacy"
    assert not legacy_dir.exists(), f"legacy directory still exists on disk: {legacy_dir}"

