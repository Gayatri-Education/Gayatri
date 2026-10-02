"""Gayatri AI Platform — Plug-and-Play Curriculum Service (Phase 15 / Section 24).

Master Plan Section 24 Requirements:
1. Target Hierarchy:
   Course -> Curriculum Version -> Subject -> Module -> Topic -> Concept -> Prerequisites (DAG) -> Activities -> Assessments.
2. Immutability Invariant:
   Once a curriculum version is published, it is strictly read-only and immutable.
   Any modifications require creating a new draft version.
3. Rigorous Validation:
   - Cycle detection: No circular prerequisite chains (A -> B -> A).
   - No orphan prerequisites: Prerequisites must reference valid concepts within curriculum scope.
   - No orphan concepts: Concepts must be placed within valid topics and modules.
   - Stable identifier enforcement: Alphanumeric and dot/hyphen identifiers only (no free text).
4. Documented Import / Export Schema:
   Universal JSON declarative format with round-trip fidelity.
5. Tutor Decoupling:
   Dynamic curriculum resolution replacing hardcoded chemistry assumptions.
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from central_platform.db import PlatformDatabase
from central_platform.models.schema import (
    Concept,
    Course,
    Curriculum,
    CurriculumVersion,
    Module,
    Prerequisite,
    Subject,
    Topic,
    User,
    UserRole,
)

logger = logging.getLogger("gayatri.curriculum.service")
STABLE_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_.\-]+$")


class CurriculumStatus(str, Enum):
    DRAFT = "draft"
    VALIDATED = "validated"
    PUBLISHED = "published"
    ARCHIVED = "archived"


@dataclass
class ValidationReport:
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    concept_count: int = 0
    cycle_nodes: List[str] = field(default_factory=list)
    orphan_prerequisites: List[str] = field(default_factory=list)
    dag_depth: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CurriculumService:
    """Authoritative service managing versioned plug-and-play curricula."""

    def __init__(self, db: PlatformDatabase):
        self.db = db

    # ── 1. Lifecycle: Create Curriculum & Draft Versions ──────────────────────

    def create_curriculum(
        self,
        admin: User,
        course_id: str,
        title: str,
        initial_version: str = "v1.0.0",
    ) -> Tuple[Curriculum, CurriculumVersion]:
        """Create a new curriculum entity and its initial draft version."""
        if admin.role in (UserRole.STUDENT,):
            raise PermissionError("Students cannot create curricula.")

        course = self.db.get_course(course_id)
        if not course:
            raise ValueError(f"Course '{course_id}' not found.")

        # Authorize admin for organization
        if admin.role == UserRole.ORG_ADMIN and course.organization_id != admin.organization_id:
            raise PermissionError("Org Admin cannot manage curricula for other organizations.")

        curr_id = f"cur-{uuid.uuid4().hex[:8]}"
        curriculum = Curriculum(
            id=curr_id,
            course_id=course_id,
            title=title,
            version=initial_version,
            is_active=True,
        )
        self.db.create_curriculum(curriculum)

        # Initial draft version
        v_id = f"cv-{uuid.uuid4().hex[:8]}"
        ver = CurriculumVersion(
            id=v_id,
            curriculum_id=curr_id,
            version_num=initial_version,
            change_log="Initial curriculum version draft",
            status=CurriculumStatus.DRAFT.value,
        )
        self.db.create_curriculum_version(ver)
        return curriculum, ver

    def create_version_draft(
        self,
        admin: User,
        curriculum_id: str,
        new_version_num: str,
        change_log: str = "",
        base_version_id: Optional[str] = None,
    ) -> CurriculumVersion:
        """Create a new draft version, optionally cloning from an existing version."""
        if admin.role in (UserRole.STUDENT,):
            raise PermissionError("Students cannot create curriculum versions.")

        curr = self.db.get_curriculum(curriculum_id)
        if not curr:
            raise ValueError(f"Curriculum '{curriculum_id}' not found.")

        # Check existing versions to prevent duplicate version_num
        versions = self.db.get_curriculum_versions(curriculum_id)
        for v in versions:
            if v.version_num == new_version_num:
                raise ValueError(f"Version '{new_version_num}' already exists for curriculum '{curriculum_id}'.")

        v_id = f"cv-{uuid.uuid4().hex[:8]}"
        schema_data = "{}"

        # If base version provided, clone its schema/hierarchy
        if base_version_id:
            base_ver = self.db.get_curriculum_version(base_version_id)
            if base_ver:
                schema_data = base_ver.schema_data

        new_ver = CurriculumVersion(
            id=v_id,
            curriculum_id=curriculum_id,
            version_num=new_version_num,
            change_log=change_log or f"Draft version {new_version_num}",
            status=CurriculumStatus.DRAFT.value,
            schema_data=schema_data,
        )
        self.db.create_curriculum_version(new_ver)
        return new_ver

    # ── 2. Immutability Guard & Node Authoring ────────────────────────────────

    def _ensure_version_mutable(self, version_id: str) -> CurriculumVersion:
        """Ensure curriculum version exists and is in a mutable draft state."""
        ver = self.db.get_curriculum_version(version_id)
        if not ver:
            raise ValueError(f"Curriculum version '{version_id}' not found.")
        if ver.status == CurriculumStatus.PUBLISHED.value:
            raise ValueError(
                f"Curriculum version '{ver.version_num}' ({version_id}) is PUBLISHED and immutable. "
                "Create a new draft version to make modifications."
            )
        return ver

    def add_module(
        self,
        admin: User,
        version_id: str,
        title: str,
        sequence_order: int = 1,
        subject_id: Optional[str] = None,
    ) -> Module:
        ver = self._ensure_version_mutable(version_id)
        mod_id = f"mod-{uuid.uuid4().hex[:8]}"
        mod = Module(
            id=mod_id,
            curriculum_id=ver.curriculum_id,
            title=title,
            sequence_order=sequence_order,
            subject_id=subject_id,
        )
        self.db.create_module(mod)
        return mod

    def add_topic(
        self,
        admin: User,
        version_id: str,
        module_id: str,
        title: str,
        sequence_order: int = 1,
    ) -> Topic:
        self._ensure_version_mutable(version_id)
        top_id = f"top-{uuid.uuid4().hex[:8]}"
        top = Topic(
            id=top_id,
            module_id=module_id,
            title=title,
            sequence_order=sequence_order,
        )
        self.db.create_topic(top)
        return top

    def add_concept(
        self,
        admin: User,
        version_id: str,
        topic_id: str,
        concept_id: str,
        name: str,
        description: str = "",
        difficulty: float = 0.5,
        prerequisites: Optional[List[str]] = None,
    ) -> Concept:
        self._ensure_version_mutable(version_id)
        if not STABLE_ID_PATTERN.match(concept_id):
            raise ValueError(f"Concept ID '{concept_id}' must be a stable identifier without spaces.")

        concept = Concept(
            id=concept_id,
            topic_id=topic_id,
            name=name,
            description=description,
            difficulty=difficulty,
        )
        self.db.create_concept(concept)

        if prerequisites:
            for p_id in prerequisites:
                if not STABLE_ID_PATTERN.match(p_id):
                    raise ValueError(f"Prerequisite ID '{p_id}' must be a stable identifier.")
                self.db.add_prerequisite(Prerequisite(prerequisite_concept_id=p_id, dependent_concept_id=concept_id))

        return concept

    # ── 3. Rigorous DAG & Structural Validation ───────────────────────────────

    def validate_curriculum(self, version_id_or_package: Any) -> ValidationReport:
        """Perform comprehensive DAG and structural validation on a curriculum package or version."""
        errors: List[str] = []
        warnings: List[str] = []
        cycle_nodes: List[str] = []
        orphan_prereqs: List[str] = []

        concepts_data: List[Dict[str, Any]] = []

        if isinstance(version_id_or_package, str):
            # Fetch from database or version schema_data
            ver = self.db.get_curriculum_version(version_id_or_package)
            if not ver:
                return ValidationReport(is_valid=False, errors=[f"Version '{version_id_or_package}' not found."])
            if ver.schema_data and ver.schema_data != "{}":
                try:
                    pkg = json.loads(ver.schema_data)
                    concepts_data = pkg.get("concepts", [])
                except Exception:
                    concepts_data = []
            if not concepts_data:
                # Build concepts from database modules/topics
                mods = self.db.get_modules_by_curriculum(ver.curriculum_id)
                for m in mods:
                    tops = self.db.get_topics_by_module(m.id)
                    for t in tops:
                        c_list = self.db.get_concepts_by_topic(t.id)
                        for c in c_list:
                            prereqs = self.db.get_prerequisites_for_concept(c.id)
                            concepts_data.append({
                                "id": c.id,
                                "name": c.name,
                                "description": c.description,
                                "difficulty": c.difficulty,
                                "topic_id": t.id,
                                "prerequisites": prereqs,
                            })
        elif isinstance(version_id_or_package, dict):
            concepts_data = list(version_id_or_package.get("concepts", []))
            if not concepts_data and "modules" in version_id_or_package:
                for mod in version_id_or_package.get("modules", []):
                    for top in mod.get("topics", []):
                        concepts_data.extend(top.get("concepts", []))
        elif isinstance(version_id_or_package, list):
            concepts_data = version_id_or_package

        if not concepts_data:
            return ValidationReport(is_valid=False, errors=["Curriculum contains no concepts."])

        # 1. Unique IDs & Programmatic Format Checks
        seen_ids: Set[str] = set()
        concept_map: Dict[str, Dict[str, Any]] = {}
        for c in concepts_data:
            cid = c.get("id") or c.get("concept_id")
            if not cid:
                errors.append("Encountered concept missing required 'id'.")
                continue
            if not STABLE_ID_PATTERN.match(cid):
                errors.append(f"Concept ID '{cid}' is invalid. Must match ^[a-zA-Z0-9_.-]+$.")
            if cid in seen_ids:
                errors.append(f"Duplicate concept ID found: '{cid}'.")
            seen_ids.add(cid)
            concept_map[cid] = c

            # Difficulty checks
            diff = c.get("difficulty", 0.5)
            if not (0.0 <= diff <= 1.0 or 1 <= diff <= 5):
                errors.append(f"Concept '{cid}' has invalid difficulty {diff}. Must be 0.0-1.0 or 1-5.")

        # 2. Orphan Prerequisites Check
        for cid, c in concept_map.items():
            prereqs = c.get("prerequisites") or []
            for p in prereqs:
                if not STABLE_ID_PATTERN.match(p):
                    errors.append(f"Prerequisite '{p}' for concept '{cid}' is invalid programmatic identifier.")
                if p not in seen_ids:
                    errors.append(f"Orphan prerequisite detected: Concept '{cid}' requires non-existent '{p}'.")
                    orphan_prereqs.append(p)

        # 3. Cycle Detection in Prerequisite Graph (DFS with recursion stack)
        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        cycle_found: bool = False

        def dfs(node: str, path: List[str]) -> bool:
            nonlocal cycle_found
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            node_data = concept_map.get(node)
            if node_data:
                for prereq in node_data.get("prerequisites") or []:
                    if prereq in rec_stack:
                        cycle_found = True
                        cycle_path = " -> ".join(path + [prereq])
                        cycle_nodes.append(cycle_path)
                        errors.append(f"Prerequisite cycle detected: {cycle_path}")
                        return True
                    if prereq not in visited and prereq in concept_map:
                        if dfs(prereq, path):
                            return True

            rec_stack.remove(node)
            path.pop()
            return False

        for cid in list(concept_map.keys()):
            if cid not in visited:
                dfs(cid, [])

        is_valid = len(errors) == 0
        return ValidationReport(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            concept_count=len(seen_ids),
            cycle_nodes=cycle_nodes,
            orphan_prerequisites=orphan_prereqs,
        )

    # ── 4. Publishing & Immutability Enforcement ──────────────────────────────

    def publish_curriculum_version(self, admin: User, version_id: str) -> CurriculumVersion:
        """Validate and publish a curriculum version, making it authoritative and immutable."""
        if admin.role in (UserRole.STUDENT,):
            raise PermissionError("Students cannot publish curricula.")

        ver = self.db.get_curriculum_version(version_id)
        if not ver:
            raise ValueError(f"Curriculum version '{version_id}' not found.")

        if ver.status == CurriculumStatus.PUBLISHED.value:
            return ver  # Already published

        # Run validation
        report = self.validate_curriculum(version_id)
        if not report.is_valid:
            error_msg = "; ".join(report.errors)
            raise ValueError(f"Curriculum validation failed before publishing: {error_msg}")

        now_iso = datetime.now(timezone.utc).isoformat()
        self.db.update_curriculum_version_status(version_id, CurriculumStatus.PUBLISHED.value, published_at=now_iso)

        # Update parent curriculum active version
        curr = self.db.get_curriculum(ver.curriculum_id)
        if curr:
            curr.version = ver.version_num
            curr.is_active = True
            self.db.create_curriculum(curr)

        ver.status = CurriculumStatus.PUBLISHED.value
        ver.published_at = now_iso
        logger.info(f"Published curriculum version {ver.version_num} ({version_id})")
        return ver

    # ── 5. Full Hierarchy Retrieval ───────────────────────────────────────────

    def get_curriculum_hierarchy(self, course_id_or_curriculum_id: str) -> Dict[str, Any]:
        """Build full Course -> Subject -> Module -> Topic -> Concept DAG hierarchy."""
        # Find active curriculum
        curr = self.db.get_curriculum(course_id_or_curriculum_id)
        if not curr:
            curr = self.db.get_curriculum_for_course(course_id_or_curriculum_id)
        if not curr:
            # Fall back to first curriculum matching course
            all_courses = self.db.list_courses()
            for c in all_courses:
                if c.id == course_id_or_curriculum_id or c.code == course_id_or_curriculum_id:
                    curr = self.db.get_curriculum_for_course(c.id)
                    break

        if not curr:
            raise ValueError(f"No active curriculum found for '{course_id_or_curriculum_id}'.")

        # Get latest active/published version
        versions = self.db.get_curriculum_versions(curr.id)
        active_ver = next((v for v in versions if v.status == CurriculumStatus.PUBLISHED.value), None)
        if not active_ver and versions:
            active_ver = versions[0]

        # Check if version has full cached declarative schema
        if active_ver and active_ver.schema_data and active_ver.schema_data != "{}":
            try:
                data = json.loads(active_ver.schema_data)
                data["version_id"] = active_ver.id
                data["curriculum_id"] = curr.id
                data["status"] = active_ver.status
                if not data.get("modules") and data.get("concepts"):
                    data["modules"] = [
                        {
                            "id": f"mod-{active_ver.id[:6]}",
                            "title": data.get("title", "Core Module"),
                            "topics": [
                                {
                                    "id": f"top-{active_ver.id[:6]}",
                                    "title": "Core Concepts",
                                    "concepts": data.get("concepts", []),
                                }
                            ],
                        }
                    ]
                return data
            except Exception as exc:
                logger.debug("Failed parsing version schema_data, falling back to relational tables: %s", exc)

        # Build dynamically from database tables
        subjects = self.db.get_subjects_by_course(curr.course_id)
        modules = self.db.get_modules_by_curriculum(curr.id)

        modules_payload = []
        total_concepts = 0
        total_topics = 0

        for m in modules:
            topics = self.db.get_topics_by_module(m.id)
            topics_payload = []
            for t in topics:
                concepts = self.db.get_concepts_by_topic(t.id)
                concepts_payload = []
                for c in concepts:
                    prereqs = self.db.get_prerequisites_for_concept(c.id)
                    concepts_payload.append({
                        "id": c.id,
                        "name": c.name,
                        "description": c.description,
                        "difficulty": c.difficulty,
                        "prerequisites": prereqs,
                    })
                total_concepts += len(concepts)
                total_topics += 1
                topics_payload.append({
                    "id": t.id,
                    "title": t.title,
                    "sequence_order": t.sequence_order,
                    "concepts": concepts_payload,
                })
            modules_payload.append({
                "id": m.id,
                "title": m.title,
                "sequence_order": m.sequence_order,
                "topics": topics_payload,
            })

        course = self.db.get_course(curr.course_id)
        return {
            "curriculum_id": curr.id,
            "version_id": active_ver.id if active_ver else None,
            "course_id": curr.course_id,
            "course_title": course.title if course else "",
            "title": curr.title,
            "version": curr.version,
            "status": active_ver.status if active_ver else "draft",
            "subjects": [s.to_dict() for s in subjects],
            "modules": modules_payload,
            "total_modules": len(modules_payload),
            "total_topics": total_topics,
            "total_concepts": total_concepts,
        }

    # ── 6. Declarative Package Import & Export ────────────────────────────────

    def import_from_provider(
        self,
        admin: 'central_platform.models.schema.User',
        provider: 'central_platform.providers.CurriculumProvider',
        curriculum_id: str,
        course_id: str
    ) -> Dict[str, Any]:
        """Fetch and import curriculum directly from a plugin provider (Phase 10)."""
        curriculum = provider.get_curriculum(curriculum_id)
        if not curriculum:
            raise ValueError(f"Curriculum '{curriculum_id}' not found in provider.")
        
        # Package it up in the expected declarative schema format
        package = {
            "title": curriculum.title,
            "version": curriculum.version,
            "modules": curriculum.metadata.get("modules", [])
        }
        return self.import_curriculum_package(admin, course_id, package, publish=True)

    def import_curriculum_package(
        self,
        admin: User,
        course_id: str,
        package: Dict[str, Any],
        publish: bool = False,
    ) -> Dict[str, Any]:
        """Import a declarative curriculum package JSON, validate it, and persist hierarchy."""
        if admin.role in (UserRole.STUDENT,):
            raise PermissionError("Students cannot import curricula.")

        course = self.db.get_course(course_id)
        if not course:
            raise ValueError(f"Course '{course_id}' not found.")

        # 1. Structural Validation First
        report = self.validate_curriculum(package)
        if not report.is_valid:
            errors_str = "; ".join(report.errors)
            raise ValueError(f"Import validation failed: {errors_str}")

        # 2. Create Curriculum & Version
        title = package.get("title") or package.get("name") or f"Curriculum for {course.title}"
        version_num = package.get("version") or package.get("version_num") or "v1.0.0"

        curriculum, ver = self.create_curriculum(
            admin=admin,
            course_id=course_id,
            title=title,
            initial_version=version_num,
        )

        # 3. Persist Subject if provided
        subject_name = package.get("subject") or package.get("subject_name")
        subj_id = None
        if subject_name:
            subj_id = f"sub-{uuid.uuid4().hex[:8]}"
            self.db.create_subject(Subject(id=subj_id, course_id=course_id, name=subject_name, code=package.get("subject_code", subject_name[:4].upper())))

        # 4. Ingest Modules, Topics, and Concepts
        concepts_list = package.get("concepts", [])
        modules_list = package.get("modules", [])

        if modules_list:
            for m_idx, m_data in enumerate(modules_list):
                mod = self.add_module(admin, ver.id, m_data.get("title", f"Module {m_idx+1}"), sequence_order=m_idx+1, subject_id=subj_id)
                for t_idx, t_data in enumerate(m_data.get("topics", [])):
                    top = self.add_topic(admin, ver.id, mod.id, t_data.get("title", f"Topic {t_idx+1}"), sequence_order=t_idx+1)
                    for c_data in t_data.get("concepts", []):
                        self.add_concept(
                            admin=admin,
                            version_id=ver.id,
                            topic_id=top.id,
                            concept_id=c_data["id"],
                            name=c_data.get("name", c_data["id"]),
                            description=c_data.get("description", ""),
                            difficulty=float(c_data.get("difficulty", 0.5)),
                            prerequisites=c_data.get("prerequisites", []),
                        )
        else:
            # Flattened concepts list: group automatically or place under Default Module
            mod = self.add_module(admin, ver.id, f"{subject_name or course.title} Core Module", sequence_order=1, subject_id=subj_id)
            top = self.add_topic(admin, ver.id, mod.id, "Core Concepts", sequence_order=1)
            for c_data in concepts_list:
                self.add_concept(
                    admin=admin,
                    version_id=ver.id,
                    topic_id=top.id,
                    concept_id=c_data["id"],
                    name=c_data.get("name", c_data["id"]),
                    description=c_data.get("description", ""),
                    difficulty=float(c_data.get("difficulty", 0.5)),
                    prerequisites=c_data.get("prerequisites", []),
                )

        # Store serialized schema_data on version
        package_canonical = dict(package)
        package_canonical["curriculum_id"] = curriculum.id
        package_canonical["version_id"] = ver.id
        package_canonical["version"] = version_num
        self.db.update_curriculum_version_schema(ver.id, json.dumps(package_canonical))

        # 5. Optionally Publish
        if publish:
            self.publish_curriculum_version(admin, ver.id)

        return {
            "curriculum_id": curriculum.id,
            "version_id": ver.id,
            "version": version_num,
            "title": title,
            "status": "published" if publish else "draft",
            "concept_count": len(concepts_list) or report.concept_count,
        }

    def export_curriculum_package(self, version_id: str) -> Dict[str, Any]:
        """Export curriculum version as a canonical declarative package with round-trip fidelity."""
        ver = self.db.get_curriculum_version(version_id)
        if not ver:
            raise ValueError(f"Curriculum version '{version_id}' not found.")

        if ver.schema_data and ver.schema_data != "{}":
            try:
                pkg = json.loads(ver.schema_data)
                pkg["version_id"] = ver.id
                pkg["version"] = ver.version_num
                pkg["status"] = ver.status
                pkg["published_at"] = ver.published_at
                return pkg
            except Exception as exc:
                logger.debug("Failed parsing version schema_data on export, falling back to relational tables: %s", exc)

        # Build dynamically from relational tables
        curr = self.db.get_curriculum(ver.curriculum_id)
        course = self.db.get_course(curr.course_id) if curr else None
        hierarchy = self.get_curriculum_hierarchy(ver.curriculum_id)

        # Extract all concepts flat for export schema
        all_concepts: List[Dict[str, Any]] = []
        for mod in hierarchy.get("modules", []):
            for top in mod.get("topics", []):
                for con in top.get("concepts", []):
                    all_concepts.append(con)

        return {
            "curriculum_id": ver.curriculum_id,
            "version_id": ver.id,
            "version": ver.version_num,
            "title": curr.title if curr else "",
            "course_id": curr.course_id if curr else "",
            "course_code": course.code if course else "",
            "status": ver.status,
            "published_at": ver.published_at,
            "concepts": all_concepts,
            "modules": hierarchy.get("modules", []),
        }
