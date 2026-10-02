"""Gayatri AI — Curriculum domain models.

Typed representations of the NCERT/CBSE chemistry curriculum manifest.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CurriculumDomain:
    """A single domain (e.g. Thermodynamics, Inorganic Chemistry) from the manifest."""
    name: str
    classes: list[str] = field(default_factory=list)
    chapters: list[str] = field(default_factory=list)
    topics: list[str] = field(default_factory=list)
    subtopics: list[str] = field(default_factory=list)
    learning_outcomes: list[str] = field(default_factory=list)
    prerequisites: list[str] = field(default_factory=list)

    def domain_id(self) -> str:
        """Stable snake_case ID derived from the domain name."""
        return self.name.lower().replace(" ", "_").replace("-", "_")

    def topic_ids(self) -> list[str]:
        """Return stable snake_case topic IDs for each topic string."""
        return [t.lower().replace(" ", "_").replace(",", "").replace("'", "").replace("-", "_")
                for t in self.topics]

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "domain_id": self.domain_id(),
            "classes": self.classes,
            "chapters": self.chapters,
            "topics": self.topics,
            "subtopics": self.subtopics,
            "learning_outcomes": self.learning_outcomes,
            "prerequisites": self.prerequisites,
        }


@dataclass
class CurriculumManifest:
    """The full chemistry curriculum manifest, a collection of domains."""
    domains: list[CurriculumDomain] = field(default_factory=list)

    def get_domain(self, name: str) -> CurriculumDomain | None:
        """Look up a domain by name (case-insensitive)."""
        for d in self.domains:
            if d.name.lower() == name.lower():
                return d
        return None

    def all_topics(self) -> list[str]:
        """Return all topics across all domains."""
        return [topic for d in self.domains for topic in d.topics]

    def all_topic_ids(self) -> list[str]:
        """Return all stable topic IDs across all domains."""
        return [tid for d in self.domains for tid in d.topic_ids()]

    def domain_names(self) -> list[str]:
        """Return all domain names."""
        return [d.name for d in self.domains]

    def supported_classes(self) -> list[str]:
        """Return sorted unique class levels across all domains."""
        seen = set()
        for d in self.domains:
            seen.update(d.classes)
        return sorted(seen)


# ── Generic Course-Independent Curriculum Hierarchy ─────────────────────

def format_concept_id(course_id: str, version_id: str, concept_key: str) -> str:
    """Produce a canonical namespaced concept ID to guarantee cross-course uniqueness."""
    clean_course = (course_id or "default").strip().lower().replace(" ", "_")
    clean_ver = (version_id or "1.0").strip().lower().replace(" ", "_")
    clean_key = (concept_key or "").strip().lower().replace(" ", "_")
    return f"course:{clean_course}:version:{clean_ver}:concept:{clean_key}"


def parse_concept_id(concept_id: str) -> dict[str, str]:
    """Parse a concept ID into constituent course, version, and local key components."""
    if not concept_id:
        return {"course_id": "", "version_id": "", "concept_key": ""}
    
    parts = concept_id.split(":")
    if len(parts) == 6 and parts[0] == "course" and parts[2] == "version" and parts[4] == "concept":
        return {
            "course_id": parts[1],
            "version_id": parts[3],
            "concept_key": parts[5],
        }
    
    # Handle legacy identifiers (e.g. chem_thermo_hess or thermo.first_law)
    return {
        "course_id": "legacy",
        "version_id": "1.0",
        "concept_key": concept_id,
    }


@dataclass
class GenericConcept:
    """A single conceptual unit of learning in any academic discipline."""
    id: str
    name: str
    description: str = ""
    difficulty: float = 0.5
    prerequisites: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)
    learning_outcomes: list[str] = field(default_factory=list)
    domain: str = ""
    chapter: str = ""
    topic: str = ""
    subtopic: str = ""
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "difficulty": self.difficulty,
            "prerequisites": self.prerequisites,
            "keywords": self.keywords,
            "aliases": self.aliases,
            "learning_outcomes": self.learning_outcomes,
            "domain": self.domain,
            "chapter": self.chapter,
            "topic": self.topic,
            "subtopic": self.subtopic,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> GenericConcept:
        return cls(
            id=data.get("id") or data.get("concept_id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            difficulty=float(data.get("difficulty", 0.5)),
            prerequisites=list(data.get("prerequisites", [])),
            keywords=list(data.get("keywords", [])),
            aliases=list(data.get("aliases", [])),
            learning_outcomes=list(data.get("learning_outcomes", [])),
            domain=data.get("domain", ""),
            chapter=data.get("chapter", ""),
            topic=data.get("topic", ""),
            subtopic=data.get("subtopic", ""),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass
class GenericTopic:
    """A topic grouping related concepts within a module."""
    id: str
    name: str
    sequence_order: int = 1
    concepts: list[GenericConcept] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "sequence_order": self.sequence_order,
            "concepts": [c.to_dict() for c in self.concepts],
        }


@dataclass
class GenericModule:
    """A high-level module (or chapter) grouping multiple topics."""
    id: str
    name: str
    sequence_order: int = 1
    topics: list[GenericTopic] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "sequence_order": self.sequence_order,
            "topics": [t.to_dict() for t in self.topics],
        }


@dataclass
class GenericCurriculum:
    """Canonical data-driven course curriculum containing modules, topics, and concepts."""
    id: str
    course_id: str
    version_id: str = "1.0"
    title: str = ""
    subject: str = ""
    modules: list[GenericModule] = field(default_factory=list)
    concepts: list[GenericConcept] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def all_concepts(self) -> list[GenericConcept]:
        """Return all concepts, merging top-level concepts and nested topic concepts."""
        seen = {}
        for c in self.concepts:
            seen[c.id] = c
        for m in self.modules:
            for t in m.topics:
                for c in t.concepts:
                    if c.id not in seen:
                        seen[c.id] = c
        return list(seen.values())

    def get_concept(self, concept_id: str) -> GenericConcept | None:
        """Find concept by exact ID, namespaced ID, or alias/name."""
        for c in self.all_concepts():
            if c.id == concept_id:
                return c
            # Check parsed key
            parsed = parse_concept_id(c.id)
            if parsed["concept_key"] == concept_id:
                return c
            # Check aliases
            if concept_id.lower() in [a.lower() for a in c.aliases]:
                return c
        return None

    def all_concept_ids(self) -> list[str]:
        return [c.id for c in self.all_concepts()]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "course_id": self.course_id,
            "version_id": self.version_id,
            "title": self.title,
            "subject": self.subject,
            "modules": [m.to_dict() for m in self.modules],
            "concepts": [c.to_dict() for c in self.concepts],
            "metadata": self.metadata,
        }

