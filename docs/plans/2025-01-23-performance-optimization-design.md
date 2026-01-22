# Performance Optimization Design - disk-cleaner v2.0

**Date**: 2025-01-23
**Version**: 2.0
**Status**: Design Complete
**Author**: Claude Code + User Brainstorming

---

## Overview

This document presents a comprehensive performance optimization strategy for the disk-cleaner skill, focusing on **scanning speed** and **deletion throughput**. The design uses an **intelligent layered approach** that dynamically selects optimal strategies based on the current scenario.

### Goals

- **Scanning Speed**: 10-15x improvement (first scan), 30-50x (cached scans)
- **Deletion Speed**: 2-4x improvement through batching
- **Hash Computation**: 5-10x improvement through adaptive sampling
- **Maintainability**: Balance performance gains with code clarity

### Performance Baseline

Current optimizations have achieved a **7.36x speedup** by replacing `Path.rglob()` with `os.scandir()`. This design builds upon that foundation.

---

## Architecture

### Three-Layer Architecture

```
┌─────────────────────────────────────────────────┐
│         Strategy Layer                          │
│  - Scene detection (file count, size, depth)    │
│  - Strategy selector                            │
│  - Performance monitoring and feedback          │
├─────────────────────────────────────────────────┤
│         Execution Layer                          │
│  ┌──────────┬──────────┬──────────┬──────────┐ │
│  │ Scanner  │ Deleter  │ Hasher   │ Cache    │ │
│  └──────────┴──────────┴──────────┴──────────┘ │
│  - Multiple strategies per engine               │
│  - Strategies can be combined                   │
├─────────────────────────────────────────────────┤
│         Infrastructure Layer                    │
│  - Performance profiler                         │
│  - Concurrency pool manager                     │
│  - Memory monitor                               │
└─────────────────────────────────────────────────┘
```

### Key Design Principles

1. **Pluggable Strategies** - Each optimization is independent and can be enabled/disabled
2. **Performance Feedback** - Real-time measurement with dynamic strategy adjustment
3. **Progressive Enhancement** - Basic functionality first, optimizations as overlays
4. **Zero-Dependency Fallback** - Graceful degradation if optimizations fail

---

## Component Design

### 1. Intelligent Scanning Engine

#### QuickProfiler

Rapid scene analysis for optimal strategy selection.

```python
class QuickProfiler:
    """Rapid performance profiler"""

    def profile(self, path: Path, sample_time: float = 0.5) -> ScanProfile:
        """
        Sample analysis to infer scene characteristics:
        - Estimated file count
        - Average file size
        - Directory depth distribution
        - I/O speed
        """
        # Implementation: Short sampling scan to estimate characteristics
```

#### ConcurrentScanner

Multi-threaded directory scanning with bounded queues.

```python
class ConcurrentScanner:
    """Concurrent scanner with optimal worker count"""

    def __init__(self, max_workers: int = None):
        # Default: min(32, (os.cpu_count() or 1) * 4)
        # I/O-bound tasks can use more threads
        self.max_workers = max_workers or self._optimal_workers()

    def scan(self, path: Path) -> Iterator[ScanResult]:
        """
        Concurrent scanning implementation:
        1. Top-level single-threaded (reduce lock contention)
        2. Deep subdirectories concurrent
        3. Bounded queue for memory control
        """
```

**Performance**: 2-4x improvement on multi-core + SSD systems

#### IncrementalCache

Cache-based incremental scanning.

```python
class IncrementalCache:
    """Incremental scan cache"""

    def load_cached_snapshot(self, path: Path) -> Optional[ScanSnapshot]:
        """Load cached scan snapshot"""
        pass

    def diff_scan(self, path: Path, cached: ScanSnapshot) -> ScanDiff:
        """
        Differential scanning:
        - Only scan changed directories
        - Reuse unchanged cache
        """
```

**Cache Strategy**:
- TTL: 7 days (configurable)
- Invalidation: mtime + inode + size
- Compression: gzip compressed storage

**Performance**: 3-5x improvement on repeat scans

#### Strategy Selection Matrix

| Scenario | File Count | File Size | Recommended Strategy |
|----------|-----------|-----------|---------------------|
| Small directory | < 1,000 | Any | Single-thread fast scan |
| Medium directory | 1K - 50K | Small files | Concurrent + batch stat |
| Large directory | > 50K | Mixed | Concurrent + cache + smart exclude |
| Full disk scan | > 100K | Mixed | All strategies + early stop |

