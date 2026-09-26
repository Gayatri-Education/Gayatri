"""End-to-end integration tests for server.py and cross-device sync."""

import json
import socket
import threading
import time
import urllib.request
import pytest

from server import HTTPServer, TeacherPortalHTTPHandler


def get_free_port():
    s = socket.socket()
    s.bind(("", 0))
    port = s.getsockname()[1]
    s.close()
    return port


@pytest.fixture(scope="module")
def live_server():
    port = get_free_port()
    httpd = HTTPServer(("127.0.0.1", port), TeacherPortalHTTPHandler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    time.sleep(0.3)
    base_url = f"http://127.0.0.1:{port}"
    yield base_url
    httpd.shutdown()


def test_server_html_dashboard(live_server):
    req = urllib.request.urlopen(f"{live_server}/")
    assert req.status == 200
    html = req.read().decode("utf-8")
    assert "Gayatri AI — Teacher Portal" in html
    assert "Monitored Students Roster" in html
    assert "Cross-Device &amp; International Sync Guide" in html or "Cross-Device" in html


def test_server_api_health(live_server):
    req = urllib.request.urlopen(f"{live_server}/api/health")
    assert req.status == 200
    data = json.loads(req.read().decode("utf-8"))
    assert data["status"] == "HEALTHY"
    assert data["service"] == "TeacherPortalServer"


def test_server_api_teacher_dashboard(live_server):
    req = urllib.request.urlopen(f"{live_server}/api/teacher/dashboard?course_id=crs-chem-101")
    assert req.status == 200
    data = json.loads(req.read().decode("utf-8"))
    assert data["ok"] is True
    assert "class_health_status" in data
    assert len(data["students"]) >= 1


def test_server_student_snapshot_sync(live_server):
    payload = json.dumps({
        "student_id": "stu-live-test",
        "student_name": "Test Student USA",
        "course_id": "crs-chem-101",
        "mastery": 0.88,
        "needs_attention": False,
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{live_server}/api/student/snapshot",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        res = json.loads(resp.read().decode("utf-8"))
        assert res["ok"] is True

    # Verify student is reflected in dashboard
    req = urllib.request.urlopen(f"{live_server}/api/teacher/dashboard?course_id=crs-chem-101")
    data = json.loads(req.read().decode("utf-8"))
    student_ids = [s["id"] for s in data["students"]]
    assert "stu-live-test" in student_ids


def test_server_teacher_instruction_injection_and_retrieval(live_server):
    payload = json.dumps({
        "instruction": "Live Test Directive: Focus on Gibbs Free Energy delta G",
        "student_id": "stu-live-test",
        "course_id": "crs-chem-101",
        "priority": 3,
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{live_server}/api/teacher/instruction",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        res = json.loads(resp.read().decode("utf-8"))
        assert res["ok"] is True
        inst_id = res["instruction_id"]

    # Verify retrieval
    req = urllib.request.urlopen(f"{live_server}/api/teacher/instructions?student_id=stu-live-test")
    assert req.status == 200
    data = json.loads(req.read().decode("utf-8"))
    assert data["ok"] is True
    found = [i for i in data["instructions"] if i["instruction_id"] == inst_id]
    assert len(found) == 1
    assert "Gibbs Free Energy" in found[0]["instruction_text"]


def test_bridge_sync_with_live_server(live_server):
    from app.bridge.facade import Bridge

    b = Bridge()
    raw = b.sync_with_central_server(live_server)
    res = json.loads(raw)
    assert res["ok"] is True
    assert res["server_url"] == live_server
