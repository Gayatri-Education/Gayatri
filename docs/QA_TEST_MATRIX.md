# Gayatri QA Test Matrix

This matrix tracks all test scenarios, execution results, environment conditions, and verification evidence across QA phases.

| Test ID | QA Phase | Component | Scenario Description | Expected Outcome | Status | Execution Evidence / Notes |
|---------|----------|-----------|----------------------|------------------|--------|----------------------------|
| TM-0001 | QA-00 | Test Suite | Run complete pytest automated test suite (135+ files) | All tests execute clean | Passed | 856 passed in 118.87s |
| TM-0002 | QA-00 | Workspace | Directory structure & component baseline audit | Complete system map & findings log | Passed | QA_SYSTEM_MAP & QA_FINDINGS created |
| TM-0003 | QA-00 | Database | SQLite database schema verification (`gayatri_local.db`) | 47 tables mapped including fee management | Passed | Applied 003 migration; 47 tables verified (BUG-0006 Fixed) |
| TM-0004 | QA-00 | Local AI Model | Local GGUF model existence and configuration check | Valid model path resolved | In Progress | Added `qwen2.5-0.5b` to search list (BUG-0003) |
| TM-0005 | QA-00 | AI Gateway | AI Adapter exception & provider failure handling | Failures log and return `success=False` | Passed | Silent `MockAIAdapter` fallbacks removed (BUG-0001 Fixed) |
| TM-0006 | QA-00 | RBAC Engine | Parent role authorization check (`UserRole.PARENT`) | Resource access granted for linked child | Passed | Matrix updated & access check returns True (BUG-0004 Fixed) |
| TM-0007 | QA-00 | Desktop UI | App portal controllers (`app/portals/*`) context resolution | Real context returned from central DB | Failed | Controllers return stub dicts (BUG-0005) |
| TM-0008 | QA-00 | RAG Pipeline | RAG document cleaner failure resilience | Clean text returned or safe error | Failed | Exception swallowed in RAG cleaner (BUG-0007) |
| TM-0009 | QA-00 | HTTP Server | Authorization check on FastAPI routes (`server.py`) | Unauthenticated requests rejected 401/403 | Failed | Routes lack RBAC middleware (BUG-0008) |

---

## Suite Summary
- **Total Scenarios**: 9
- **Passed**: 5
- **Failed**: 3
- **In Progress**: 1
- **Blocked**: 0
