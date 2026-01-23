"""
Performance profiling and monitoring.

Tracks performance metrics for different operations to identify bottlenecks
and measure optimization effectiveness.
"""

import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class PerformanceReport:
    """Performance report for an operation or session."""

    operation: str
    total_time: float
    memory_used: float  # MB
    item_count: int
    throughput: float  # items/second

    def __str__(self) -> str:
        return (
            f"{self.operation}: {self.total_time:.2f}s, "
            f"{self.throughput:.0f} items/s, "
            f"{self.memory_used:.1f} MB"
        )


class PerformanceProfiler:
    """
    Performance profiler for tracking operation metrics.

    Measures:
    - Execution time
    - Memory usage
    - Throughput (items per second)
    - Identifies bottlenecks
    """

    def __init__(self):
        self.metrics: Dict[str, List[float]] = {}
        self._operation_stack: List[str] = []
        self._operation_times: Dict[str, float] = {}

    @contextmanager
    def profile(self, operation: str):
        """
        Context manager for automatic performance recording.

        Usage:
            with profiler.profile('scan'):
                result = scanner.scan()
        """
        import tracemalloc

        # Start tracking
        start_time = time.time()
        tracemalloc.start()
        start_mem = tracemalloc.get_traced_memory()[0]

        self._operation_stack.append(operation)

        try:
            yield
        finally:
            # Stop tracking
            elapsed = time.time() - start_time
            current_mem, peak_mem = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            memory_used = (peak_mem - start_mem) / 1024 / 1024  # Convert to MB

            # Record metrics (initialize list if needed)
            time_key = f"{operation}_time"
            mem_key = f"{operation}_memory"

            if time_key not in self.metrics:
                self.metrics[time_key] = []
            if mem_key not in self.metrics:
                self.metrics[mem_key] = []

            self.metrics[time_key].append(elapsed)
            self.metrics[mem_key].append(memory_used)
            self._operation_times[operation] = elapsed

            self._operation_stack.pop()

    def record(self, operation: str, value: float, metric: str = "time"):
        """
        Manually record a metric.

        Args:
            operation: Operation name (e.g., 'scan', 'delete')
            value: Metric value
            metric: Metric type ('time', 'memory', 'throughput')
        """
        key = f"{operation}_{metric}"
        if key not in self.metrics:
            self.metrics[key] = []
        self.metrics[key].append(value)

    def get_operation_time(self, operation: str) -> Optional[float]:
        """Get the last recorded time for an operation."""
        return self._operation_times.get(operation)

    def get_average_time(self, operation: str) -> float:
        """Get average execution time for an operation."""
        times = self.metrics.get(f"{operation}_time", [])
        if not times:
            return 0.0
        return sum(times) / len(times)

    def get_peak_memory(self, operation: str) -> float:
        """Get peak memory usage for an operation (MB)."""
        memories = self.metrics.get(f"{operation}_memory", [])
        if not memories:
            return 0.0
        return max(memories)

    def generate_report(self, operation: str, item_count: int) -> PerformanceReport:
        """
        Generate a performance report for an operation.

        Args:
            operation: Operation name
            item_count: Number of items processed

        Returns:
            PerformanceReport with metrics
        """
        total_time = self.get_average_time(operation)
        memory_used = self.get_peak_memory(operation)
        throughput = item_count / total_time if total_time > 0 else 0

        return PerformanceReport(
            operation=operation,
            total_time=total_time,
            memory_used=memory_used,
            item_count=item_count,
            throughput=throughput,
        )

    def get_all_reports(self) -> List[PerformanceReport]:
        """Get reports for all tracked operations."""
        reports = []
        for key in self.metrics.keys():
            if key.endswith("_time"):
                operation = key[:-5]  # Remove '_time' suffix
                if self.metrics[key]:  # Only if has data
                    item_count = int(self.get_average_time(operation) * 1000)  # Estimate
                    reports.append(self.generate_report(operation, item_count))
        return reports

    def identify_bottleneck(self) -> Optional[str]:
        """
        Identify the slowest operation.

        Returns:
            Operation name with highest average time, or None
        """
        operation_times = {}
        for key, times in self.metrics.items():
            if key.endswith("_time") and times:
                operation = key[:-5]
                avg_time = sum(times) / len(times)
                operation_times[operation] = avg_time

        if not operation_times:
            return None

        return max(operation_times.items(), key=lambda x: x[1])[0]

    def reset(self):
        """Clear all metrics."""
        self.metrics.clear()
        self._operation_stack.clear()
        self._operation_times.clear()

    def summary(self) -> str:
        """Generate a summary of all metrics."""
        lines = ["Performance Summary:", "=" * 50]

        for operation in ["scan", "delete", "hash"]:
            if self.metrics.get(f"{operation}_time"):
                avg_time = self.get_average_time(operation)
                peak_mem = self.get_peak_memory(operation)
                lines.append(
                    f"{operation.capitalize()}: " f"{avg_time:.2f}s avg, " f"{peak_mem:.1f} MB peak"
                )

        bottleneck = self.identify_bottleneck()
        if bottleneck:
            lines.append(f"\nBottleneck: {bottleneck}")

        return "\n".join(lines)
