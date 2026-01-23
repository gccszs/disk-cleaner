"""
Performance optimization module for disk-cleaner.

This module provides intelligent, layered performance optimizations:
- Concurrent scanning and deletion
- Incremental caching
- Adaptive hash computation
- Performance monitoring

All optimizations are pluggable and can be disabled via configuration.
"""

from diskcleaner.optimization.profiler import PerformanceProfiler, PerformanceReport
from diskcleaner.optimization.concurrency import ConcurrencyManager
from diskcleaner.optimization.memory import MemoryMonitor, MemoryStatus
from diskcleaner.optimization.scan import (
    QuickProfiler,
    ConcurrentScanner,
    IncrementalCache,
    ScanStrategy,
    ScanProfile,
    ScanResult,
    ScanSnapshot,
    FileInfo,
)

__all__ = [
    'PerformanceProfiler',
    'PerformanceReport',
    'ConcurrencyManager',
    'MemoryMonitor',
    'MemoryStatus',
    'QuickProfiler',
    'ConcurrentScanner',
    'IncrementalCache',
    'ScanStrategy',
    'ScanProfile',
    'ScanResult',
    'ScanSnapshot',
    'FileInfo',
]
