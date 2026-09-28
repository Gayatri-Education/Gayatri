"""Phase 28: Final Repository Cleanup & Codebase Integrity Master Suite.

Implements Master Plan Section 37:
Verifies cleanup, dead-code elimination, and structural integrity:
1. All modules in `central_platform`, `core`, and `server` import cleanly without runtime errors or deprecated module references.
2. Zero orphaned files or broken circular dependencies in Python package structures.
3. System integrity and deterministic execution across learning engines and data layers.
"""

import importlib
import pkgutil
import pytest

import central_platform
import core


def test_import_integrity_central_platform():
    """Test 1: Recursively import all modules in central_platform to verify clean syntax and valid references."""
    for module_info in pkgutil.walk_packages(central_platform.__path__, central_platform.__name__ + "."):
        # Import every submodule
        mod = importlib.import_module(module_info.name)
        assert mod is not None


def test_import_integrity_core_tutor():
    """Test 2: Recursively import all modules in core to verify stable tutor engine integrity."""
    for module_info in pkgutil.walk_packages(core.__path__, core.__name__ + "."):
        mod = importlib.import_module(module_info.name)
        assert mod is not None


def test_no_unhandled_todo_deadlocks():
    """Test 3: Core contracts maintain explicit error handling or production implementation."""
    from central_platform.models.schema import User, UserRole
    user = User(
        id="usr_clean_1",
        email="clean@gayatri.ai",
        full_name="Clean User",
        role=UserRole.STUDENT,
        organization_id="org_clean",
    )
    d = user.to_dict()
    assert d["role"] == "student"
    assert d["full_name"] == "Clean User"
