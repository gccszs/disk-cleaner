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
from diskcleaner.optimization.delete import (
    BatchDeleter,
    AsyncDeleter,
    SmartDeleter,
    DeletionManager,
    DeleteStrategy,
    DeleteResult,
    ProgressUpdate,
)

__all__ = [
    # Infrastructure
    'PerformanceProfiler',
    'PerformanceReport',
    'ConcurrencyManager',
    'MemoryMonitor',
    'MemoryStatus',
    # Scanning
    'QuickProfiler',
    'ConcurrentScanner',
    'IncrementalCache',
    'ScanStrategy',
    'ScanProfile',
    'ScanResult',
    'ScanSnapshot',
    'FileInfo',
    # Deletion
    'BatchDeleter',
    'AsyncDeleter',
    'SmartDeleter',
    'DeletionManager',
    'DeleteStrategy',
    'DeleteResult',
    'ProgressUpdate',
]
