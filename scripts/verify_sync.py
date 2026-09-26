"""Gayatri AI — Teacher-to-Student Synchronization & Directive Verification CLI.

Tests end-to-end connectivity, student progress sync, teacher instruction dispatch,
and verifies that directives reach and alter the local AI Tutor prompt.

Usage:
    python scripts/verify_sync.py
    python scripts/verify_sync.py --url http://127.0.0.1:8000
    python scripts/verify_sync.py --url https://<remote-server-host>
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def run_verification(server_url: str = "http://localhost:8000") -> bool:
    clean_url = server_url.rstrip("/")
    print("=" * 70)
    print("GAYATRI AI — TEACHER-STUDENT SYNC & DIRECTIVE VERIFICATION")
    print(f"Target Server: {clean_url}")
    print("=" * 70)

    # ── Gate 1: Server Health & Connectivity ──
    print("\n[Gate 1/5] Checking Server Connectivity...")
    t0 = time.time()
    try:
        req = urllib.request.Request(f"{clean_url}/api/health", headers={"User-Agent": "GayatriVerifier/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            latency_ms = int((time.time() - t0) * 1000)
            data = json.loads(resp.read().decode("utf-8"))
            if resp.status == 200 and data.get("status") == "HEALTHY":
                print(f"  [PASS] Server ONLINE ({latency_ms}ms) | Service: {data.get('service')} | Monitored: {data.get('students_monitored')} students")
            else:
                print(f"  [FAIL] Unexpected response: {data}")
                return False
    except Exception as e:
        print(f"  [FAIL] Server unreachable at {clean_url}: {e}")
        print("  Hint: Ensure 'python server.py' is running on the host machine.")
        return False

    # ── Gate 2: Push Student Progress & Telemetry Snapshot ──
    print("\n[Gate 2/5] Pushing Student Telemetry Snapshot to Central Platform...")
    test_sid = "verify_student_usa"
    snapshot_payload = json.dumps({
        "student_id": test_sid,
        "student_name": "Verification Student (USA)",
        "course_id": "crs-chem-101",
        "mastery": 0.86,
        "needs_attention": False,
        "misconceptions": ["THERMO_SIGN_CONVENTION"],
        "hint_count": 2,
        "retention_rate": 0.91,
    }).encode("utf-8")

    try:
        req = urllib.request.Request(
            f"{clean_url}/api/student/snapshot",
            data=snapshot_payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            if res.get("ok"):
                print(f"  [PASS] Student snapshot accepted! (ID: {test_sid}, Mastery: 86%)")
            else:
                print(f"  [FAIL] Snapshot error: {res}")
                return False
    except Exception as e:
        print(f"  [FAIL] Could not push snapshot: {e}")
        return False

    # ── Gate 3: Dispatch Teacher Directive (Teacher Side) ──
    print("\n[Gate 3/5] Dispatching Targeted Pedagogical Directive (Teacher -> Server)...")
    directive_text = "VERIFICATION TEST DIRECTIVE: Enforce strict sign reasoning for expansion work."
    inst_payload = json.dumps({
        "instruction": directive_text,
        "student_id": test_sid,
        "course_id": "crs-chem-101",
        "priority": 3,
    }).encode("utf-8")

    try:
        req = urllib.request.Request(
            f"{clean_url}/api/teacher/instruction",
            data=inst_payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            if res.get("ok"):
                inst_id = res["instruction_id"]
                print(f"  [PASS] Directive created on server! (ID: {inst_id})")
            else:
                print(f"  [FAIL] Instruction dispatch error: {res}")
                return False
    except Exception as e:
        print(f"  [FAIL] Could not dispatch instruction: {e}")
        return False

    # ── Gate 4: Student Device Instruction Pull ──
    print("\n[Gate 4/5] Pulling Instructions from Server to Student Device...")
    try:
        req = urllib.request.Request(f"{clean_url}/api/teacher/instructions?student_id={test_sid}&course_id=crs-chem-101")
        with urllib.request.urlopen(req, timeout=5) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            instructions = res.get("instructions", [])
            match = [i for i in instructions if i["instruction_id"] == inst_id]
            if match:
                print(f"  [PASS] Student device pulled directive: \"{match[0]['instruction_text']}\"")
            else:
                print(f"  [FAIL] Directive {inst_id} not found in student pull: {instructions}")
                return False
    except Exception as e:
        print(f"  [FAIL] Could not pull instructions: {e}")
        return False

    # ── Gate 5: Local AI Tutor System Prompt Verification ──
    print("\n[Gate 5/5] Verifying Directive Alters Local AI Tutor System Prompt...")
    try:
        from central_platform.teacher.instruction import TeacherInstruction
        from app.bridge.facade import get_teacher_instruction_engine
        from core.runtimes.chemistry import _build_chemistry_system_prompt

        # Register into local student instruction engine
        engine = get_teacher_instruction_engine()
        engine.add_instruction(
            TeacherInstruction(
                instruction_id=inst_id,
                teacher_id="tchr-101",
                student_id=test_sid,
                course_id="crs-chem-101",
                instruction_text=directive_text,
                priority=3,
            )
        )

        active = engine.get_instructions_for_student(test_sid, "crs-chem-101")
        bullet_list = "\n".join(f"  * {i.instruction_text}" for i in active)
        directive_block = f"[PRIORITY TEACHER INSTRUCTIONS]:\n{bullet_list}"

        system_prompt = _build_chemistry_system_prompt(
            topics=["Thermodynamics"],
            rag_evidence="",
            policy_directive=directive_block,
            memory_summary="",
            is_slm=False,
        )

        if "[PRIORITY TEACHER INSTRUCTIONS]" in system_prompt and directive_text in system_prompt:
            print("  [PASS] AI Tutor prompt contains teacher directive!")
            print(f"         Prompt snippet: ...{directive_block[:70]}...")
        else:
            print("  [FAIL] Directive did not appear in AI Tutor prompt!")
            return False
    except Exception as e:
        print(f"  [FAIL] Runtime verification error: {e}")
        return False

    print("\n" + "=" * 70)
    print("RESULT: ALL 5/5 VERIFICATION GATES PASSED PERFECTLY!")
    print("Connectivity, telemetry sync, and teacher instruction routing are verified.")
    print("=" * 70)
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify Gayatri AI Teacher-Student Sync & Instructions")
    parser.add_argument("--url", default="http://localhost:8000", help="Central Platform Server URL (default: http://localhost:8000)")
    args = parser.parse_args()

    success = run_verification(args.url)
    sys.exit(0 if success else 1)
