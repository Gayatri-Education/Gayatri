# Local Dependency & Packaging Forensic Audit

**Audit Date:** 2026-10-02T15:55:00+05:30  
**Repository:** `Gayatri-Education/Gayatri`  
**Python Runtime:** Python 3.12.10 (win32)  
**Package Build System:** Setuptools >= 70 via `setuptools.build_meta`  

---

## 1. Executive Summary

A comprehensive source code AST scan across all Python files in the repository was executed to extract all third-party imports and compare them against `pyproject.toml`, `requirements.txt`, and `requirements.lock`.

### Critical Blockers Identified & Resolved:
1. **Missing Runtime Dependencies in `requirements.txt`**:
   `fastapi`, `uvicorn`, `pyjwt`, `psutil`, `rank-bm25`, `pypdf`, and `pymupdf` were imported extensively across `central_platform/` and `tests/`, but were completely omitted from `requirements.txt`. This caused remote GitHub Actions CI to fail immediately with `ModuleNotFoundError: No module named 'fastapi'`.
2. **Packaging Discovery Omission in `pyproject.toml`**:
   The setuptools package discovery configuration was restricted to `include = ["app*", "core*", "tests*"]`. Any installation via `pip install .` or `pip install -e .` completely omitted the entire `central_platform` and `adapters` trees (finding only 21 of 50 packages).
3. **Stale Lockfile (`requirements.lock`)**:
   `requirements.lock` was frozen against an older iteration that lacked `fastapi`, `uvicorn`, `psutil`, and `pyjwt`.

---

## 2. Exhaustive Third-Party Import Scan Results

An AST parse of every Python file in the repository (excluding `.git`, `.venv`, and `scratch/`) identified the following external packages:

| Imported Module | Source Location | Classification | Declared in `requirements.txt` (Before) | Declared in `requirements.txt` (After) | Status |
|---|---|---|---|---|---|
| `fastapi` | `central_platform/api/*`, `auth/*`, 25+ test suites | **CORE RUNTIME** | ❌ Missing | ✅ `fastapi>=0.110.0` | **RESOLVED** |
| `uvicorn` | `central_platform/api/server.py`, scripts | **CORE RUNTIME** | ❌ Missing | ✅ `uvicorn>=0.28.0` | **RESOLVED** |
| `pydantic` | `central_platform/models/*`, `api/schemas.py`, RAG | **CORE RUNTIME** | ✅ `pydantic>=2.0` | ✅ `pydantic>=2.0` | VERIFIED |
| `httpx` | `central_platform/ai/adapters.py`, cloud providers | **CORE RUNTIME** | ✅ `httpx>=0.27.0` | ✅ `httpx>=0.27.0` | VERIFIED |
| `jwt` (`PyJWT`) | `central_platform/auth/tokens.py`, `dependencies.py` | **CORE RUNTIME** | ❌ Missing | ✅ `pyjwt>=2.8.0` | **RESOLVED** |
| `cryptography` | `central_platform/auth/tokens.py`, security, cache | **CORE RUNTIME** | ✅ `cryptography>=43.0.0` | ✅ `cryptography>=43.0.0` | VERIFIED |
| `psutil` | `central_platform/performance/profiler.py`, scripts | **CORE RUNTIME** | ❌ Missing | ✅ `psutil>=5.9.0` | **RESOLVED** |
| `rank_bm25` | `central_platform/rag/service.py`, local RAG | **CORE RUNTIME** | ❌ Missing | ✅ `rank-bm25>=0.2.2` | **RESOLVED** |
| `pypdf` | `central_platform/rag/parsers.py` | **KNOWLEDGE INGESTION** | ❌ Missing | ✅ `pypdf>=4.0.0` | **RESOLVED** |
| `pymupdf` (`fitz`) | `central_platform/rag/parsers.py` | **KNOWLEDGE INGESTION** | ❌ Missing | ✅ `pymupdf>=1.24.0` | **RESOLVED** |
| `PySide6` | `app/ui/*`, `app/windows/*`, desktop shell | **DESKTOP UI** | ✅ `PySide6>=6.11.0` | ✅ `PySide6>=6.11.0` | VERIFIED |
| `llama_cpp` | `central_platform/ai/llama_cpp_runner.py` | **LOCAL SLM** | ✅ `llama-cpp-python>=0.3.0` | ✅ `llama-cpp-python>=0.3.0` | VERIFIED |
| `pytest` | `tests/*` | **DEV / TEST** | ✅ `pytest>=8.0.0` | ✅ `pytest>=8.0.0` | VERIFIED |
| `pytestqt` | `tests/*` | **DEV / TEST** | ✅ `pytest-qt>=4.4.0` | ✅ `pytest-qt>=4.4.0` | VERIFIED |
| `ruff` | CI linting | **DEV / TOOLING** | ✅ `ruff>=0.6.0` | ✅ `ruff>=0.6.0` | VERIFIED |
| `torch` | `training/train_colab.py`, `train_slm.py` | **TRAINING ONLY** | ❌ Excluded (Dev/Colab) | ❌ Excluded | INTENTIONAL |
| `transformers` | `training/train_colab.py`, `train_slm.py` | **TRAINING ONLY** | ❌ Excluded (Dev/Colab) | ❌ Excluded | INTENTIONAL |
| `peft` | `training/train_colab.py`, `train_slm.py` | **TRAINING ONLY** | ❌ Excluded (Dev/Colab) | ❌ Excluded | INTENTIONAL |
| `trl` | `training/train_colab.py`, `train_slm.py` | **TRAINING ONLY** | ❌ Excluded (Dev/Colab) | ❌ Excluded | INTENTIONAL |
| `datasets` | `training/train_colab.py`, `train_slm.py` | **TRAINING ONLY** | ❌ Excluded (Dev/Colab) | ❌ Excluded | INTENTIONAL |
| `psycopg2` | `central_platform/db.py` (optional backend) | **OPTIONAL DRIVER** | ❌ Optional | ❌ Optional | INTENTIONAL |