---

### 2. Intelligent Deletion Engine

#### BatchDeleter

Smart batched deletion with real-time progress.

```python
class BatchDeleter:
    """Smart batch deleter"""

    def __init__(self):
        self.batch_config = {
            'small': {'count': 1000, 'interval': 0.1},
            'medium': {'count': 5000, 'interval': 0.5},
            'large': {'count': 10000, 'interval': 1.0},
        }

    def delete_with_progress(self, files: List[Path]) -> DeleteResult:
        """
        Batched deletion + real-time progress:
        1. Choose batch strategy based on file count
        2. Delete in batches, update progress after each
        3. Capture failures, continue processing
        4. Support cancellation
        """
```

**Performance**: 2-4x improvement (vs single deletion), responsive UI

#### AsyncDeleter

Background deletion with UI thread separation.

```python
class AsyncDeleter:
    """Async deleter"""

    def __init__(self, max_workers: int = 2):
        # 2 threads enough for deletion (disk I/O bound)
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.progress_queue = Queue()

    def delete_async(self, files: List[Path]) -> Iterator[ProgressUpdate]:
        """
        Async deletion, progress via queue:
        - Background thread executes deletion
        - Main thread reads progress from queue
        - Support cancel and pause
        """
```

**Performance**: UI always responsive, better user experience

#### DeleteStrategy

Smart deletion strategy selection.

```python
class DeleteStrategy:
    """Deletion strategy"""

    DELETE_DIRECT = "direct"      # Direct delete (fastest)
    DELETE_RECYCLE = "recycle"    # Move to recycle bin
    DELETE_SMART = "smart"        # Smart selection

    @staticmethod
    def smart_strategy(file: Path) -> str:
        """
        Smart decision:
        - Small files (< 10MB): direct delete
        - Large files (> 10MB): recycle bin
        - System paths: recycle bin
        - User data: recycle bin
        """
```

**Performance**: 3-5x improvement for large files (skip small files)

#### Deletion Strategy Matrix

| Scenario | File Count | File Size | Recommended Strategy |
|----------|-----------|-----------|---------------------|
| Few small files | < 100 | < 10MB | Single-thread, direct |
| Few large files | < 100 | > 10MB | Async, smart recycle |
| Many small files | > 1000 | < 10MB | Batch + progress |
| Many large files | > 1000 | > 10MB | Async batch + permanent |

---

### 3. Intelligent Hash Engine

#### AdaptiveHasher

Adaptive hash computation based on file size.

```python
class AdaptiveHasher:
    """Adaptive hash calculator"""

    def compute_hash(self, file: Path) -> str:
        """
        Adaptive hash strategy:
        - < 1MB: Full SHA-256
        - 1MB - 100MB: Head + tail + middle sample
        - > 100MB: Multi-segment sample
        """
```

**Performance**: 5-10x improvement for large files, >99% accuracy

#### ParallelHasher

Multi-process concurrent hash computation.

```python
class ParallelHasher:
    """Concurrent hash calculator"""

    def __init__(self, max_workers: int = None):
        # Default: os.cpu_count()
        # Hash is CPU-bound, use processes not threads
        self.max_workers = max_workers or os.cpu_count()

    def hash_files_parallel(self, files: List[Path]) -> Dict[Path, str]:
        """
        Concurrent hash calculation:
        - Use ProcessPoolExecutor
        - Batch processing, reduce process overhead
        - Support progress feedback
        """
```

**Performance**: 2-4x improvement on multi-core CPUs

#### FastFilter

Quick pre-filtering before hash computation.

```python
class FastFilter:
    """Fast pre-filter"""

    def quick_dedup(self, files: List[FileInfo]) -> List[List[FileInfo]]:
        """
        Three-stage filtering:
        1. Group by size (different size = different file)
        2. Group by extension (optional)
        3. Only compute hash for suspected duplicates
        """
```

**Performance**: Reduce 80-90% of hash computations

#### HashCache

LRU cache for computed hashes.

```python
class HashCache:
    """Hash cache"""

    def __init__(self, max_size: int = 10000):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.cache_file = Path.home() / '.disk-cleaner' / 'hash_cache.json'

    def get_or_compute(self, file: Path) -> str:
        """
        Get or compute hash:
        - Key: (path, size, mtime)
        - LRU eviction
        - Persist to disk
        """
```

**Performance**: Near-zero hash time on repeat scans

