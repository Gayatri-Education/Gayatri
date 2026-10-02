# Phase 03 Execution Plan — Generic Curriculum & Versioned Learning Graph

**Document:** `docs/reports/PHASE_03_PLAN.md`  
**Governing Document:** `GAYATRI_PHASE_BY_PHASE_DEVELOPMENT_PLAN.md` (Section 12.3)  
**Target Repository:** `https://github.com/Gayatri-Education/Gayatri`  
**Branch:** `master`  
**Date:** 2026-10-01  

---

## 1. Phase Objective

Replace Chemistry-specific curriculum logic with an extensible, data-driven course curriculum engine. The engine must natively ingest and resolve curricula for **Chemistry, Physics, History, Programming**, or arbitrary school-created course structures without source-code changes, while cleanly decoupling Chemistry-specific logic into dedicated adapter territory and preserving full backward compatibility for existing regression suites.

---

## 2. Forensic Findings & Architectural Decoupling Strategy

1. **Current Couplings Identified:**
   - `core/curriculum/resolver.py`: Contains hardcoded `CONCEPT_KEYWORD_MAP` (Chemistry-only) and returns hardcoded fallback `chem_general_undetermined` with topic `"General Chemistry"`.
   - `core/curriculum/validator.py`: Has hardcoded `ALLOWED_DOMAINS` restricting valid domains to 5 Chemistry disciplines.
   - `core/curriculum/models.py`: Defines `CurriculumDomain` with NCERT/CBSE chemistry manifest assumptions.
   - `core/curriculum/loader.py`: Hardcoded path assumptions to `ncert_class11_12.json` and Chemistry manifest.
2. **Target Architecture:**
   - **Generic Taxonomy Hierarchy:** `CourseVersion` → `Curriculum` → `Subject` → `Module` → `Topic` → `Concept` → `Prerequisite`. Optional levels supported for flat or flexible course structures.
   - **Decoupled Chemistry Adapter:** Chemistry keyword maps and domain knowledge are isolated in `core/curriculum/chemistry_adapter.py`.
   - **Pluggable & Course-Scoped `ConceptResolver`:** Resolves concept IDs using:
     1. Explicit concept ID lookup.
     2. Active course curriculum manifest and metadata.
     3. Course-scoped keyword aliases and semantic matching.
     4. Safe course-neutral unknown result (`undetermined`, `general`, `unspecified`) instead of Chemistry defaults.
     5. Backward-compatibility routing: when `course_id` is omitted or points to Chemistry, seamlessly delegates to the Chemistry adapter so that all 874 existing tests remain 100% green.
   - **Namespaced Concept IDs:** Format helper `format_concept_id(course_id, version_id, concept_key)` produces collision-proof IDs: `course:<cid>:version:<vid>:concept:<key>`, with dual-lookup support for legacy keys (`chem_*`, `thermo.*`).
   - **Generalized Graph & DAG Validation:**
     - Cycle detection across arbitrary graph depths.
     - Missing prerequisite detection.
     - Orphan concept detection.
     - Prerequisite chain traversal scoped by course and version.

---

## 3. Planned Implementation Details

### Step 1: Generic Curriculum Models (`core/curriculum/models.py`)
- Enhance `CurriculumDomain`, `CurriculumManifest`, and introduce generic domain structures:
  - `GenericConcept`: `id`, `name`, `description`, `difficulty`, `prerequisites`, `keywords`, `aliases`, `learning_outcomes`, `metadata`.
  - `GenericTopic`: `id`, `name`, `concepts`, `sequence_order`.
  - `GenericModule`: `id`, `name`, `topics`, `sequence_order`.
  - `GenericCurriculum`: `id`, `course_id`, `version_id`, `title`, `modules`, `all_concepts_map`.
  - Helpers for namespacing and legacy ID normalization.

### Step 2: Dedicated Chemistry Adapter (`core/curriculum/chemistry_adapter.py`)
- Move `CONCEPT_KEYWORD_MAP` out of generic `resolver.py` into `ChemistryCurriculumAdapter`.
- Register the Chemistry adapter with the central curriculum provider registry.

### Step 3: Generic & Extensible `ConceptResolver` (`core/curriculum/resolver.py`)
- Refactor `ConceptResolver` to be course-aware.
- Accept optional `course_id` and `course_version_id`.
- Look up active course curriculum and its registered adapter/manifest.
- If no course is specified or course is Chemistry, fall back to Chemistry adapter for 100% backward compatibility.
- Safe unknown result returns `ResolvedConcept(domain="General", chapter="General", topic="General", subtopic="General", concept_id="general_undetermined", confidence=0.3)`.

### Step 4: Extensible `CurriculumValidator` (`core/curriculum/validator.py`)
- Remove hardcoded `ALLOWED_DOMAINS` restriction.
- Validate domain names dynamically against manifest or accept arbitrary valid string domains.
- Retain strict DAG cycle detection, missing prerequisite detection, orphan concept warnings, and difficulty range validation.

### Step 5: Generic Fixture Curricula for 4 Required Disciplines
Create canonical fixture manifests:
1. **Chemistry:** `data/curriculum/chemistry/ncert_class11_12.json`
2. **Physics:** `data/curriculum/physics/mechanics_grade11.json` (Kinematics, Newton's Laws, Work-Energy-Power, Gravitation)
3. **History:** `data/curriculum/history/world_history.json` (Ancient Mesopotamia, Roman Republic, Middle Ages, Industrial Revolution)
4. **Programming:** `data/curriculum/python/beginner.json` & `data/curriculum/programming/intro_cs.json` (Variables, Control Flow, Functions, OOP, Data Structures)

### Step 6: Learning Graph & Scoped DAG Validation (`central_platform/learning/graph.py` & `core/knowledge_graph.py`)
- Ensure `LearningGraph` and `LearningDependencyGraph` can load and validate any course curriculum.
- Verify prerequisite traversal and cycle detection are strictly scoped to the course/version.

---

## 4. Test Strategy & Acceptance Gate

Create dedicated test suite `tests/test_phase03_generic_curriculum.py` covering:
1. **Four-Course Ingestion Test:** Ingest Chemistry, Physics, History, Programming through the same generic engine.
2. **Zero-Chemistry Dependency Verification:** Disable/mock the Chemistry adapter and demonstrate that Physics, History, and Programming curricula load, validate, resolve concepts, and traverse DAGs with zero Chemistry code paths.
3. **DAG Cycle & Missing Prerequisite Detection:** Verify cycle detection across all 4 courses.
4. **Cross-Course Concept Collision Resistance:** Verify that concepts sharing identical local names across courses (e.g., "Thermodynamics" in Physics vs Chemistry, or "Functions" in Math vs Programming) have distinct, collision-free namespaced IDs.
5. **Full Regression Gate:** All 874 existing tests pass without regressions or modifications to existing assertions.

---

## 5. Artifacts to Generate Upon Completion

- `docs/reports/PHASE_03_PLAN.md` (this plan)
- `docs/reports/PHASE_03_TEST_REPORT.md`
- `docs/reports/PHASE_03_TEST_RESULTS.json`
- Updates to `PROJECT_STATE.yaml`, `DEVELOPMENT_LOG.md`, `BUG_REGISTER.md`, `GITHUB_SYNC_QUEUE.md`
