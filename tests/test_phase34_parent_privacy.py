"""Phase 34 — Parent Privacy & Visibility Subsystem Unit & Integration Tests.

Verifies:
1. ParentVisibilityLevel enum and StudentPrivacySetting serialization.
2. Default privacy settings (academic visibility active, AI chat history private).
3. Explicit policy overrides (e.g. SUMMARY_ONLY, RESTRICTED, BLOCKED).
4. Boundary checks for chat history, assessment details, teacher notes, and financials.
5. Telemetry data filtering for parent view.
"""

import pytest

from central_platform.privacy.policies import (
    ParentVisibilityLevel,
    PrivacyRulesEngine,
    StudentPrivacySetting,
)


def test_parent_visibility_level_enum_and_setting_defaults():
    setting = StudentPrivacySetting(student_id="s101", parent_id="p202")
    assert setting.visibility_level == ParentVisibilityLevel.FULL_TRANSPARENCY
    assert setting.allow_chat_history_visibility is False  # AI Chat is private by default
    assert setting.allow_assessment_answers_visibility is True

    d = setting.to_dict()
    assert d["visibility_level"] == "full_transparency"


def test_default_privacy_boundary_checks():
    parent_id = "parent_001"
    student_id = "student_001"

    # Default policy checks
    assert PrivacyRulesEngine.can_parent_view_chat_history(parent_id, student_id) is False
    assert PrivacyRulesEngine.can_parent_view_assessment_answers(parent_id, student_id) is True
    assert PrivacyRulesEngine.can_parent_view_teacher_notes(parent_id, student_id) is True
    assert PrivacyRulesEngine.can_parent_view_financials(parent_id, student_id) is True


def test_explicit_policy_overrides():
    parent_id = "parent_002"
    student_id = "student_002"

    # Set custom setting allowing chat history
    setting = StudentPrivacySetting(
        student_id=student_id,
        parent_id=parent_id,
        visibility_level=ParentVisibilityLevel.FULL_TRANSPARENCY,
        allow_chat_history_visibility=True,
    )
    PrivacyRulesEngine.set_privacy_setting(setting)

    assert PrivacyRulesEngine.can_parent_view_chat_history(parent_id, student_id) is True

    # Override with SUMMARY_ONLY
    setting_summary = StudentPrivacySetting(
        student_id=student_id,
        parent_id=parent_id,
        visibility_level=ParentVisibilityLevel.SUMMARY_ONLY,
    )
    PrivacyRulesEngine.set_privacy_setting(setting_summary)

    assert PrivacyRulesEngine.can_parent_view_teacher_notes(parent_id, student_id) is False
    assert PrivacyRulesEngine.can_parent_view_chat_history(parent_id, student_id) is False


def test_data_filtering_for_blocked_and_summary_levels():
    parent_id = "parent_003"
    student_id = "student_003"

    raw_data = {
        "overall_mastery": 88.5,
        "attendance_pct": 95.0,
        "teacher_notes": ["Needs practice in Calculus"],
        "chat_history": ["How do I integrate x^2?"],
        "assessments": [{"title": "Math Quiz", "score": 90}],
        "fee_summary": {"balance_due": 0.0},
    }

    # 1. BLOCKED policy
    blocked_setting = StudentPrivacySetting(
        student_id=student_id,
        parent_id=parent_id,
        visibility_level=ParentVisibilityLevel.BLOCKED,
    )
    PrivacyRulesEngine.set_privacy_setting(blocked_setting)

    filtered_blocked = PrivacyRulesEngine.filter_student_data_for_parent(parent_id, student_id, raw_data)
    assert filtered_blocked["status"] == "access_blocked"
    assert "teacher_notes" not in filtered_blocked

    # 2. SUMMARY_ONLY policy
    summary_setting = StudentPrivacySetting(
        student_id=student_id,
        parent_id=parent_id,
        visibility_level=ParentVisibilityLevel.SUMMARY_ONLY,
    )
    PrivacyRulesEngine.set_privacy_setting(summary_setting)

    filtered_summary = PrivacyRulesEngine.filter_student_data_for_parent(parent_id, student_id, raw_data)
    assert filtered_summary["overall_mastery"] == 88.5
    assert "teacher_notes" not in filtered_summary
    assert "chat_history" not in filtered_summary