#### Hash Strategy Matrix

| Scenario | File Count | File Size | Recommended Strategy |
|----------|-----------|-----------|---------------------|
| Few small files | < 100 | < 10MB | Single-thread full SHA-256 |
| Many small files | > 100 | < 10MB | Concurrent + xxhash |
| Few large files | < 100 | > 100MB | Sample hash + concurrent |
| Many large files | > 100 | > 100MB | Sample + concurrent + xxhash |

---

## Infrastructure Layer

### PerformanceProfiler

Real-time performance monitoring.

```python
class PerformanceProfiler:
    """Performance profiler"""

    @contextmanager
    def profile(self, operation: str):
        """
        Context manager for automatic recording:
        with profiler.profile('scan'):
            result = scanner.scan()
        """
```

### ConcurrencyManager

Unified pool management.

```python
class ConcurrencyManager:
    """Concurrency resource manager"""

    def get_thread_pool(self, purpose: str, max_workers: int = None):
        """
        Get or create thread pool:
        purpose: 'io_scan', 'io_delete', 'hash_compute'
        """
```

### MemoryMonitor

Prevent excessive memory usage.

```python
class MemoryMonitor:
    """Memory monitor"""

    def check_memory(self) -> MemoryStatus:
        """
        Check current memory usage:
        return: OK | WARNING | CRITICAL
        """
```

### StrategySelector

Automatic strategy selection based on scene.

```python
class StrategySelector:
    """Strategy selector"""

    def select_scan_strategy(self, profile: ScanProfile) -> ScanStrategy:
        """Select optimal scan strategy based on scene"""
```

---

## Data Flow & Integration

### Core Data Flow

```
User triggers scan
    ↓
[QuickProfiler] Quick scene analysis
    ↓
[StrategySelector] Select optimal strategy
    ↓
[PerformanceProfiler] Start monitoring
    ↓
┌─────────────────────────────────────┐
│  Scan Phase                         │
│  - ConcurrentScanner                │
│  - IncrementalCache                 │
│  - MemoryMonitor                    │
│  - Real-time progress               │
└─────────────────────────────────────┘
    ↓ ScanResult (file list)
┌─────────────────────────────────────┐
│  Analysis Phase                     │
│  - FileClassifier                   │
│  - FastFilter                       │
│  - AdaptiveHasher                   │
│  - DuplicateFinder                  │
└─────────────────────────────────────┘
    ↓ CleanupReport (suggestions)
┌─────────────────────────────────────┐
│  User Confirmation                 │
│  - Interactive UI                   │
│  - Layered display                  │
│  - User selection                   │
└─────────────────────────────────────┘
    ↓ SelectedItems
┌─────────────────────────────────────┐
│  Delete Phase                       │
│  - BatchDeleter                     │
│  - AsyncDeleter                     │
│  - Progress + cancel support        │
└─────────────────────────────────────┘
    ↓
[PerformanceProfiler] Generate report
    ↓
User views results
```

### Integration with Existing Code

**Minimal invasive integration**:

```python
# scripts/analyze_disk.py
def scan_directory(self, path: str = None):
    # Old code preserved as fallback
    # try:
    #     from diskcleaner.optimization import OptimizedScanner
    #     scanner = OptimizedScanner(...)
    #     result = scanner.scan(path)
    # except ImportError:
    #     result = self._legacy_scan(path)
    # return result
```

**Configuration switches**:

```yaml
# config.yaml
optimization:
  enabled: true
  scan:
    concurrent: true
    cache: true
    early_stop: true
  delete:
    batch: true
    async: true
  hash:
    algorithm: auto
    sampling: true
    parallel: true
```

---

## Performance Targets

### Overall Goals

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Scanning speed | > 1000 files/s | files / time |
| Memory usage | < 500MB | psutil / custom |
| CPU usage | < 80% | psutil |
| Cache hit rate | > 60% | cache hits / queries |

### Specific Targets

**Scanning**:
- Small files (10K): < 5 seconds
- Medium directories (50K): < 15 seconds
- Large directories (100K): < 30 seconds

**Deletion**:
- Batch deletion: 10,000 files < 5 seconds
- Large files: 1GB file < 1 second
- Recycle bin overhead: < 20% vs direct delete

**Hashing**:
- Small files (< 1MB): 1000 files < 2 seconds (full SHA-256)
- Medium files (1-100MB): 100 files < 5 seconds (sampled)
- Large files (> 100MB): 10 files < 3 seconds (multi-sample)
- Using xxhash: 8-10x faster than SHA-256

