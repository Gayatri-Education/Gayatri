"""Gayatri AI Platform — Parent Privacy & Visibility Policy Subsystem (Phase 34).

Provides authoritative privacy rule enforcement, explicit parent visibility levels,
student data filtering, and access boundaries between parents, students, and institutions.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ParentVisibilityLevel(str, Enum):
    FULL_TRANSPARENCY = "full_transparency"  # Grades, attendance, homework, AI chat history, teacher notes
    SUMMARY_ONLY = "summary_only"            # Aggregate mastery & attendance metrics, no raw chat
    RESTRICTED = "restricted"              # Grades & attendance only, no detailed notes or chats
    BLOCKED = "blocked"                    # Privacy hold (e.g., legal or age threshold restriction)


@dataclass
class StudentPrivacySetting:
    """Explicit privacy settings configured for a student-parent link."""
    student_id: str
    parent_id: str
    visibility_level: ParentVisibilityLevel = ParentVisibilityLevel.FULL_TRANSPARENCY
    allow_chat_history_visibility: bool = False  # By default, private AI chat stays private
    allow_assessment_answers_visibility: bool = True
    allow_teacher_notes_visibility: bool = True
    allow_financial_visibility: bool = True
    updated_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["visibility_level"] = (
            self.visibility_level.value
            if isinstance(self.visibility_level, ParentVisibilityLevel)
            else self.visibility_level
        )
        return d


class PrivacyRulesEngine:
    """Authoritative Privacy Rules Engine enforcing data access boundaries."""

    _policy_store: Dict[str, StudentPrivacySetting] = {}

    @classmethod
    def _make_key(cls, parent_id: str, student_id: str) -> str:
        return f"{parent_id}:{student_id}"

    @classmethod
    def set_privacy_setting(cls, setting: StudentPrivacySetting) -> None:
        key = cls._make_key(setting.parent_id, setting.student_id)
        cls._policy_store[key] = setting

    @classmethod
    def get_privacy_setting(cls, parent_id: str, student_id: str) -> StudentPrivacySetting:
        key = cls._make_key(parent_id, student_id)
        if key in cls._policy_store:
            return cls._policy_store[key]
        # Default policy: Full transparency for academic progress, but private AI chat history
        return StudentPrivacySetting(
            student_id=student_id,
            parent_id=parent_id,
            visibility_level=ParentVisibilityLevel.FULL_TRANSPARENCY,
            allow_chat_history_visibility=False,
            allow_assessment_answers_visibility=True,
            allow_teacher_notes_visibility=True,
            allow_financial_visibility=True,
        )

    @classmethod
    def can_parent_view_chat_history(cls, parent_id: str, student_id: str) -> bool:
        setting = cls.get_privacy_setting(parent_id, student_id)
        if setting.visibility_level in (ParentVisibilityLevel.BLOCKED, ParentVisibilityLevel.RESTRICTED):
            return False
        return setting.allow_chat_history_visibility

    @classmethod
    def can_parent_view_assessment_answers(cls, parent_id: str, student_id: str) -> bool:
        setting = cls.get_privacy_setting(parent_id, student_id)
        if setting.visibility_level in (ParentVisibilityLevel.BLOCKED, ParentVisibilityLevel.RESTRICTED):
            return False
        return setting.allow_assessment_answers_visibility

    @classmethod
    def can_parent_view_teacher_notes(cls, parent_id: str, student_id: str) -> bool:
        setting = cls.get_privacy_setting(parent_id, student_id)
        if setting.visibility_level in (ParentVisibilityLevel.BLOCKED, ParentVisibilityLevel.SUMMARY_ONLY):
            return False
        return setting.allow_teacher_notes_visibility

    @classmethod
    def can_parent_view_financials(cls, parent_id: str, student_id: str) -> bool:
        setting = cls.get_privacy_setting(parent_id, student_id)
        if setting.visibility_level == ParentVisibilityLevel.BLOCKED:
            return False
        return setting.allow_financial_visibility

    @classmethod
    def filter_student_data_for_parent(
        cls,
        parent_id: str,
        student_id: str,
        raw_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Sanitize raw student telemetry/records before serving to parent UI."""
        setting = cls.get_privacy_setting(parent_id, student_id)

        if setting.visibility_level == ParentVisibilityLevel.BLOCKED:
            return {
                "student_id": student_id,
                "status": "access_blocked",
                "message": "Access restricted by institution privacy policy.",
            }

        filtered = {
            "student_id": student_id,
            "overall_mastery": raw_data.get("overall_mastery", 0.0),
            "attendance_pct": raw_data.get("attendance_pct", 100.0),
        }

        if setting.visibility_level != ParentVisibilityLevel.SUMMARY_ONLY:
            if setting.allow_teacher_notes_visibility:
                filtered["teacher_notes"] = raw_data.get("teacher_notes", [])
            if setting.allow_assessment_answers_visibility:
                filtered["assessments"] = raw_data.get("assessments", [])

        if setting.allow_chat_history_visibility:
            filtered["chat_history"] = raw_data.get("chat_history", [])

        if setting.allow_financial_visibility:
            filtered["fee_summary"] = raw_data.get("fee_summary", {})

        return filtered
