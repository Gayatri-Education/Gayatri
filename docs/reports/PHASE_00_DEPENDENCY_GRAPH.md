# Gayatri Platform — Initial Dependency Graph & Coupling Analysis

**Document:** `docs/reports/PHASE_00_DEPENDENCY_GRAPH.md`  
**Generated At:** 2026-10-01T11:26:00+05:30  

## 1. Top-Level Subsystem Coupling Matrix

| Calling Subsystem | Target Subsystem | Import Count |
|-------------------|------------------|--------------|
| `central_platform` | `central_platform` | 294 |
| `core` | `core` | 181 |
| `app` | `core` | 30 |
| `central_platform` | `core` | 15 |
| `app` | `app` | 9 |
| `core` | `legacy` | 3 |
| `app` | `central_platform` | 3 |
| `core` | `app` | 1 |
| `legacy` | `core` | 1 |

## 2. Legacy Module Dependency Infiltration

The following modules import from `legacy`:

| Caller File | Imported Legacy Module |
|-------------|------------------------|
| `core/inference/service.py` | `legacy.agents.default_agents` |
| `core/runtimes/chemistry.py` | `legacy.agents.default_agents` |
| `core/runtimes/general.py` | `legacy.agents.default_agents` |

## 3. High In-Degree Central Modules (Most Heavily Depended Upon)

| Module Prefix | In-Degree (Number of referencing files) |
|---------------|-----------------------------------------|
| `central_platform.models` | 44 |
| `core.tutor` | 35 |
| `central_platform.api` | 34 |
| `core.config` | 29 |
| `central_platform.events` | 26 |
| `core.learning` | 25 |
| `central_platform.db` | 25 |
| `central_platform.auth` | 23 |
| `central_platform.ai` | 22 |
| `core.providers` | 21 |
| `central_platform.teacher` | 20 |
| `central_platform.assessment` | 17 |
| `core.security` | 15 |
| `central_platform.slr` | 15 |
| `central_platform.learning` | 13 |
| `core.rag` | 12 |
| `central_platform.notifications` | 12 |
| `core.agents` | 9 |
| `core.assessment` | 9 |
| `central_platform.rag` | 9 |
| `core.settings` | 8 |
| `core.errors` | 8 |
| `central_platform.sync` | 8 |
| `core.db` | 7 |
| `core.curriculum` | 7 |

## 4. Key Cross-Boundary Circular or Problematic Couplings

1. **Core to Legacy Coupling:** `core.inference.service` and `core.runtimes.*` call into `legacy.agents.default_agents`.
2. **Core to Hardcoded Chemistry Coupling:** `core.curriculum` and `core.tutor` hardcode chemistry concept IDs and keyword catalogs.
3. **App Bridge to Server Couplings:** `app.bridge.facade` directly calls live server APIs while hardcoding demo student rosters.
