"""
scripts/launch_local_environment.py
One-Click Local Platform Launcher for Gayatri V2.

Bootstraps the local SQLite database, seeds realistic test data,
and launches the FastAPI server with an interactive console guide.
"""

from __future__ import annotations

import os
import sys
import webbrowser
from pathlib import Path

# Ensure root directory in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.seed_local_environment import seed_local_environment


def print_banner(tokens: dict):
    print("\n" + "=" * 78)
    print("      GAYATRI V2 — LOCAL PLATFORM ENVIRONMENT READY FOR TESTING")
    print("=" * 78)
    print("\n[PORTALS & WEB INTERFACES]")
    print("  • Super Admin Portal:    http://127.0.0.1:8000/admin")
    print("  • Teacher Web Portal:    http://127.0.0.1:8000/teacher")
    print("  • Student Dashboard:     http://127.0.0.1:8000/student")
    print("  • Interactive Web Tutor: http://127.0.0.1:8000/tutor")
    print("  • Swagger API Explorer:  http://127.0.0.1:8000/docs")
    print("  • Legacy Command Center: http://127.0.0.1:8000/")
    
    print("\n[SEEDED TEST ACCOUNTS & TOKENS]")
    for user_id, info in tokens.items():
        print(f"  • {info['name']}")
        print(f"    Email: {info['email']} | Role: {info['role']} | Org: {info['organization_id']}")
        print(f"    Token: {info['token'][:36]}... (Full token in local_auth_tokens.json)\n")

    print("[NATIVE DESKTOP TUTOR]")
    print("  • Run in separate terminal: python -m app.main")
    print("=" * 78 + "\n")


def main():
    db_file = os.getenv("GAYATRI_DB_PATH", "gayatri_local.db")
    tokens = seed_local_environment(db_file)
    print_banner(tokens)

    # Launch uvicorn server
    try:
        import uvicorn
        print("[+] Starting FastAPI Central Platform Server on http://127.0.0.1:8000 ...")
        uvicorn.run("central_platform.api.app:app", host="127.0.0.1", port=8000, reload=False)
    except ImportError:
        print("[!] uvicorn not found. Running with basic ASGI server or install with: pip install uvicorn")


if __name__ == "__main__":
    main()
