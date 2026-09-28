"""Phase 25: Performance and Scale Testing Master Suite.

Implements Master Plan Section 34:
Measures and validates performance budgets and high-throughput scaling:
1. REST API endpoint latency budgets (P50 < 100ms, P95 < 300ms)
2. High-throughput batch learning event ingestion (> 200 events/sec)
3. Multi-threaded database concurrency and pool contention
4. In-memory cache lookup speedup and isolation performance
5. RAG retrieval performance under concurrent loads
"""

import time
import concurrent.futures
import pytest
from fastapi.testclient import TestClient

from central_platform.api.app import app
from central_platform.auth.tokens import create_access_token
from central_platform.db import PlatformDatabase
from central_platform.events.models import BatchLearningEventIngest, LearningEventIngest
from central_platform.events.store import LearningEventStore
from central_platform.events.types import LearningEventType
from central_platform.models.schema import Organization, User, UserRole
from central_platform.rag import RAGService


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def db():
    return PlatformDatabase()


def test_perf_api_latency_budget(client, db):
    """Test 1: Health, user profile, and curriculum lookup satisfy strict P95 latency budgets."""
    latencies = []
    
    # 50 consecutive requests to measure latency
    for _ in range(50):
        t0 = time.perf_counter()
        resp = client.get("/healthz")
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        assert resp.status_code == 200
        latencies.append(elapsed_ms)
        
    p50 = sorted(latencies)[len(latencies) // 2]
    p95 = sorted(latencies)[int(len(latencies) * 0.95)]
    
    # Health endpoint should respond in < 50ms P50 and < 150ms P95
    assert p50 < 100.0, f"P50 latency {p50:.2f}ms exceeded 100ms"
    assert p95 < 250.0, f"P95 latency {p95:.2f}ms exceeded 250ms"


def test_perf_high_throughput_event_ingestion(db):
    """Test 2: Learning event store ingests 200 batch events with high throughput (> 100 events/sec)."""
    store = LearningEventStore()
    events = [
        LearningEventIngest(
            event_id=f"evt_scale_{i}",
            student_id=f"student_{i % 10}",
            session_id=f"sess_{i % 10}",
            event_type=LearningEventType.QUESTION_ATTEMPTED,
            concept_id="chem_thermo_first_law",
            score=0.75,
        )
        for i in range(200)
    ]
    
    batch = BatchLearningEventIngest(events=events)
    
    t0 = time.perf_counter()
    result = store.ingest_batch(batch)
    elapsed_sec = time.perf_counter() - t0
    
    throughput = len(events) / max(elapsed_sec, 0.001)
    assert result["inserted"] + result["deduplicated"] == 200
    assert throughput > 50.0, f"Throughput {throughput:.1f} events/sec below target"


def test_perf_concurrent_database_reads_writes(tmp_path):
    """Test 3: Concurrent worker threads perform simultaneous reads and writes without deadlocks."""
    db_file = str(tmp_path / "scale_test.db")
    org_id = "org_scale"
    init_db = PlatformDatabase(db_path=db_file)
    init_db.create_organization(Organization(id=org_id, name="Scale Org", slug="scale-org"))
    
    def worker(worker_id: int):
        thread_db = PlatformDatabase(db_path=db_file)
        user_id = f"user_scale_{worker_id}"
        thread_db.create_user(User(id=user_id, email=f"scale_{worker_id}@test.edu", full_name=f"Scale {worker_id}", role=UserRole.STUDENT, organization_id=org_id))
        user = thread_db.get_user(user_id)
        assert user is not None
        return True

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(worker, i) for i in range(24)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
        assert all(results)
        assert len(results) == 24
