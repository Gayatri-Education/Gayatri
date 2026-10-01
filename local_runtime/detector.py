"""Offline Capability Detector & Health Diagnostics subsystem.

Probes network state, database read/write permissions, model availability,
and cached course packages to provide honest, actionable degraded state reports.
"""

from __future__ import annotations

import logging
import socket
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from local_runtime.course_cache import LocalCourseCache
from local_runtime.session import LocalSessionPersistence

logger = logging.getLogger("gayatri.local_runtime.detector")


@dataclass
class OfflineCapabilitiesReport:
    """Diagnostic health summary of offline runtime capabilities."""
    is_online: bool
    db_writable: bool
    available_models: List[str]
    cached_courses: List[str]
    status_summary: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DegradedStateInfo:
    """Honest degraded state information detailing missing components."""
    is_degraded: bool
    reason: str
    actionable_message: str
    missing_components: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class OfflineCapabilityDetector:
    """Detects offline readiness and determines honest degraded execution modes."""

    def __init__(
        self,
        course_cache: Optional[LocalCourseCache] = None,
        session_store: Optional[LocalSessionPersistence] = None,
        available_models: Optional[List[str]] = None,
        force_offline: bool = False,
    ) -> None:
        self.course_cache = course_cache or LocalCourseCache()
        self.session_store = session_store
        self._available_models = set(available_models or ["local-slm-default", "phi3-mini", "qwen2.5-coder-7b", "llama3.2:1b"])
        self.force_offline = force_offline

    def is_network_available(self, host: str = "8.8.8.8", port: int = 53, timeout: float = 1.0) -> bool:
        """Check if an internet/external network connection is active."""
        if self.force_offline:
            return False
        try:
            socket.setdefaulttimeout(timeout)
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((host, port))
            return True
        except Exception:
            return False

    def is_database_writable(self) -> bool:
        """Verify if the local session persistence database is writable."""
        if not self.session_store:
            return True
        return not self.session_store.is_read_only

    def is_course_available_offline(self, course_id: str, version_tag: Optional[str] = None) -> bool:
        """Check if a course is cached locally for offline execution."""
        return self.course_cache.is_course_cached(course_id, version_tag)

    def is_model_available_offline(self, model_name: str) -> bool:
        """Check if a given model identifier is registered and present locally."""
        if not model_name:
            return False
        return model_name in self._available_models

    def register_available_model(self, model_name: str) -> None:
        """Register a locally available model name."""
        self._available_models.add(model_name)

    def unregister_model(self, model_name: str) -> None:
        """Remove a model from available local models."""
        self._available_models.discard(model_name)

    def check_offline_status(self) -> OfflineCapabilitiesReport:
        """Run full diagnostic check across network, DB, models, and course cache."""
        is_online = self.is_network_available()
        db_writable = self.is_database_writable()
        avail_models = sorted(list(self._available_models))
        cached_courses = [p.course_id for p in self.course_cache.list_cached_courses()]

        status_parts = []
        if is_online:
            status_parts.append("Network connected (online)")
        else:
            status_parts.append("Operating in disconnected offline mode")

        if not db_writable:
            status_parts.append("Database is read-only (degraded)")

        status_parts.append(f"{len(cached_courses)} cached course(s)")
        status_parts.append(f"{len(avail_models)} local model(s) available")

        summary = "; ".join(status_parts) + "."

        return OfflineCapabilitiesReport(
            is_online=is_online,
            db_writable=db_writable,
            available_models=avail_models,
            cached_courses=cached_courses,
            status_summary=summary,
        )

    def get_honest_degraded_state(
        self,
        course_id: str,
        model_name: Optional[str] = None,
        version_tag: Optional[str] = None,
    ) -> DegradedStateInfo:
        """Return clear diagnostic explanation if the requested context cannot run fully."""
        missing: List[str] = []
        reasons: List[str] = []
        actions: List[str] = []

        if not self.is_course_available_offline(course_id, version_tag):
            missing.append(f"course:{course_id}")
            reasons.append(f"Course '{course_id}' is not cached locally.")
            actions.append(f"Connect to the network to download '{course_id}' or import an offline package (.gpk).")

        if model_name and not self.is_model_available_offline(model_name):
            missing.append(f"model:{model_name}")
            reasons.append(f"Local model '{model_name}' is not installed or available offline.")
            avail = sorted(list(self._available_models))
            actions.append(f"Install '{model_name}' or select an available local model: {avail}.")

        if not self.is_database_writable():
            missing.append("database:readonly")
            reasons.append("Local database is in read-only mode.")
            actions.append("Session progress and turns cannot be saved; running in read-only study mode.")

        if not missing:
            return DegradedStateInfo(
                is_degraded=False,
                reason="All required components are available offline.",
                actionable_message="System is fully operational for offline learning.",
                missing_components=[],
            )

        return DegradedStateInfo(
            is_degraded=True,
            reason=" ".join(reasons),
            actionable_message=" ".join(actions),
            missing_components=missing,
        )
