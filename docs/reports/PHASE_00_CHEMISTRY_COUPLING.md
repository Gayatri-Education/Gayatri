# Phase 00 — Chemistry Domain Coupling & Infiltration Audit

**Document:** `docs/reports/PHASE_00_CHEMISTRY_COUPLING.md`  
**Governing Document:** `GAYATRI_PHASE_BY_PHASE_DEVELOPMENT_PLAN.md` (Section 12.0)  
**Inspection Date:** 2026-10-01  
**Commit SHA:** `bf47a63`  

---

## 1. Executive Summary

A comprehensive automated scan for Chemistry-specific keywords (`chemistry`, `thermodynamics`, `hess`, `ncert`, `chemical`, `crs-chem-101`, `chem_101`) across all source code outside `adapters/chemistry/`, `tests/`, and `docs/` identified **115 coupled files**.

Gayatri currently cannot run in an arbitrary domain (e.g. History, Mathematics, Programming) without triggering Chemistry assumptions or hardcoded fallbacks.

---

## 2. Infiltration Breakdown by Subsystem

### 2.1 Core Curriculum & Concept Resolution
- **Files:** `core/curriculum/catalog.py`, `core/curriculum/resolver.py`, `core/curriculum/graph.py`
- **Issue:** Concept resolution matches incoming queries against hardcoded keyword tables for NCERT Chemistry Class 11 and 12 (e.g. `hesss_law`, `gibbs_free_energy`, `ionization_enthalpy`, `spdf_orbitals`).
- **Impact:** Any subject without hardcoded Chemistry entries falls back to a generic error or misroutes to thermodynamics.

### 2.2 Generic Tutor Core & Orchestrator
- **Files:** `core/orchestrator.py`, `core/runtimes/chemistry.py`, `core/tutor/chemistry_tools.py`
- **Issue:** Chemistry equation balancing and periodic table tools are wired directly into the generic `TutorOrchestrator` rather than being provided dynamically via course capability policies.
- **Impact:** Generic tutor cannot operate if Chemistry tool dependencies fail or if another course disables tools.

### 2.3 Application UI & Bridge Facade
- **Files:** `app/bridge/facade.py`, `app/ui/index.html`
- **Issue:**
  - `app/ui/index.html` contains hardcoded tab labels: `"Chemistry sessions"` and `"General sessions"`.
  - `app/bridge/facade.py` hardcodes default parameters: `course_id = "crs-chem-101"` and `chapter = "thermodynamics"`.
- **Impact:** Students browsing the web interface or desktop shell are presented with fixed Chemistry UI elements regardless of actual course enrollments.

### 2.4 Knowledge & RAG Storage Defaults
- **Files:** `core/rag/store.py`, `core/rag/retriever.py`, `scripts/ingest_knowledge.py`
- **Issue:** `provenance_type` defaults to `'NCERT'` and assumes Chemistry chapter indices.
- **Impact:** Ingesting non-NCERT or non-Chemistry textbooks leads to corrupted metadata provenance tags.

---

## 3. High-Priority Coupled File Registry (Top 25)

1. `app/bridge/facade.py`
2. `app/ui/index.html`
3. `app/ui/teacher_portal.html`
4. `core/orchestrator.py`
5. `core/curriculum/catalog.py`
6. `core/curriculum/resolver.py`
7. `core/curriculum/graph.py`
8. `core/runtimes/chemistry.py`
9. `core/tutor/chemistry_tools.py`
10. `core/tutor/state.py`
11. `core/rag/store.py`
12. `core/rag/retriever.py`
13. `core/assessment/engine.py`
14. `central_platform/ai/query_understanding.py`
15. `central_platform/ai/response_planner.py`
16. `central_platform/learning/graph.py`
17. `central_platform/learning/mastery.py`
18. `central_platform/portals/student.py`
19. `central_platform/portals/teacher.py`
20. `scripts/ingest_knowledge.py`
21. `scripts/seed_local_environment.py`
22. `scripts/generate_slm_training_data.py`
23. `scripts/validate_training_dataset.py`
24. `model_manifest.json`
25. `server.py`

---

## 4. Extraction & Decoupling Strategy (Phases 3, 9, 15)

1. **Extract to `adapters/chemistry/`:**
   - Move `chemistry_tools.py`, equation balancers, and stoichiometry modules into `adapters/chemistry/tools.py`.
   - Move Chemistry misconception taxonomies into `adapters/chemistry/misconceptions.py`.
   - Package NCERT Chemistry curriculum data into a course manifest (`adapters/chemistry/chemistry_manifest.json`).
2. **Data-Driven Generic Core:**
   - Redesign curriculum resolution to query active course version database records rather than hardcoded Python maps.
   - Inject course tools dynamically based on `course_version.tool_policy`.
3. **CI Static Guard:**
   - Add automated test failing if any file in `core/` or `central_platform/` contains hardcoded Chemistry keywords.
