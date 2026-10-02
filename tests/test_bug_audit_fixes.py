"""
Regression tests for bugs found by the adversarial code audit.

BUG-PLT-022: db.get_teacher_instructions(only_active=True) — malformed expires_at
             was silently swallowed (except: pass → append) meaning a corrupt
             timestamp caused an EXPIRED instruction to be served as ACTIVE.
             Fix: treat unparseable expires_at as expired (fail-safe, log warning).

BUG-PLT-023: db.get_hierarchical_teacher_instructions(only_active=True) — same
             malformed expires_at silent pass bug in the sibling method.

BUG-PLT-024: TeacherInstructionEngine._is_temporally_valid() — except Exception:
             returned True, making a corrupt timestamp make the instruction
             permanently appear valid.
             Fix: return False on parse error (fail-safe).
"""
import sqlite3
import tempfile
import os
import pytest
from datetime import datetime, timezone, timedelta


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _make_db(tmp_path: str):
    from central_platform.db import PlatformDatabase
    db = PlatformDatabase(db_path=os.path.join(tmp_path, "audit_fix.db"))
    return db


def _insert_raw_instruction(db_path: str, instruction_id: str, expires_at, is_active: int = 1):
    """Directly insert a teacher instruction row bypassing Python layer to inject bad data."""
    conn = sqlite3.connect(db_path)
    conn.execute("""
        INSERT INTO teacher_instructions (
            id, teacher_id, student_id, course_id, instruction_text,
            concept_scope, priority, is_active, organization_id,
            course_version_id, class_id, session_id, scope_type,
            status, safety_status, start_at, expires_at,
            version, audit_trail_json, created_at, updated_at
        ) VALUES (
            ?, 'teacher-1', 'all', 'course-1', 'Test instruction',
            'ALL', 3, ?, NULL,
            NULL, NULL, NULL, 'COURSE',
            'active', 'validated', NULL, ?,
            1, '[]', '2025-01-01T00:00:00+00:00', '2025-01-01T00:00:00+00:00'
        )
    """, (instruction_id, is_active, expires_at))
    conn.commit()
    conn.close()


# ──────────────────────────────────────────────────────────────────────────────
# BUG-PLT-022: get_teacher_instructions malformed expires_at
# ──────────────────────────────────────────────────────────────────────────────

class TestBugPLT022GetTeacherInstructionsMalformedExpiry:

    def test_malformed_expires_at_treated_as_expired(self, tmp_path):
        """A corrupted expires_at timestamp must NOT cause the instruction to be served."""
        db = _make_db(str(tmp_path))
        db_path = os.path.join(str(tmp_path), "audit_fix.db")

        # Insert instruction with a malformed (unparseable) expires_at
        _insert_raw_instruction(db_path, "inst-bad-expire", "NOT_A_DATE_!!!!")

        results = db.get_teacher_instructions(course_id="course-1", only_active=True)
        ids = [r.id for r in results]
        assert "inst-bad-expire" not in ids, (
            "BUG-PLT-022 REGRESSION: malformed expires_at instruction was served as active"
        )

    def test_valid_future_expires_at_is_served(self, tmp_path):
        """A valid future expires_at must still be served."""
        db = _make_db(str(tmp_path))
        db_path = os.path.join(str(tmp_path), "audit_fix.db")

        future = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
        _insert_raw_instruction(db_path, "inst-valid-future", future)

        results = db.get_teacher_instructions(course_id="course-1", only_active=True)
        ids = [r.id for r in results]
        assert "inst-valid-future" in ids, "Valid future expiry instruction should be served"

    def test_past_expires_at_not_served(self, tmp_path):
        """A valid past expires_at must NOT be served."""
        db = _make_db(str(tmp_path))
        db_path = os.path.join(str(tmp_path), "audit_fix.db")

        past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        _insert_raw_instruction(db_path, "inst-valid-past", past)

        results = db.get_teacher_instructions(course_id="course-1", only_active=True)
        ids = [r.id for r in results]
        assert "inst-valid-past" not in ids, "Expired instruction should not be served"

    def test_null_expires_at_is_served(self, tmp_path):
        """An instruction with no expires_at (NULL) must be served indefinitely."""
        db = _make_db(str(tmp_path))
        db_path = os.path.join(str(tmp_path), "audit_fix.db")

        _insert_raw_instruction(db_path, "inst-no-expiry", None)  # NULL expires_at

        results = db.get_teacher_instructions(course_id="course-1", only_active=True)
        ids = [r.id for r in results]
        assert "inst-no-expiry" in ids, "No-expiry instruction should be served indefinitely"


