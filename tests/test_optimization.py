"""
Unit tests for optimization infrastructure components.

Tests:
- PerformanceProfiler
- ConcurrencyManager
- MemoryMonitor
"""

import time
from pathlib import Path

import pytest

from diskcleaner.optimization.concurrency import ConcurrencyManager
from diskcleaner.optimization.memory import MemoryMonitor, MemoryStatus
from diskcleaner.optimization.profiler import PerformanceProfiler, PerformanceReport


class TestPerformanceProfiler:
    """Tests for PerformanceProfiler."""

    def test_profiler_initialization(self):
        """Test profiler can be initialized."""
        profiler = PerformanceProfiler()
        assert profiler is not None
        assert len(profiler.metrics) == 0

    def test_profile_context_manager(self):
        """Test profiling with context manager."""
        profiler = PerformanceProfiler()

        with profiler.profile("test_operation"):
            time.sleep(0.1)  # Simulate work

        # Check metrics were recorded
        assert "test_operation_time" in profiler.metrics
        assert len(profiler.metrics["test_operation_time"]) == 1
        assert profiler.metrics["test_operation_time"][0] >= 0.1

    def test_get_operation_time(self):
        """Test getting operation time."""
        profiler = PerformanceProfiler()

        with profiler.profile("scan"):
            time.sleep(0.05)

        scan_time = profiler.get_operation_time("scan")
        assert scan_time is not None
        assert scan_time >= 0.05

    def test_get_average_time(self):
        """Test calculating average time."""
        profiler = PerformanceProfiler()

        # Run same operation multiple times
        for _ in range(3):
            with profiler.profile("repeat"):
                time.sleep(0.01)

        avg_time = profiler.get_average_time("repeat")
        assert avg_time >= 0.01
        assert avg_time < 0.1  # Should be reasonable

    def test_generate_report(self):
        """Test generating performance report."""
        profiler = PerformanceProfiler()

        with profiler.profile("scan"):
            time.sleep(0.05)

        report = profiler.generate_report("scan", item_count=1000)

        assert isinstance(report, PerformanceReport)
        assert report.operation == "scan"
        assert report.item_count == 1000
        assert report.total_time >= 0.05
        assert report.throughput > 0

    def test_identify_bottleneck(self):
        """Test bottleneck identification."""
        profiler = PerformanceProfiler()

        # Simulate multiple operations
        with profiler.profile("fast"):
            time.sleep(0.01)

        with profiler.profile("slow"):
            time.sleep(0.05)

        with profiler.profile("medium"):
            time.sleep(0.02)

        bottleneck = profiler.identify_bottleneck()
        assert bottleneck == "slow"

    def test_reset(self):
        """Test resetting profiler."""
        profiler = PerformanceProfiler()

        with profiler.profile("test"):
            pass

        assert len(profiler.metrics) > 0

        profiler.reset()
        assert len(profiler.metrics) == 0

    def test_summary(self):
        """Test generating summary."""
        profiler = PerformanceProfiler()

        with profiler.profile("scan"):
            time.sleep(0.01)

        summary = profiler.summary()
        assert "Performance Summary" in summary
        assert "scan" in summary.lower()

    def test_manual_record(self):
        """Test manual metric recording."""
        profiler = PerformanceProfiler()

        profiler.record("custom", 1.5, "time")
        profiler.record("custom", 100, "throughput")

        assert "custom_time" in profiler.metrics
        assert profiler.metrics["custom_time"] == [1.5]
        assert profiler.metrics["custom_throughput"] == [100]


class TestConcurrencyManager:
    """Tests for ConcurrencyManager."""

    def test_manager_initialization(self):
        """Test manager can be initialized."""
        manager = ConcurrencyManager()
        assert manager is not None
        assert not manager.is_initialized()

    def test_get_thread_pool(self):
        """Test getting thread pool."""
        manager = ConcurrencyManager()

        pool = manager.get_thread_pool("io_scan")
        assert pool is not None
        assert manager.is_initialized()

        # Same pool should be returned
        pool2 = manager.get_thread_pool("io_scan")
        assert pool is pool2

    def test_multiple_pools(self):
        """Test creating multiple pools."""
        manager = ConcurrencyManager()

        pool1 = manager.get_thread_pool("io_scan")
        pool2 = manager.get_thread_pool("io_delete")
        pool3 = manager.get_thread_pool("ui_update")

        assert pool1 is not pool2
        assert pool2 is not pool3
        assert manager.get_pool_count() == 3

    def test_optimal_threads(self):
        """Test optimal thread calculation."""
        manager = ConcurrencyManager()

        # I/O bound should get more threads
        io_workers = manager._optimal_threads("io_scan")
        assert io_workers >= 1
        assert io_workers <= 32  # Capped at 32

        # UI updates should get minimal threads
        ui_workers = manager._optimal_threads("ui_update")
        assert ui_workers == 2

    def test_shutdown_pool(self):
        """Test shutting down specific pool."""
        manager = ConcurrencyManager()

        pool = manager.get_thread_pool("test")
        manager.shutdown_pool("test")

        # Pool should be removed
        assert manager.get_pool_count() == 0

    def test_shutdown_all(self):
        """Test shutting down all pools."""
        manager = ConcurrencyManager()

        manager.get_thread_pool("io_scan")
        manager.get_thread_pool("io_delete")
        manager.get_process_pool("hash_compute")

        assert manager.get_pool_count() == 3

        manager.shutdown_all()
        assert manager.get_pool_count() == 0
        assert not manager.is_initialized()

    def test_context_manager(self):
        """Test using as context manager."""
        with ConcurrencyManager() as manager:
            manager.get_thread_pool("test")
            assert manager.is_initialized()

        # Pools should be shutdown after exit
        assert manager.get_pool_count() == 0


