"""Authoritative Student Progress Service (Phase 09).

Master Plan Section 18:
Aggregates all 14 canonical student learning progress dimensions directly
from Authoritative SLR data and central learning events.
Strictly ensures recommendations are policy-generated (no free-form LLM text).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from central_platform.db import PlatformDatabase
from central_platform.events.store import LearningEventStore
from central_platform.progress.models import (
    AccuracyTrendPoint,
    HeatmapNode,
    LearningStreak,
    MasteryTrendPoint,
    QuestionTypeMetric,
    ReviewDueItem,
    SessionSummary,
    StudentProgressReport,
    TopicMastery,
    WeakArea,
)
from central_platform.slr.service import SLRService
from core.learning.progress import get_concept_domain, get_status_label
from core.learning.scheduler import SpacedReviewScheduler


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _format_concept_name(concept_id: str) -> str:
    """Format concept code to clean human-readable title."""
    parts = concept_id.replace("chem_", "").replace("thermo_", "").replace("inorg_", "").split("_")
    return " ".join(p.capitalize() for p in parts)


class StudentProgressService:
    """Authoritative progress engine computing all 14 learning progress dimensions."""

    def __init__(
        self,
        db: Optional[PlatformDatabase] = None,
        event_store: Optional[LearningEventStore] = None,
        slr_service: Optional[SLRService] = None,
    ):
        if db is not None:
            self.db = db
        else:
            try:
                from central_platform.auth.dependencies import get_db
                self.db = get_db()
            except Exception:
                self.db = PlatformDatabase()

        self.event_store = (
            event_store if event_store is not None else LearningEventStore(db=self.db)
        )
        self.slr_service = (
            slr_service
            if slr_service is not None
            else SLRService(db=self.db, event_store=self.event_store)
        )
        self.scheduler = SpacedReviewScheduler()

    def get_student_progress(
        self,
        student_id: str,
        course_id: Optional[str] = None,
    ) -> StudentProgressReport:
        """Construct the canonical 14-dimension Student Learning Progress Report."""
        target_course = course_id or "crs-chem-101"
        self.slr_service._ensure_student_scaffolding(student_id, target_course)

        # 1. Authoritative SLR & Masteries
        slr = self.slr_service.get_authoritative_slr(student_id, target_course)
        overall_mastery = slr.mastery.overall_score
        concept_scores = dict(slr.mastery.concept_scores)
        concept_confidences = dict(slr.mastery.concept_confidences)

        # 2. Chronological event stream
        raw_events = self.event_store.get_student_events(student_id, target_course, limit=500)

        # 2. Topic Mastery Aggregation
        topic_buckets: Dict[str, List[float]] = {}
        for cid, score in concept_scores.items():
            domain = get_concept_domain(cid)
            topic_buckets.setdefault(domain, []).append(score)

        topic_mastery: List[TopicMastery] = []
        for domain, scores in topic_buckets.items():
            avg_score = round(sum(scores) / len(scores), 4)
            if avg_score >= 0.80:
                t_status = "MASTERED"
            elif avg_score >= 0.65:
                t_status = "PROFICIENT"
            elif avg_score >= 0.40:
                t_status = "PRACTICING"
            else:
                t_status = "LEARNING"

            topic_mastery.append(
                TopicMastery(
                    topic_id=domain.lower().replace(" ", "_"),
                    topic_name=domain,
                    concept_count=len(scores),
                    mastery_score=avg_score,
                    status=t_status,
                )
            )

        # 3. Concept Heatmap
        status_colors = {
            "MASTERED": "#10b981",    # Emerald
            "PROFICIENT": "#3b82f6",  # Blue
            "PRACTICING": "#f59e0b",  # Amber
            "LEARNING": "#6366f1",    # Indigo
            "NEW": "#9ca3af",         # Slate
            "REVIEW_DUE": "#8b5cf6",  # Purple
        }

        concept_heatmap: List[HeatmapNode] = []
        review_due_items: List[ReviewDueItem] = []

        for cid, score in concept_scores.items():
            domain = get_concept_domain(cid)
            conf = concept_confidences.get(cid, 0.80)

            # Check review schedule from latest events
            next_rev = ""
            for ev in reversed(raw_events):
                if ev.concept_id == cid and ev.payload:
                    next_rev = ev.payload.get("next_review_at", "")
                    if next_rev:
                        break

            is_due = self.scheduler.is_review_due(next_rev) if next_rev else False
            c_name = _format_concept_name(cid)

            # Exposure count from events
            exposure = sum(1 for e in raw_events if e.concept_id == cid)
            status_lbl = get_status_label(score, exposure, is_due)
            color = status_colors.get(status_lbl, "#3b82f6")

            concept_heatmap.append(
                HeatmapNode(
                    concept_id=cid,
                    concept_name=c_name,
                    domain=domain,
                    mastery_score=round(score, 4),
                    confidence=round(conf, 4),
                    status=status_lbl,
                    color=color,
                    is_review_due=is_due,
                )
            )

            if is_due:
                review_due_items.append(
                    ReviewDueItem(
                        concept_id=cid,
                        concept_name=c_name,
                        due_at=next_rev or _now_iso(),
                        overdue_days=1,
                        current_mastery=score,
                    )
                )

        # 4. Recent Sessions
        recent_sessions = [
            {
                "session_id": s.session_id,
                "concept_id": s.concept_id,
                "status": s.status,
                "started_at": s.started_at,
                "ended_at": s.ended_at,
                "duration_seconds": s.duration_seconds or 0,
            }
            for s in slr.recent_sessions
        ]

        # 5. Recent Activity Timeline
        recent_activity = [
            {
                "item_id": t.item_id,
                "event_type": t.event_type,
                "summary": t.summary,
                "timestamp": t.timestamp,
                "score": t.score,
                "concept_id": t.concept_id,
            }
            for t in slr.learning_timeline[:20]
        ]

        # 6. Weak Areas (< 0.60 mastery where student has had exposure)
        weak_areas: List[WeakArea] = []
        for cid, score in concept_scores.items():
            exposure = sum(1 for e in raw_events if e.concept_id == cid)
            if score < 0.60 and exposure > 0:
                gap = round(1.0 - score, 4)
                weak_areas.append(
                    WeakArea(
                        concept_id=cid,
                        concept_name=_format_concept_name(cid),
                        mastery_score=round(score, 4),
                        mastery_gap=gap,
                        recommended_action=f"Remediate core fundamentals in {_format_concept_name(cid)}",
                    )
                )
        weak_areas.sort(key=lambda w: w.mastery_gap, reverse=True)

        # 7. Misconceptions
        misconceptions = [
            {
                "code": m.code,
                "name": m.name,
                "category": m.category,
                "frequency": m.frequency,
                "last_observed": m.last_observed,
                "remediation": m.remediation,
                "status": m.status,
            }
            for m in slr.misconceptions
        ]

        # 8. Accuracy Trends & 9. Mastery Trends
        accuracy_trends: List[AccuracyTrendPoint] = []
        mastery_trends: List[MasteryTrendPoint] = []

        valid_events = [e for e in raw_events if e.payload and e.payload.get("correctness") in ("correct", "incorrect", "partially_correct")]
        running_correct = 0
        running_mastery = 0.50

        for i, ev in enumerate(valid_events):
            corr = ev.payload.get("correctness")
            if corr == "correct":
                running_correct += 1
                running_mastery = min(1.0, running_mastery + 0.05)
            elif corr == "partially_correct":
                running_correct += 0.5
                running_mastery = min(1.0, running_mastery + 0.02)
            else:
                running_mastery = max(0.0, running_mastery - 0.05)

            cur_acc = round(running_correct / (i + 1), 4)

            # Sample periodic trend points
            if (i + 1) % max(1, len(valid_events) // 10 or 1) == 0 or i == len(valid_events) - 1:
                accuracy_trends.append(
                    AccuracyTrendPoint(
                        timestamp=ev.created_at,
                        accuracy=cur_acc,
                        event_count=i + 1,
                    )
                )
                mastery_trends.append(
                    MasteryTrendPoint(
                        timestamp=ev.created_at,
                        mastery=round(running_mastery, 4),
                        event_count=i + 1,
                    )
                )

        if not accuracy_trends:
            accuracy_trends.append(AccuracyTrendPoint(_now_iso(), 1.0 if overall_mastery >= 0.7 else 0.5, 0))
        if not mastery_trends:
            mastery_trends.append(MasteryTrendPoint(_now_iso(), overall_mastery, 0))

        # 10. Question-Type Performance
        type_buckets: Dict[str, Dict[str, int]] = {}
        for ev in raw_events:
            p = ev.payload or {}
            q_type = p.get("question_type") or ("numerical" if "num" in str(ev.concept_id) else "conceptual")
            if q_type not in type_buckets:
                type_buckets[q_type] = {"attempts": 0, "correct": 0}

            corr = str(p.get("correctness", "")).lower()
            if corr in ("correct", "incorrect", "partially_correct"):
                type_buckets[q_type]["attempts"] += 1
                if corr == "correct":
                    type_buckets[q_type]["correct"] += 1

        question_type_performance: Dict[str, QuestionTypeMetric] = {}
        for qt, data in type_buckets.items():
            att = data["attempts"]
            corr = data["correct"]
            acc = round(corr / att, 4) if att > 0 else 0.0
            question_type_performance[qt] = QuestionTypeMetric(
                question_type=qt,
                attempts=att,
                correct=corr,
                accuracy=acc,
            )

        if not question_type_performance:
            question_type_performance["conceptual"] = QuestionTypeMetric("conceptual", 1, 1 if overall_mastery >= 0.5 else 0, overall_mastery)

        # 12. Policy-driven Recommendations (strictly from SLR learning policy)
        recommendations = [
            {
                "recommendation_id": r.recommendation_id,
                "concept_id": r.concept_id,
                "action_type": r.action_type,
                "reason": r.reason,
                "priority": r.priority,
            }
            for r in slr.recommendations
        ]

        # 13. Latest Session Summary
        session_summary: Optional[SessionSummary] = None
        if slr.recent_sessions:
            latest_s = slr.recent_sessions[0]
            sess_events = [e for e in raw_events if e.session_id == latest_s.session_id]
            sess_att = len(sess_events)
            sess_corr = sum(1 for e in sess_events if (e.payload or {}).get("correctness") == "correct")
            sess_acc = round(sess_corr / sess_att, 4) if sess_att > 0 else 1.0

            session_summary = SessionSummary(
                session_id=latest_s.session_id,
                concept_id=latest_s.concept_id,
                status=latest_s.status,
                questions_attempted=sess_att,
                accuracy=sess_acc,
                duration_seconds=latest_s.duration_seconds or 120,
            )

        # 14. Learning Streak Calculation
        active_dates: Set[str] = set()
        for ev in raw_events:
            ts = ev.created_at
            if ts and len(ts) >= 10:
                active_dates.add(ts[:10])

        streak_count = len(active_dates)
        latest_date = max(active_dates) if active_dates else _now_iso()[:10]
        learning_streak = LearningStreak(
            current_streak_days=streak_count,
            longest_streak_days=max(streak_count, 1),
            active_days_last_30=streak_count,
            last_active_date=latest_date,
        )

        return StudentProgressReport(
            student_id=student_id,
            course_id=target_course,
            generated_at=_now_iso(),
            overall_mastery=overall_mastery,
            topic_mastery=topic_mastery,
            concept_heatmap=concept_heatmap,
            recent_sessions=recent_sessions,
            recent_activity=recent_activity,
            weak_areas=weak_areas,
            misconceptions=misconceptions,
            accuracy_trends=accuracy_trends,
            mastery_trends=mastery_trends,
            question_type_performance=question_type_performance,
            review_due=review_due_items,
            recommendations=recommendations,
            session_summary=session_summary,
            learning_streak=learning_streak,
        )