# ──────────────────────────────────────────────────────────────────────────────
# BUG-PLT-023: get_hierarchical_teacher_instructions malformed expires_at
# ──────────────────────────────────────────────────────────────────────────────

class TestBugPLT023HierarchicalMalformedExpiry:

    def test_malformed_expires_at_treated_as_expired_hierarchical(self, tmp_path):
        """Same fix in get_hierarchical_teacher_instructions."""
        db = _make_db(str(tmp_path))
        db_path = os.path.join(str(tmp_path), "audit_fix.db")

        _insert_raw_instruction(db_path, "hier-bad-expire", "¡CORRUPT_DATE!")

        results = db.get_hierarchical_teacher_instructions(
            course_id="course-1", only_active=True
        )
        ids = [r.id for r in results]
        assert "hier-bad-expire" not in ids, (
            "BUG-PLT-023 REGRESSION: malformed expires_at in hierarchical query was served as active"
        )

    def test_valid_future_hierarchical(self, tmp_path):
        """Valid future expiry served correctly in hierarchical query."""
        db = _make_db(str(tmp_path))
        db_path = os.path.join(str(tmp_path), "audit_fix.db")

        future = (datetime.now(timezone.utc) + timedelta(hours=12)).isoformat()
        _insert_raw_instruction(db_path, "hier-valid-future", future)

        results = db.get_hierarchical_teacher_instructions(
            course_id="course-1", only_active=True
        )
        ids = [r.id for r in results]
        assert "hier-valid-future" in ids


# ──────────────────────────────────────────────────────────────────────────────
# BUG-PLT-024: TeacherInstructionEngine._is_temporally_valid parse error → False
# ──────────────────────────────────────────────────────────────────────────────

class TestBugPLT024TemporalValidityParseError:

    def _make_engine(self):
        from central_platform.teacher.instruction import TeacherInstruction, TeacherInstructionEngine
        engine = TeacherInstructionEngine()
        return engine, TeacherInstruction

    def test_malformed_start_at_returns_false(self):
        """Corrupt start_at must return False (fail-safe) not True."""
        engine, TI = self._make_engine()
        inst = TI(
            instruction_id="ti-bad-start",
            teacher_id="t1",
            course_id="c1",
            instruction_text="test",
            start_at="NOT_A_DATE",
            expires_at=None,
        )
        result = engine._is_temporally_valid(inst, datetime.now(timezone.utc))
        assert result is False, (
            "BUG-PLT-024 REGRESSION: malformed start_at returned True — corrupt timestamp makes instruction always valid"
        )

    def test_malformed_expires_at_returns_false(self):
        """Corrupt expires_at must return False (fail-safe) not True."""
        engine, TI = self._make_engine()
        inst = TI(
            instruction_id="ti-bad-expire",
            teacher_id="t1",
            course_id="c1",
            instruction_text="test",
            start_at=None,
            expires_at="GARBAGE_DATE_STRING",
        )
        result = engine._is_temporally_valid(inst, datetime.now(timezone.utc))
        assert result is False, (
            "BUG-PLT-024 REGRESSION: malformed expires_at returned True — instruction appears permanently valid"
        )

    def test_valid_active_instruction_returns_true(self):
        """A properly formatted active instruction must still return True."""
        engine, TI = self._make_engine()
        past_start = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        future_exp = (datetime.now(timezone.utc) + timedelta(hours=23)).isoformat()
        inst = TI(
            instruction_id="ti-valid",
            teacher_id="t1",
            course_id="c1",
            instruction_text="test",
            start_at=past_start,
            expires_at=future_exp,
        )
        result = engine._is_temporally_valid(inst, datetime.now(timezone.utc))
        assert result is True, "Valid active instruction should pass temporal validity"

    def test_expired_instruction_returns_false(self):
        """An expired instruction must return False."""
        engine, TI = self._make_engine()
        past_exp = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        inst = TI(
            instruction_id="ti-expired",
            teacher_id="t1",
            course_id="c1",
            instruction_text="test",
            start_at=None,
            expires_at=past_exp,
        )
        result = engine._is_temporally_valid(inst, datetime.now(timezone.utc))
        assert result is False, "Expired instruction should return False"

    def test_not_yet_started_returns_false(self):
        """An instruction that hasn't started yet must return False."""
        engine, TI = self._make_engine()
        future_start = (datetime.now(timezone.utc) + timedelta(hours=5)).isoformat()
        inst = TI(
            instruction_id="ti-future",
            teacher_id="t1",
            course_id="c1",
            instruction_text="test",
            start_at=future_start,
            expires_at=None,
        )
        result = engine._is_temporally_valid(inst, datetime.now(timezone.utc))
        assert result is False, "Not-yet-started instruction should return False"