class TestMemoryMonitor:
    """Tests for MemoryMonitor."""

    def test_initialization(self):
        """Test monitor can be initialized."""
        monitor = MemoryMonitor(threshold_mb=500)
        assert monitor is not None
        assert monitor.threshold == 500 * 1024 * 1024

    def test_get_memory_usage(self):
        """Test getting memory usage."""
        monitor = MemoryMonitor()

        usage = monitor.get_memory_usage()
        assert usage > 0
        assert isinstance(usage, (int, float))

    def test_check_memory(self):
        """Test memory status check."""
        monitor = MemoryMonitor(threshold_mb=10000)  # High threshold

        status = monitor.check_memory()
        assert status in [MemoryStatus.OK, MemoryStatus.WARNING, MemoryStatus.CRITICAL]

    def test_get_memory_info(self):
        """Test getting detailed memory info."""
        monitor = MemoryMonitor(threshold_mb=1000)

        info = monitor.get_memory_info()
        assert info.status in [MemoryStatus.OK, MemoryStatus.WARNING, MemoryStatus.CRITICAL]
        assert info.current_mb > 0
        assert info.threshold_mb == 1000
        assert 0 <= info.percent_used <= 100
        assert info.suggestion in ["CONTINUE", "REDUCE_CONCURRENCY", "STOP_AND_GC"]

    def test_should_pause(self):
        """Test pause decision."""
        monitor = MemoryMonitor(threshold_mb=10000)

        # Should not pause with high threshold
        assert not monitor.should_pause()

    def test_should_reduce_concurrency(self):
        """Test concurrency reduction decision."""
        monitor = MemoryMonitor(threshold_mb=10000)

        # Should not reduce with high threshold
        assert not monitor.should_reduce_concurrency()

    def test_force_gc(self):
        """Test forcing garbage collection."""
        monitor = MemoryMonitor()

        # Just verify it runs without error
        freed = monitor.force_gc()
        assert isinstance(freed, float)
        # freed can be negative or near zero due to measurement precision

    def test_optimal_workers(self):
        """Test optimal worker calculation."""
        monitor = MemoryMonitor(threshold_mb=10000)

        # With high threshold, workers should remain the same
        current = 8
        optimal = monitor.get_optimal_workers(current)
        assert optimal == current

    def test_format_memory(self):
        """Test memory formatting."""
        monitor = MemoryMonitor()

        # Test MB format
        result = monitor.format_memory(100 * 1024 * 1024)
        assert "MB" in result
        assert "100.0" in result

        # Test GB format
        result = monitor.format_memory(2 * 1024 * 1024 * 1024)
        assert "GB" in result

    def test_summary(self):
        """Test generating summary."""
        monitor = MemoryMonitor(threshold_mb=1000)

        summary = monitor.summary()
        assert "Memory Status" in summary
        assert "Usage" in summary
        assert "Suggestion" in summary

    def test_set_threshold(self):
        """Test updating threshold."""
        monitor = MemoryMonitor(threshold_mb=500)

        monitor.set_threshold(1000)
        assert monitor.threshold == 1000 * 1024 * 1024
        assert monitor.warning_threshold == monitor.threshold * 0.7


class TestIntegration:
    """Integration tests for infrastructure components."""

    def test_profiler_with_concurrency(self):
        """Test profiler tracking concurrent work."""
        profiler = PerformanceProfiler()
        manager = ConcurrencyManager()

        with profiler.profile("concurrent_test"):
            pool = manager.get_thread_pool("test")
            # Simulate some work
            import time

            time.sleep(0.05)

        report = profiler.generate_report("concurrent_test", 100)
        assert report.total_time >= 0.05

        manager.shutdown_all()

    def test_memory_monitor_in_loop(self):
        """Test memory monitoring during repeated operations."""
        monitor = MemoryMonitor(threshold_mb=10000)
        profiler = PerformanceProfiler()

        for i in range(5):
            with profiler.profile(f"iteration_{i}"):
                # Simulate work
                time.sleep(0.01)

            # Check memory
            status = monitor.check_memory()
            assert status in [MemoryStatus.OK, MemoryStatus.WARNING, MemoryStatus.CRITICAL]

        assert len(profiler.metrics) >= 5
