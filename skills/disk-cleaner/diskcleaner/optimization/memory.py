"""
Memory monitoring and management.

Monitors memory usage and provides suggestions to prevent OOM.
"""

import gc
import os
from dataclasses import dataclass
from enum import Enum


class MemoryStatus(Enum):
    """Memory usage status."""

    OK = "OK"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


@dataclass
class MemoryInfo:
    """Current memory information."""

    status: MemoryStatus
    current_mb: float
    threshold_mb: float
    percent_used: float
    suggestion: str


class MemoryMonitor:
    """
    Memory usage monitor.

    Features:
    - Real-time memory tracking
    - Automatic garbage collection trigger
    - Dynamic concurrency adjustment suggestions
    """

    def __init__(self, threshold_mb: int = 500):
        """
        Initialize memory monitor.

        Args:
            threshold_mb: Memory threshold in MB
        """
        self.threshold = threshold_mb * 1024 * 1024  # Convert to bytes
        self.warning_threshold = self.threshold * 0.7
        self.critical_threshold = self.threshold * 0.9
        self.warning_shown = False

    def get_memory_usage(self) -> float:
        """
        Get current memory usage in bytes.

        Returns:
            Memory usage in bytes
        """
        try:
            import psutil

            process = psutil.Process(os.getpid())
            return process.memory_info().rss
        except ImportError:
            # Fallback: use tracemalloc
            import tracemalloc

            if not tracemalloc.is_tracing():
                tracemalloc.start()
            current, _ = tracemalloc.get_traced_memory()
            return current

    def check_memory(self) -> MemoryStatus:
        """
        Check current memory usage status.

        Returns:
            MemoryStatus enum value
        """
        current = self.get_memory_usage()

        if current > self.critical_threshold:
            return MemoryStatus.CRITICAL
        elif current > self.warning_threshold:
            return MemoryStatus.WARNING
        else:
            return MemoryStatus.OK

    def get_memory_info(self) -> MemoryInfo:
        """
        Get detailed memory information.

        Returns:
            MemoryInfo with current status and suggestion
        """
        current_bytes = self.get_memory_usage()
        current_mb = current_bytes / 1024 / 1024
        threshold_mb = self.threshold / 1024 / 1024
        percent_used = (current_bytes / self.threshold) * 100

        status = self.check_memory()
        suggestion = self._suggest_action(status)

        return MemoryInfo(
            status=status,
            current_mb=current_mb,
            threshold_mb=threshold_mb,
            percent_used=percent_used,
            suggestion=suggestion,
        )

    def _suggest_action(self, status: MemoryStatus) -> str:
        """
        Suggest action based on memory status.

        Returns:
            Action suggestion string
        """
        if status == MemoryStatus.CRITICAL:
            return "STOP_AND_GC"
        elif status == MemoryStatus.WARNING:
            return "REDUCE_CONCURRENCY"
        else:
            return "CONTINUE"

    def should_pause(self) -> bool:
        """
        Check if operations should pause due to memory.

        Returns:
            True if memory usage is critical
        """
        return self.check_memory() == MemoryStatus.CRITICAL

    def should_reduce_concurrency(self) -> bool:
        """
        Check if concurrency should be reduced.

        Returns:
            True if memory usage is at warning level
        """
        status = self.check_memory()
        return status == MemoryStatus.WARNING or status == MemoryStatus.CRITICAL

    def force_gc(self) -> float:
        """
        Force garbage collection and return freed memory.

        Returns:
            Memory freed in MB
        """
        before = self.get_memory_usage()
        gc.collect()
        after = self.get_memory_usage()

        freed_mb = (before - after) / 1024 / 1024
        return freed_mb

    def get_optimal_workers(self, current_workers: int) -> int:
        """
        Adjust worker count based on memory pressure.

        Args:
            current_workers: Current number of workers

        Returns:
            Recommended worker count
        """
        status = self.check_memory()

        if status == MemoryStatus.CRITICAL:
            # Reduce to minimum
            return max(1, current_workers // 4)
        elif status == MemoryStatus.WARNING:
            # Reduce by half
            return max(1, current_workers // 2)
        else:
            # No change needed
            return current_workers

    def format_memory(self, bytes_value: float) -> str:
        """
        Format bytes to human-readable string.

        Args:
            bytes_value: Memory in bytes

        Returns:
            Formatted string (e.g., "128.5 MB")
        """
        mb = bytes_value / 1024 / 1024
        if mb < 1024:
            return f"{mb:.1f} MB"
        else:
            gb = mb / 1024
            return f"{gb:.2f} GB"

    def summary(self) -> str:
        """Generate a summary of current memory status."""
        info = self.get_memory_info()
        lines = [
            f"Memory Status: {info.status.value}",
            (
                f"Usage: {info.current_mb:.1f} MB / "
                f"{info.threshold_mb:.0f} MB ({info.percent_used:.1f}%)"
            ),
            f"Suggestion: {info.suggestion}",
        ]
        return "\n".join(lines)

    def set_threshold(self, threshold_mb: int):
        """
        Update memory threshold.

        Args:
            threshold_mb: New threshold in MB
        """
        self.threshold = threshold_mb * 1024 * 1024
        self.warning_threshold = self.threshold * 0.7
        self.critical_threshold = self.threshold * 0.9
