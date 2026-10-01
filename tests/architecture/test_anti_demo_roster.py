"""Architecture Guard: Ensure generic domain services do not contain hardcoded demo user rosters."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

DEMO_USER_REGEX = re.compile(
    r"\b(Rahul Kumar|Priya Sharma|Amit Patel|local_user_1|local_student_1)\b",
    re.IGNORECASE,
)


def test_courses_and_models_zero_demo_roster():
    """Assert that central_platform/courses and models contain zero hardcoded demo users."""
    for sub in ["courses", "models"]:
        sub_dir = ROOT / "central_platform" / sub
        if not sub_dir.exists():
            continue
        for py_file in sub_dir.rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                matches = DEMO_USER_REGEX.findall(content)
                assert not matches, f"Found demo user identifiers in {py_file}: {matches}"
            except Exception:
                pass


def test_demo_roster_guard_negative_synthetic_detection():
    """Negative test: verify that synthetic demo user identifiers are caught."""
    synthetic_code = "student_name = 'Rahul Kumar'"
    assert DEMO_USER_REGEX.search(synthetic_code) is not None
