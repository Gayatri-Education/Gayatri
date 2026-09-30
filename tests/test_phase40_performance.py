"""Phase 40 — Performance Profiling & Benchmark Subsystem Unit & Integration Tests.

Verifies:
1. PerformanceMetricType enum and PerformanceBenchmarkResult serialization.
2. Startup latency benchmark (< 1000ms).
3. Database query latency benchmark (< 50ms average).
4. RAG search latency benchmark (< 100ms average).
5. Memory usage profiling (< 1024 MB).
6. Multi-threaded concurrency benchmark.
7. Full performance audit runner.
"""

import pytest

from central_platform.db import PlatformDatabase
from central_platform.models.schema import Organization
from central_platform.performance.profiler import (
    PerformanceBenchmarkResult,
    PerformanceMetricType,
    PerformanceProfiler,
)


@pytest.fixture
def db():
    database = PlatformDatabase(":memory:")
    database.create_organization(Organization(id="org_master_1", name="Test Org", slug="test-org"))
    yield database
    database.close()


def test_performance_result_dataclass():
    res = PerformanceBenchmarkResult(
        metric_type=PerformanceMetricType.STARTUP_TIME,
        latency_ms=120.0,
        passed=True,
    )
    assert res.metric_type == PerformanceMetricType.STARTUP_TIME
    d = res.to_dict()
    assert d["metric_type"] == "startup_time"
    assert d["latency_ms"] == 120.0


def test_benchmark_startup_time():
    res = PerformanceProfiler.benchmark_startup_time()
    assert isinstance(res, PerformanceBenchmarkResult)
    assert res.passed is True
    assert res.latency_ms < 1000.0


def test_benchmark_database_query_latency(db: PlatformDatabase):
    res = PerformanceProfiler.benchmark_database_query_latency(db, query_count=20)
    assert isinstance(res, PerformanceBenchmarkResult)
    assert res.passed is True
    assert res.latency_ms < 50.0  # Average latency under 50ms


def test_benchmark_rag_search_latency():
    res = PerformanceProfiler.benchmark_rag_search_latency(search_count=10)
    assert isinstance(res, PerformanceBenchmarkResult)
    assert res.passed is True
    assert res.latency_ms < 100.0


def test_benchmark_memory_usage():
    res = PerformanceProfiler.benchmark_memory_usage()
    assert isinstance(res, PerformanceBenchmarkResult)
    assert res.memory_mb > 0.0
    assert res.passed is True  # Memory under 1GB limit


def test_benchmark_concurrency():
    res = PerformanceProfiler.benchmark_concurrency(concurrent_workers=4, requests_per_worker=5)
    assert isinstance(res, PerformanceBenchmarkResult)
    assert res.passed is True
    assert res.throughput_qps > 0.0
    assert res.details["completed_requests"] == 20


def test_run_full_performance_audit(db: PlatformDatabase):
    results = PerformanceProfiler.run_full_performance_audit(db=db)
    assert len(results) >= 5
    for r in results:
        assert isinstance(r, PerformanceBenchmarkResult)
        assert r.passed is True
