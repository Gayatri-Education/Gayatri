"""Typed error definitions for the Offline Local Runtime subsystem."""

from __future__ import annotations

from typing import List, Optional


class OfflineRuntimeError(Exception):
    """Base exception for all offline local runtime errors."""
    pass


class OfflineCourseNotCachedError(OfflineRuntimeError):
    """Raised when an operation requires a course package that is not cached locally."""

    def __init__(
        self,
        course_id: str,
        version_tag: Optional[str] = None,
        message: Optional[str] = None,
    ) -> None:
        self.course_id = course_id
        self.version_tag = version_tag
        version_str = f" (version: '{version_tag}')" if version_tag else ""
        default_message = (
            f"Course '{course_id}'{version_str} is not cached locally for offline execution. "
            f"Please connect to the network to download the course package or import an offline bundle (.gpk)."
        )
        super().__init__(message or default_message)


class ModelUnavailableError(OfflineRuntimeError):
    """Raised when a requested offline SLM/LLM model is missing or not installed."""

    def __init__(
        self,
        model_name: str,
        available_models: Optional[List[str]] = None,
        message: Optional[str] = None,
    ) -> None:
        self.model_name = model_name
        self.available_models = available_models or []
        avail_str = f" Available offline models: {self.available_models}." if self.available_models else " No offline models are currently installed."
        default_message = (
            f"Local model '{model_name}' is not installed or available offline.{avail_str} "
            f"Please download it via model manager or select an available local model."
        )
        super().__init__(message or default_message)


class CorruptedCacheError(OfflineRuntimeError):
    """Raised when a cached course package fails checksum verification or has invalid contents."""

    def __init__(
        self,
        course_id: str,
        package_path: Optional[str] = None,
        quarantine_path: Optional[str] = None,
        reason: Optional[str] = None,
        message: Optional[str] = None,
    ) -> None:
        self.course_id = course_id
        self.package_path = package_path
        self.quarantine_path = quarantine_path
        self.reason = reason or "Checksum verification failure or malformed archive"
        quarantine_info = f" Quarantined to: {quarantine_path}." if quarantine_path else ""
        default_message = (
            f"Cached course package for '{course_id}' is corrupted: {self.reason}.{quarantine_info}"
        )
        super().__init__(message or default_message)


class ReadOnlyDatabaseError(OfflineRuntimeError):
    """Raised when a state modification is attempted on a read-only database."""

    def __init__(
        self,
        message: Optional[str] = None,
        db_path: Optional[str] = None,
    ) -> None:
        self.db_path = db_path
        default_message = (
            f"Local database is in read-only degraded mode{f' at {db_path}' if db_path else ''}. "
            "Write operations (turns, mastery updates, learning events) are blocked."
        )
        super().__init__(message or default_message)
