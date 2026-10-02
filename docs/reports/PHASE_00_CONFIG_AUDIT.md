# Phase 00 — Configuration Consistency & Model Manifest Audit

**Document:** `docs/reports/PHASE_00_CONFIG_AUDIT.md`  
**Governing Document:** `GAYATRI_PHASE_BY_PHASE_DEVELOPMENT_PLAN.md` (Section 12.0)  
**Inspection Date:** 2026-10-01  
**Commit SHA:** `bf47a63`  

---

## 1. Executive Summary

An audit of platform configuration files, model manifests, environment variables, and fallback settings was performed to identify drift, contradictory identifiers, and silent runtime failure vectors.

---

## 2. Model Manifest vs Runtime Configuration Drift

| Attribute | `model_manifest.json` | `core/config.py` | Status |
|---|---|---|---|
| **Authoritative Model ID** | `gayatri-chem-qwen2.5-0.5b-v4` | Implicit (searches list of 8 filenames) | **CONTRADICTION** |
| **Model Filename** | `qwen2.5-0.5b-instruct-q4_k_m.gguf` | Falls back to `Gayatri-Tutor-v3-Q4_K_M.gguf` | **CONTRADICTION** |
| **Quantization** | `Q4_K_M` | Varies (`Q4_K_M`, `Q8_0`) | **INCONSISTENT** |
| **Context Length** | 8192 | 4096 (in `core/inference/service.py`) | **CONTRADICTION** |
| **Chat Template** | `chatml` | Custom prompt templates in `core/` | **DRIFT** |
| **Disk Presence** | 0 files matching on disk | 0 files matching on disk | **MISSING ON DISK** |
| **Manifest Checksum** | `e3b0c442...` (SHA256 of empty string) | None | **INVALID CHECKSUM** |

### Key Forensic Findings:
1. `model_manifest.json` hardcodes `gayatri-chem-` into its identifier, coupling the local model definition to Chemistry.
2. The checksum in `model_manifest.json` is `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`, which is the standard SHA-256 hash of a 0-byte (empty) string.
3. When no model file exists on disk, `core/config.py` defaults to returning `"Gayatri-Tutor-v3-Q4_K_M.gguf"` which also does not exist on disk, causing unhandled runtime load failures if local llama.cpp is invoked without cloud fallback.

---

## 3. Environment Configuration Audit

- **Database Configuration:** `DATABASE_URL` is parsed by `central_platform/db.py`. Defaults to `sqlite:///gayatri_local.db` if unspecified. PostgreSQL driver is imported optionally.
- **Provider API Keys:**
  - `OPENAI_API_KEY`: Checked by `central_platform/ai/adapters.py`.
  - `ANTHROPIC_API_KEY`: Checked by `central_platform/ai/adapters.py`.
  - `GEMINI_API_KEY`: Checked by `central_platform/ai/adapters.py`.
- **JWT & Encryption Secrets:**
  - `JWT_SECRET_KEY`: Defaults to a development fallback string if not set in `.env`.
  - `local_auth_tokens.json`: Contains pre-generated static test tokens committed in the project root (tracked in BUG-ARCH-003).

---

## 4. Remediation Plan (Scheduled for Phase 8 / Phase 9)
1. Establish a single authoritative `ModelRegistry` in `central_platform/ai/models.py`.
2. Clean `model_manifest.json` of subject-specific naming (`gayatri-slm-qwen2.5-0.5b`).
3. Enforce clear exception raising with user-facing guidance when local model files are missing on disk, rather than falling back to nonexistent legacy filenames.
