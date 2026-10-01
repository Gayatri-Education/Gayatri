"""Architecture Guard: Ensure generic course and platform modules do not contain Chemistry coupling."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

CHEM_KEYWORDS = [
    r"\bchemistry\b",
    r"\bthermodynamics\b",
    r"\bhess\b",
    r"\bchemical\b",
    r"\bcrs-chem-101\b",
    r"\bchem_101\b",
]
CHEM_REGEX = re.compile("|".join(CHEM_KEYWORDS), re.IGNORECASE)


def scan_file_for_chemistry(file_path: Path) -> list[str]:
    """Scan a file and return matching lines containing Chemistry keywords."""
    matches = []
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        for idx, line in enumerate(f, 1):
            if line.strip().startswith("#"):
                continue  # Ignore comments
            if CHEM_REGEX.search(line):
                matches.append(f"Line {idx}: {line.strip()}")
    return matches


def test_courses_domain_zero_chemistry_coupling():
    """Verify that central_platform/courses contains zero Chemistry references."""
    courses_dir = ROOT / "central_platform" / "courses"
    if not courses_dir.exists():
        return

    violations = {}
    for py_file in courses_dir.glob("*.py"):
        matches = scan_file_for_chemistry(py_file)
        if matches:
            violations[py_file.name] = matches

    assert not violations, f"Found Chemistry coupling in central_platform/courses: {violations}"


def test_architecture_guard_negative_synthetic_detection():
    """Negative test: verify that the scanner detects intentional synthetic Chemistry keywords."""
    synthetic_code = """
    def calculate_reaction():
        import chemistry
        return 'crs-chem-101'
    """
    matches = [line for line in synthetic_code.splitlines() if CHEM_REGEX.search(line)]
    assert len(matches) >= 2, "Scanner failed to detect synthetic Chemistry keywords."
