"""Learning Graph Engine for Phase 13.

Implements concept graph with prerequisites, mastery, confidence, attempts,
misconceptions, review scheduling, assessment state, and teacher interventions.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from central_platform.db import PlatformDatabase
from central_platform.models.schema import (
    Concept,
    MasteryState,
    Misconception,
    Prerequisite,
    StudentLearningRecord,
    StudentMisconceptionRecord,
    TeacherInstructionRecord,
)


@dataclass
class ConceptNodeState:
    """Full node state in the Learning Graph for a specific student and concept."""
    concept_id: str
    concept_name: str
    topic_id: str
    description: str = ""
    difficulty: float = 0.5
    
    # Mastery & Confidence
    mastery_score: float = 0.50
    confidence: float = 0.80
    mastery_status: str = "practicing"  # "new", "practicing", "mastered", "review_due"
    
    # Prerequisite DAG relationships
    prerequisite_ids: List[str] = field(default_factory=list)
    dependent_ids: List[str] = field(default_factory=list)
    prerequisites_satisfied: bool = True
    
    # Attempts & Telemetry
    total_attempts: int = 0
    correct_attempts: int = 0
    incorrect_attempts: int = 0
    hints_requested: int = 0
    last_practiced_at: Optional[str] = None
    
    # Misconceptions
    active_misconceptions: List[str] = field(default_factory=list)
    
    # Review & Assessment
    next_review_at: Optional[str] = None
    review_due: bool = False
    assessments_completed: int = 0
    
    # Teacher Interventions
    active_teacher_instructions: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class LearningGraph:
    """Authoritative Concept Learning Graph manager."""

    def __init__(self, db: PlatformDatabase):
        self.db = db

    def get_prerequisites(self, concept_id: str) -> List[str]:
        """Fetch direct prerequisite concept IDs."""
        if hasattr(self.db, "get_prerequisites_for_concept"):
            return self.db.get_prerequisites_for_concept(concept_id)
        return []

    def get_prerequisite_chain(self, concept_id: str, visited: Optional[Set[str]] = None) -> List[str]:
        """Recursively fetch full prerequisite DAG chain."""
        if visited is None:
            visited = set()
        
        if concept_id in visited:
            return []  # Prevent infinite loops in cycle
        visited.add(concept_id)
        
        chain = []
        direct = self.get_prerequisites(concept_id)
        for prereq in direct:
            chain.append(prereq)
            chain.extend(self.get_prerequisite_chain(prereq, visited))
            
        return list(dict.fromkeys(chain))  # Deduplicate while preserving order

    def validate_dag(self, concept_ids: List[str]) -> Dict[str, Any]:
        """Check for cycles or missing prerequisites in the graph across any depth."""
        cycles = []
        missing = []
        
        for cid in concept_ids:
            prereqs = self.get_prerequisites(cid)
            for p in prereqs:
                if p not in concept_ids and not self.db.get_concept(p):
                    missing.append({"concept_id": cid, "missing_prerequisite": p})
                # Check for cycle of any depth: if cid is in p's prerequisite chain
                p_chain = self.get_prerequisite_chain(p)
                if cid in p_chain or cid == p:
                    cycles.append((cid, p))
                    
        return {
            "valid": len(cycles) == 0 and len(missing) == 0,
            "cycles": cycles,
            "missing_prerequisites": missing,
        }

    @staticmethod
    def validate_curriculum_dag(curriculum: Any) -> Dict[str, Any]:
        """Validate an in-memory GenericCurriculum for cycles, missing prereqs, and orphan concepts."""
        concepts = curriculum.all_concepts() if hasattr(curriculum, "all_concepts") else []
        cid_set = {c.id for c in concepts}
        adj = {c.id: list(c.prerequisites) for c in concepts}

        # 1. Missing prerequisites
        missing = []
        for c in concepts:
            for p in c.prerequisites:
                if p not in cid_set:
                    missing.append({"concept_id": c.id, "missing_prerequisite": p})

        # 2. Cycle detection using DFS with recursion stack
        visited: Dict[str, int] = {}
        cycles = []

        def dfs(node: str, path: List[str]):
            visited[node] = 1  # in progress
            for neighbor in adj.get(node, []):
                if neighbor not in cid_set:
                    continue
                if visited.get(neighbor) == 1:
                    cycles.append((node, neighbor))
                elif visited.get(neighbor) != 2:
                    dfs(neighbor, path + [neighbor])
            visited[node] = 2  # done

        for cid in cid_set:
            if visited.get(cid) is None:
                dfs(cid, [cid])

        # 3. Orphan detection
        dependents: Dict[str, List[str]] = {cid: [] for cid in cid_set}
        for cid, prereqs in adj.items():
            for p in prereqs:
                if p in dependents:
                    dependents[p].append(cid)

        orphans = []
        if len(cid_set) > 1:
            for cid in cid_set:
                if not adj.get(cid) and not dependents.get(cid):
                    orphans.append(cid)

        return {
            "valid": len(cycles) == 0 and len(missing) == 0,
            "cycles": cycles,
            "missing_prerequisites": missing,
            "orphan_concepts": orphans,
        }

    def get_concept_node_state(

        self,
        student_id: str,
        course_id: str,
        concept_id: str,
    ) -> ConceptNodeState:
        """Construct the complete multi-dimensional node state for a student."""
        # 1. Fetch Concept Entity
        concept = self.db.get_concept(concept_id)
        c_name = concept.name if concept else concept_id
        t_id = concept.topic_id if concept else ""
        desc = concept.description if concept else ""
        diff = concept.difficulty if concept else 0.5

        # 2. Fetch SLR and Mastery
        slr = self.db.get_slr(student_id, course_id)
        mastery_score = 0.50
        confidence = 0.80
        mastery_status = "new"
        last_practiced = None
        
        if slr:
            mastery_states = self.db.get_mastery_states_for_slr(slr.id)
            ms = next((m for m in mastery_states if m.concept_id == concept_id), None)
            if ms:
                mastery_score = ms.score
                confidence = ms.confidence
                mastery_status = ms.state
                last_practiced = ms.last_practiced_at

        # 3. Prerequisites & Satisfaction Check
        prereq_ids = self.get_prerequisites(concept_id)
        prereqs_satisfied = True
        if slr and prereq_ids:
            mastery_states = self.db.get_mastery_states_for_slr(slr.id)
            for pid in prereq_ids:
                p_ms = next((m for m in mastery_states if m.concept_id == pid), None)
                if not p_ms or p_ms.score < 0.60:
                    prereqs_satisfied = False
                    break

        # 4. Telemetry Events (Attempts & Hints)
        events = self.db.query_learning_events(student_id=student_id, course_id=course_id, limit=500)
        concept_events = [e for e in events if e.concept_id == concept_id]
        
        total_attempts = len(concept_events)
        correct_attempts = 0
        incorrect_attempts = 0
        hints_requested = 0
        
        for ev in concept_events:
            p = ev.payload or {}
            if ev.event_type == "answer_submitted":
                correctness = p.get("correctness")
                if correctness == "correct" or (ev.score is not None and ev.score >= 0.7):
                    correct_attempts += 1
                elif correctness == "incorrect" or (ev.score is not None and ev.score < 0.5):
                    incorrect_attempts += 1
            elif ev.event_type == "hint_requested":
                hints_requested += 1

        # 5. Active Misconceptions
        student_miscs = self.db.get_student_misconceptions(student_id)
        active_miscs = [m.misconception_code for m in student_miscs if m.frequency > 0]

        # 6. Teacher Instructions
        instructions = self.db.get_teacher_instructions_for_course(course_id) if hasattr(self.db, "get_teacher_instructions_for_course") else []
        active_instructions = [
            {"id": i.id, "directive": i.instruction_text}
            for i in instructions
            if getattr(i, "is_active", True)
        ]

        return ConceptNodeState(
            concept_id=concept_id,
            concept_name=c_name,
            topic_id=t_id,
            description=desc,
            difficulty=diff,
            mastery_score=mastery_score,
            confidence=confidence,
            mastery_status=mastery_status,
            prerequisite_ids=prereq_ids,
            prerequisites_satisfied=prereqs_satisfied,
            total_attempts=total_attempts,
            correct_attempts=correct_attempts,
            incorrect_attempts=incorrect_attempts,
            hints_requested=hints_requested,
            last_practiced_at=last_practiced,
            active_misconceptions=active_miscs,
            active_teacher_instructions=active_instructions,
        )
