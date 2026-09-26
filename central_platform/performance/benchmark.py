"""Performance benchmarking harness measuring latency percentiles (P50, P95, P99) and throughput."""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, List


@dataclass
class BenchmarkResult:
    scenario_name: str
    total_operations: int
    throughput_ops_per_sec: float
    p50_ms: float
    p95_ms: float
    p99_ms: float
    min_ms: float
    max_ms: float
    error_count: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class PerformanceBenchmark:
    """Benchmark harness for load profiling and latency metric calculation."""

    @staticmethod
    def run_benchmark(scenario_name: str, target_func: Callable[[], None], iterations: int = 100) -> BenchmarkResult:
        latencies_ms: List[float] = []
        errors = 0
        start_total = time.time()

        for _ in range(iterations):
            op_start = time.time()
            try:
                target_func()
            except Exception:
                errors += 1
            finally:
                op_duration = (time.time() - op_start) * 1000.0
                latencies_ms.append(op_duration)

        total_duration = time.time() - start_total
        latencies_ms.sort()

        def percentile(p: float) -> float:
            if not latencies_ms:
                return 0.0
            idx = int(math.ceil(p * len(latencies_ms))) - 1
            return latencies_ms[max(0, min(idx, len(latencies_ms) - 1))]

        throughput = iterations / total_duration if total_duration > 0 else 0.0

        return BenchmarkResult(
            scenario_name=scenario_name,
            total_operations=iterations,
            throughput_ops_per_sec=throughput,
            p50_ms=percentile(0.50),
            p95_ms=percentile(0.95),
            p99_ms=percentile(0.99),
            min_ms=latencies_ms[0] if latencies_ms else 0.0,
            max_ms=latencies_ms[-1] if latencies_ms else 0.0,
            error_count=errors,
        )
