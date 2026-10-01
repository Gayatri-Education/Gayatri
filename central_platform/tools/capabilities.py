"""Gayatri AI Platform — Course Tool Capabilities & Context Models (Phase 08).

Defines:
- ToolCategory: Classification of tool domains (CALCULATION, SCIENCE, CODING, etc.)
- ResourceLimits: Maximum execution time, input/output sizes, and memory usage.
- ToolCapability: Declarative metadata, parameter schemas, and permission rules.
- ToolExecutionContext: Request-time context (course, student, session, role, course policy).
- ToolExecutionResult: Standardized execution response with timing and resource metrics.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from central_platform.models.schema import CourseToolPolicy, UserRole


class ToolCategory(str, Enum):
    CALCULATION = "calculation"
    SCIENCE = "science"
    CODING = "coding"
    GRAPHING = "graphing"
    REFERENCE = "reference"


@dataclass
class ResourceLimits:
    timeout_seconds: float = 5.0
    max_input_chars: int = 10000
    max_output_chars: int = 50000
    max_memory_mb: int = 128

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ToolCapability:
    tool_id: str
    name: str
    description: str
    category: ToolCategory
    allowed_roles: List[UserRole] = field(
        default_factory=lambda: [
            UserRole.STUDENT,
            UserRole.TEACHER,
            UserRole.ORG_ADMIN,
            UserRole.SUPER_ADMIN,
        ]
    )
    resource_limits: ResourceLimits = field(default_factory=ResourceLimits)
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["category"] = self.category.value if isinstance(self.category, ToolCategory) else str(self.category)
        d["allowed_roles"] = [
            r.value if isinstance(r, UserRole) else str(r) for r in self.allowed_roles
        ]
        return d


@dataclass
class ToolExecutionContext:
    course_id: str
    student_id: Optional[str] = None
    session_id: Optional[str] = None
    user_role: UserRole = UserRole.STUDENT
    course_policy: Optional[CourseToolPolicy] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["user_role"] = self.user_role.value if isinstance(self.user_role, UserRole) else str(self.user_role)
        if self.course_policy:
            d["course_policy"] = self.course_policy.to_dict()
        return d


@dataclass
class ToolExecutionResult:
    success: bool
    output: Any = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    resource_usage: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
