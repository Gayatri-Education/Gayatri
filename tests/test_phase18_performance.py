"""Unit and integration test suite for Phase 18: Performance & Load Testing."""

import time
import pytest
from central_platform.performance.benchmark import PerformanceBenchmark


def test_performance_benchmark_execution():
    def dummy_workload():
        time.sleep(0.001)

    result = PerformanceBenchmark.run_benchmark(
        scenario_name="dashboard_load_test",
        target_func=dummy_workload,
        iterations=50,
    )

    assert result.scenario_name == "dashboard_load_test"
    assert result.total_operations == 50
    assert result.throughput_ops_per_sec > 0
    assert result.p50_ms >= 0.9
    assert result.p95_ms >= result.p50_ms
    assert result.p99_ms >= result.p95_ms
    assert result.error_count == 0


def test_performance_benchmark_error_tracking():
    counter = 0

    def failing_workload():
        nonlocal counter
        counter += 1
        if counter % 2 == 0:
            raise ValueError("Simulated workload error")

    result = PerformanceBenchmark.run_benchmark(
        scenario_name="failing_scenario",
        target_func=failing_workload,
        iterations=10,
    )

    assert result.total_operations == 10
    assert result.error_count == 5