*Note: ML training packages (`torch`, `transformers`, `peft`, `trl`, `datasets`) are strictly restricted to scripts in `training/` designed to run in external GPU environments (e.g. Google Colab). They are intentionally not required for the local or edge inference runtime.*

---

## 3. Package Discovery & Build Test Evidence

Prior to reconciliation, running package discovery via Setuptools:
```python
packages = setuptools.find_packages(where=".", include=["app*", "core*", "tests*"])
# Result: 21 packages found (central_platform was completely excluded)
```

After updating `pyproject.toml` to `include = ["app*", "core*", "central_platform*", "adapters*", "tests*"]`:
```python
packages = setuptools.find_packages(where=".", include=["app*", "core*", "central_platform*", "adapters*", "tests*"])
# Result: 50 packages found
```

### Installation Verification:
An isolated editable package build was executed:
```bash
pip install --no-deps -e .
```

**Result:**
```text
Building editable for gayatri-ai (pyproject.toml): finished with status 'done'
Created wheel for gayatri-ai: filename=gayatri_ai-5.0.0-0.editable-py3-none-any.whl size=15638
Successfully installed gayatri-ai-5.0.0
```

---

## 4. Reconciled `requirements.txt` Specification

The authoritative `requirements.txt` is now:

```text
# Gayatri AI — Base Dependencies
# Development install: pip install -r requirements.txt
# Reproducible / pinned release install: pip install -r requirements.lock (Audit #PACKAGE-001)

# Core runtime
PySide6>=6.11.0
llama-cpp-python>=0.3.0
httpx>=0.27.0
cryptography>=43.0.0
pydantic>=2.0
fastapi>=0.110.0
uvicorn>=0.28.0
pyjwt>=2.8.0
psutil>=5.9.0
rank-bm25>=0.2.2

# Document & knowledge processing
pypdf>=4.0.0
pymupdf>=1.24.0

# Dev / testing
pytest>=8.0.0
pytest-qt>=4.4.0
ruff>=0.6.0
```
