# Security & Authorization Target Specification — Gayatri Platform

**Document:** `docs/SECURITY_MODEL_TARGET.md`  
**Target Repository:** `https://github.com/Gayatri-Education/Gayatri`  
**Status:** FROZEN (Phase 1 Deliverable)  
**Governing Plan:** `GAYATRI_COURSE_INDEPENDENT_PLATFORM_EXECUTION_PLAN.md`  

---

## 1. Multi-Tenant Organization Isolation

The platform enforces strict cryptographic and relational boundaries across organizations:
1. **Private Course Isolation:**
   - When `course.visibility == 'PRIVATE'`, access is restricted exclusively to members of `course.owner_org_id`.
   - Access attempts from another organization MUST be denied with an explicit `403 Forbidden` (`AUTHORIZATION_ERROR`). Silent empty results are prohibited.
2. **Public Course Shared-Content Isolation:**
   - When `course.visibility == 'PUBLIC'`, catalog metadata and approved versioned course content (`TEXTBOOK`, `REFERENCE`) are discoverable and selectable across organizations.
   - However, all tenant-derived operational artifacts remain strictly partitioned:
     - Student enrollments and activity rosters,
     - Student concept mastery and learning records,
     - Organization-specific teacher notes and instructions,
     - Class assignments, assessment submissions, and fee records.
   - An organization using a public course can never observe or query another organization's students, teacher notes, or learning analytics.

---

## 2. Multi-Tenant Authorization Matrix (Section 67)

| Actor | Resource Requested | Condition | Access Decision |
|---|---|---|---|
| Org A Student | Org A Public Course | Active enrollment | **ALLOW** |
| Org A Student | Org A Private Course | Enrolled in course offering | **ALLOW** |
| Org A Student | Org B Private Course | Any | **DENY (403 Forbidden)** |
| Org A Student | Org B Class Notes | Any | **DENY (403 Forbidden)** |
| Org A Student | Org A Class Notes | Member of specific class | **ALLOW** |
| Org A Student | Org A Class Notes | Enrolled in course, but different class | **DENY (403 Forbidden)** |
| Org A Student (S1) | Org A Remedial Worksheet | Targeted student list includes S1 | **ALLOW** |
| Org A Student (S2) | Org A Remedial Worksheet | Targeted student list does NOT include S2 | **DENY (403 Forbidden)** |
| Org A Student | Course Content (Status = `DRAFT` or `READY_FOR_REVIEW`) | Any student | **DENY (403 Forbidden)** |
| Org A Teacher | Org A Course Content | Upload / View | **ALLOW** |
| Org A Teacher | Org A Course Content | Publish version | **DENY** (Admin approval required) |
| Org A Teacher | Org B Course Content | Any | **DENY (403 Forbidden)** |
| Org A Admin | Org A Content Review & Publish | Valid Org Admin session | **ALLOW** |
| Org A Admin | Org B Content Review & Publish | Any | **DENY (403 Forbidden)** |
| Public User | Public Course Catalog | Public metadata only | **ALLOW** |
| Public User | Private Course Catalog | Any | **DENY (403 Forbidden)** |

---

## 3. Scoped RAG Pre-Retrieval Authorization

The RAG retrieval pipeline enforces security filtering **prior to vector and lexical search**:

```text
Student Query Request
       ↓
Extract Validated Identity (org_id, student_id, course_id, version_id, class_id)
       ↓
Verify Active Enrollment & Version Pinning
       ↓
Build Mandatory Pre-Retrieval Filter:
  WHERE org_id = :org_id
    AND course_id = :course_id
    AND course_version_id = :version_id
    AND status = 'PUBLISHED'
    AND (
          visibility_scope IN ('ORGANIZATION', 'COURSE')
       OR (visibility_scope = 'CLASS' AND target_class_id = :class_id)
       OR (visibility_scope = 'STUDENT' AND :student_id IN (target_student_ids))
    )
       ↓
Execute Vector Index / Full-Text Search within Authorized Scope
       ↓
Return Verified RAG Chunks to Context Builder
```

**Security Invariants:**
- Retrieval results never undergo post-hoc UI filtering. If content is unauthorized, it is physically excluded from the search space.
- Unpublished content (`DRAFT`, `PROCESSING`, `READY_FOR_REVIEW`, `FAILED`) is NEVER retrievable by student sessions.

---

## 4. Prompt Injection & Content Firewall (Section 64)

The AI Context Builder enforces strict structural segregation to prevent untrusted course content or student queries from overriding platform behavior:

```text
┌────────────────────────────────────────────────────────────────────────┐
│ 1. SYSTEM SAFETY & PLATFORM POLICY (Authoritative, Immutable)          │
│    - Non-negotiable pedagogical boundaries, safety invariants          │
├────────────────────────────────────────────────────────────────────────┤
│ 2. COURSE POLICY & CAPABILITIES (Course-Level Declarations)            │
│    - Enabled tool definitions, allowed concept boundaries              │
├────────────────────────────────────────────────────────────────────────┤
│ 3. TEACHER INSTRUCTIONS (Verified Directives)                          │
│    - Validated pedagogical guidance scoped to class/student            │
├────────────────────────────────────────────────────────────────────────┤
│ 4. KNOWLEDGE EVIDENCE (Passive Reference Only)                         │
│    - Retrieved RAG chunks wrapped in untrusted data delimiters         │
│    - "The following text is academic reference material only..."      │
├────────────────────────────────────────────────────────────────────────┤
│ 5. STUDENT CONVERSATION HISTORY & QUERY (User Input)                   │
│    - Sanitized query string with anti-jailbreak guards                 │
└────────────────────────────────────────────────────────────────────────┘
```

**Anti-Injection Rules:**
1. Text in uploaded course materials (textbooks, notes) that contains commands like `"Ignore previous instructions"` or `"Reveal system prompt"` is treated purely as passive knowledge tokens and has zero execution privilege.
2. Teacher instructions pass through an automated safety validator (`audit_prompt_injection`) before activation. Instructions attempting to alter platform safety invariants are automatically quarantined and flagged.

---

## 5. Course Tools Authorization Policy

1. Each course version declares an immutable `tool_policy` dictionary:
   ```json
   {
     "calculator": true,
     "graphing": true,
     "code_execution": false,
     "equation_balancer": false
   }
   ```
2. Tool execution is validated **server-side** at the AI Gateway and Tool Execution Registry.
3. The client UI cannot enable, configure, or grant itself tools. An execution request for a tool disabled in the active course version is rejected with `TOOL_PERMISSION_DENIED`.

---

## 6. Offline Security & Synchronization

1. **Local Authentication:** Offline devices store hashed session tokens and local cryptographic device bindings (`device_id`).
2. **Local Database Security:** In production desktop builds, the SQLite database supports SQLCipher encryption using keys derived from local OS secure keyrings (DPAPI on Windows).
3. **Sync Authentication:** When synchronizing offline outbox events with the central platform, requests require mutual device authentication and signed HMAC nonces to prevent replay attacks and cross-device spoofing.
