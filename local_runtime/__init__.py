"""Offline Local Runtime Package for Gayatri AI.

Provides fully course-independent local runtime capabilities:
- Course package caching and SHA-256 integrity quarantine
- Strictly scoped offline BM25 knowledge search
- Transactional session persistence with crash rollback and restart resilience
- Offline capability detection and honest degraded state reporting
"""

from __future__ import annotations

from local_runtime.course_cache import CoursePackageMetadata, LocalCourseCache
from local_runtime.detector import (
    DegradedStateInfo,
    OfflineCapabilitiesReport,
    OfflineCapabilityDetector,
)
from local_runtime.engine import LocalRuntimeEngine
from local_runtime.errors import (
    CorruptedCacheError,
    ModelUnavailableError,
    OfflineCourseNotCachedError,
    OfflineRuntimeError,
    ReadOnlyDatabaseError,
)
from local_runtime.rag_cache import LocalRAGCache
from local_runtime.session import LocalSessionPersistence

__all__ = [
    "CoursePackageMetadata",
    "LocalCourseCache",
    "LocalRAGCache",
    "LocalSessionPersistence",
    "OfflineCapabilityDetector",
    "OfflineCapabilitiesReport",
    "DegradedStateInfo",
    "LocalRuntimeEngine",
    "OfflineRuntimeError",
    "OfflineCourseNotCachedError",
    "ModelUnavailableError",
    "CorruptedCacheError",
    "ReadOnlyDatabaseError",
]
