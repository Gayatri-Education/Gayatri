"""Local Runtime Engine subsystem.

Unifies local course caching, course-isolated RAG retrieval, transactional session
persistence, and offline capability diagnostics for offline learning execution.
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Dict, List, Optional

from local_runtime.course_cache import LocalCourseCache
from local_runtime.detector import DegradedStateInfo, OfflineCapabilityDetector
from local_runtime.errors import (
    ModelUnavailableError,
    OfflineCourseNotCachedError,
    ReadOnlyDatabaseError,
)
from local_runtime.rag_cache import LocalRAGCache
from local_runtime.session import LocalSessionPersistence

logger = logging.getLogger("gayatri.local_runtime.engine")


class LocalRuntimeEngine:
    """Offline local execution engine for student tutoring sessions."""

    def __init__(
        self,
        course_cache: Optional[LocalCourseCache] = None,
        rag_cache: Optional[LocalRAGCache] = None,
        session_store: Optional[LocalSessionPersistence] = None,
        detector: Optional[OfflineCapabilityDetector] = None,
        orchestrator: Optional[Any] = None,
    ) -> None:
        self.course_cache = course_cache or LocalCourseCache()
        self.rag_cache = rag_cache or LocalRAGCache()
        self.session_store = session_store or LocalSessionPersistence()
        self.detector = detector or OfflineCapabilityDetector(
            course_cache=self.course_cache,
            session_store=self.session_store,
        )
        self.orchestrator = orchestrator

    def get_honest_state(
        self,
        course_id: str,
        model_name: Optional[str] = None,
        version_tag: Optional[str] = None,
    ) -> DegradedStateInfo:
        """Check whether execution is fully operational or in honest degraded mode."""
        return self.detector.get_honest_degraded_state(
            course_id=course_id,
            model_name=model_name,
            version_tag=version_tag,
        )

    def execute_tutor_turn(
        self,
        session_id: str,
        student_id: str,
        course_id: str,
        user_input: str,
        model_name: str = "local-slm-default",
        turn_index: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Execute a complete offline tutoring turn with transactional persistence.
        
        Guarantees:
        - Rejects uncached courses with OfflineCourseNotCachedError.
        - Rejects missing models with ModelUnavailableError.
        - Respects read-only mode by rejecting mutations with ReadOnlyDatabaseError.
        - Scopes knowledge search strictly to course_id.
        - Atomically commits turn, mastery delta, and events.
        """
        # 1. Verify course availability offline
        if not self.detector.is_course_available_offline(course_id):
            raise OfflineCourseNotCachedError(course_id=course_id)

        # 2. Verify model availability offline
        if not self.detector.is_model_available_offline(model_name):
            available = sorted(list(self.detector._available_models))
            raise ModelUnavailableError(model_name=model_name, available_models=available)

        # 3. Verify database writability
        if self.session_store.is_read_only:
            raise ReadOnlyDatabaseError(db_path=self.session_store.db_path)

        # 4. Begin transactional turn (PENDING_COMMIT)
        turn_id = self.session_store.begin_turn(
            session_id=session_id,
            student_id=student_id,
            course_id=course_id,
            user_input=user_input,
            turn_index=turn_index,
        )

        try:
            # 5. Fetch course curriculum and concepts
            cached_course = self.course_cache.get_cached_course(course_id) or {}
            manifest = cached_course.get("manifest", cached_course)
            concepts = manifest.get("concepts", [])
            concept_names = [c.get("name", c.get("id", "")) for c in concepts]

            # 6. Scoped RAG knowledge retrieval
            rag_chunks = self.rag_cache.search(query=user_input, course_id=course_id, top_k=3)

            # 7. Generate tutor response
            if self.orchestrator is not None and hasattr(self.orchestrator, "process_turn"):
                tutor_output = self.orchestrator.process_turn(
                    user_input=user_input,
                    course_id=course_id,
                    rag_chunks=rag_chunks,
                )
            else:
                # Built-in deterministic offline tutor generation
                context_str = " ".join([c["text"] for c in rag_chunks]) if rag_chunks else "Foundational syllabus guidance."
                tutor_output = (
                    f"Offline Tutor Response for '{user_input}': "
                    f"Based on course curriculum [{', '.join(concept_names[:3])}], "
                    f"here is the guided explanation: {context_str[:200]}"
                )

            # 8. Compute mastery progression
            current_mastery = self.session_store.get_student_mastery(student_id, course_id)
            target_concept = concepts[0]["id"] if concepts else "core_concept_1"
            prev_score = current_mastery.get(target_concept, 0.5)
            new_score = round(min(1.0, prev_score + 0.1), 2)
            mastery_updates = {target_concept: new_score}

            # 9. Learning events
            events = [
                {
                    "event_id": f"evt_{uuid.uuid4().hex[:10]}",
                    "event_type": "turn_completed",
                    "payload": {
                        "turn_id": turn_id,
                        "session_id": session_id,
                        "input_length": len(user_input),
                        "citations_count": len(rag_chunks),
                        "model_used": model_name,
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    },
                }
            ]

            # 10. Commit turn transaction
            self.session_store.commit_turn(
                turn_id=turn_id,
                tutor_output=tutor_output,
                mastery_updates=mastery_updates,
                events=events,
            )

            return {
                "ok": True,
                "turn_id": turn_id,
                "session_id": session_id,
                "student_id": student_id,
                "course_id": course_id,
                "tutor_output": tutor_output,
                "rag_citations": rag_chunks,
                "mastery": mastery_updates,
                "status": "COMPLETED",
            }
        except Exception:
            # If an error occurred before commit, roll back the turn
            try:
                self.session_store.rollback_turn(turn_id)
            except Exception:
                pass
            raise