---

## Dependencies

### Required (Standard Library)

- `concurrent.futures` - Thread/process pools
- `threading` - Thread management
- `multiprocessing` - Process pool
- `queue` - Thread-safe queues
- `collections.OrderedDict` - LRU cache
- `pathlib` - Path operations
- `os` - System operations
- `hashlib` - Hash algorithms
- `time` - Timing
- `shutil` - File operations

### Optional (Third-party)

- `xxhash` - Ultra-fast hashing (8-10x faster than SHA-256)
- `blake3` - Fast and secure hashing
- `psutil` - Advanced system monitoring (optional, can fallback to basic)

**Design Principle**: All optimizations work with zero dependencies. External libraries provide additional speedups but are not required.

---

## Implementation Phases

### Phase 1: Infrastructure (Week 1)

- [ ] `PerformanceProfiler` - Performance monitoring
- [ ] `ConcurrencyManager` - Pool management
- [ ] `MemoryMonitor` - Memory tracking
- [ ] Unit tests for infrastructure

### Phase 2: Scanning Optimization (Week 2)

- [ ] `QuickProfiler` - Scene analysis
- [ ] `ConcurrentScanner` - Concurrent scanning
- [ ] `IncrementalCache` - Caching system
- [ ] Integration with `analyze_disk.py`
- [ ] Performance benchmarks

### Phase 3: Deletion Optimization (Week 3)

- [ ] `BatchDeleter` - Batched deletion
- [ ] `AsyncDeleter` - Async deletion
- [ ] `DeleteStrategy` - Smart strategy
- [ ] Integration with `clean_disk.py`
- [ ] Performance benchmarks

### Phase 4: Hash Optimization (Week 4)

- [ ] `AdaptiveHasher` - Adaptive hashing
- [ ] `ParallelHasher` - Concurrent hashing
- [ ] `FastFilter` - Pre-filtering
- [ ] `HashCache` - Hash caching
- [ ] Integration with `duplicate_finder.py`
- [ ] Performance benchmarks

### Phase 5: Integration & Testing (Week 5)

- [ ] `StrategySelector` - Auto strategy selection
- [ ] `OptimizationEngine` - Unified interface
- [ ] Configuration system
- [ ] End-to-end testing
- [ ] Cross-platform validation
- [ ] Performance comparison tool

### Phase 6: Documentation & Release (Week 6)

- [ ] Update user documentation
- [ ] Write performance reports
- [ ] Create usage examples
- [ ] Update CHANGELOG
- [ ] Release v2.0

---

## Risk Mitigation

### Technical Risks

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Concurrency bugs | High | Extensive testing, fallback to single-thread |
| Memory leaks | Medium | Memory monitoring, bounded queues |
| Cache invalidation | Medium | Conservative TTL, multiple keys |
| Platform differences | Medium | Test on all platforms, feature flags |

### Performance Risks

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Overhead > benefit | Medium | Profiling before optimization |
| Degradation on small dirs | Low | Adaptive strategy selection |
| Thread overhead | Low | Bounded thread pools |

---

## Success Criteria

### Performance Criteria

- [ ] Scanning speed: 10-15x improvement (first scan)
- [ ] Cached scanning: 30-50x improvement
- [ ] Deletion speed: 2-4x improvement
- [ ] Hash speed: 5-10x improvement (large files)
- [ ] Memory usage: < 500MB for 100K files

### Quality Criteria

- [ ] All tests pass (unit + integration)
- [ ] Test coverage > 80%
- [ ] No regression in functionality
- [ ] Backward compatibility maintained
- [ ] Cross-platform compatibility verified

### User Experience Criteria

- [ ] Progress bars work smoothly
- [ ] UI remains responsive
- [ ] Cancellation works correctly
- [ ] Configuration is clear
- [ ] Performance is visible to users

---

## Next Steps

1. ✅ **Design complete** - This document
2. ⏸️ **Create implementation plan** - Detailed task breakdown
3. ⏸️ **Setup implementation workspace** - Use git worktree
4. ⏸️ **Begin Phase 1 implementation**

---

## References

- Existing performance document: `performance_progress_improvement.md`
- Task plan: `task_plan.md`
- Implementation tracker: `implementation-tracker.md`
- Design doc: `docs/design-2025-01-22-enhancement.md`

---

**End of Design Document**
