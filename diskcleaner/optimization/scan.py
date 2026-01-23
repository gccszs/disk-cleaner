"""
Optimized scanning components.

Provides:
- QuickProfiler: Fast scene analysis
- ConcurrentScanner: Multi-threaded directory scanning
- IncrementalCache: Scan result caching
"""

import hashlib
import json
import os
import queue
import threading
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from diskcleaner.optimization.memory import MemoryMonitor


@dataclass
class ScanProfile:
    """Profile of a scanning scene."""

    file_count: int = 0
    total_size: int = 0
    dir_count: int = 0
    max_depth: int = 0
    avg_file_size: float = 0.0
    files_per_second: float = 0.0
    estimated_time: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class FileInfo:
    """Information about a file or directory."""

    path: str
    name: str
    size: int
    mtime: float
    is_dir: bool = False
    depth: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FileInfo":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class ScanResult:
    """Result of a scan operation."""

    items: List[FileInfo]
    total_count: int
    total_size: int
    error_count: int = 0
    scan_time: float = 0.0
    stopped_early: bool = False
    stop_reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "items": [item.to_dict() for item in self.items],
            "total_count": self.total_count,
            "total_size": self.total_size,
            "error_count": self.error_count,
            "scan_time": self.scan_time,
            "stopped_early": self.stopped_early,
            "stop_reason": self.stop_reason,
        }


@dataclass
class ScanSnapshot:
    """Snapshot of a scan for caching."""

    path: str
    timestamp: float
    items: List[FileInfo]
    total_count: int
    total_size: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "path": self.path,
            "timestamp": self.timestamp,
            "items": [item.to_dict() for item in self.items],
            "total_count": self.total_count,
            "total_size": self.total_size,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScanSnapshot":
        """Create from dictionary."""
        data["items"] = [FileInfo.from_dict(item) for item in data["items"]]
        return cls(**data)


class QuickProfiler:
    """
    Fast scene profiler for scanning strategy selection.

    Performs short sampling to infer directory characteristics.
    """

    def __init__(self, sample_time: float = 0.5):
        """
        Initialize profiler.

        Args:
            sample_time: Sampling time in seconds
        """
        self.sample_time = sample_time

    def profile(self, path: Path) -> ScanProfile:
        """
        Profile a directory by sampling.

        Args:
            path: Directory to profile

        Returns:
            ScanProfile with inferred characteristics
        """
        if not path.exists():
            return ScanProfile()

        result = ScanProfile()
        stop_flag = threading.Event()
        profile_data = {
            "file_count": 0,
            "total_size": 0,
            "dir_count": 0,
            "max_depth": 0,
            "sampled_files": 0,
        }
        lock = threading.Lock()

        def scan_worker():
            """Background scanning thread."""
            try:
                for root, dirs, files in os.walk(str(path)):
                    if stop_flag.is_set():
                        break

                    with lock:
                        profile_data["dir_count"] += len(dirs)
                        profile_data["file_count"] += len(files)

                        # Sample file sizes (first 100)
                        for i, f in enumerate(files[:100]):
                            try:
                                file_path = Path(root) / f
                                if file_path.is_file():
                                    profile_data["total_size"] += file_path.stat().st_size
                                    profile_data["sampled_files"] += 1
                            except (OSError, PermissionError):
                                pass

                        # Calculate depth
                        depth = root[len(str(path)) :].count(os.sep)
                        profile_data["max_depth"] = max(profile_data["max_depth"], depth)

            except Exception:
                pass  # Errors don't prevent sampling

        # Start sampling thread
        thread = threading.Thread(target=scan_worker, daemon=True)
        thread.start()
        thread.join(timeout=self.sample_time)
        stop_flag.set()

        # Calculate derived metrics
        result.file_count = profile_data["file_count"]
        result.total_size = profile_data["total_size"]
        result.dir_count = profile_data["dir_count"]
        result.max_depth = profile_data["max_depth"]

        if profile_data["sampled_files"] > 0:
            result.avg_file_size = profile_data["total_size"] / profile_data["sampled_files"]

        if self.sample_time > 0:
            result.files_per_second = result.file_count / self.sample_time

        # Estimate full scan time (with 2x safety margin)
        if result.files_per_second > 0:
            result.estimated_time = (result.file_count / result.files_per_second) * 2

        return result


class ConcurrentScanner:
    """
    Concurrent directory scanner with bounded queues.

    Uses thread pool for concurrent I/O operations.
    """

    def __init__(
        self,
        max_workers: Optional[int] = None,
        strategy: Optional["ScanStrategy"] = None,
        memory_monitor: Optional[MemoryMonitor] = None,
        progress_callback=None,
    ):
        """
        Initialize concurrent scanner.

        Args:
            max_workers: Maximum worker threads (None for auto)
            strategy: Scanning strategy options
            memory_monitor: Memory monitoring instance
            progress_callback: Optional callback for progress updates
        """
        self.max_workers = max_workers or self._optimal_workers()
        self.strategy = strategy or ScanStrategy()
        self.memory_monitor = memory_monitor
        self.progress_callback = progress_callback

        # Bounded queue to prevent memory explosion
        self.queue_size = 10000

    def scan(self, path: Path, progress_callback=None) -> ScanResult:
        """
        Concurrently scan a directory.

        Args:
            path: Directory to scan
            progress_callback: Optional progress callback

        Returns:
            ScanResult with all found items
        """
        if not path.exists() or not path.is_dir():
            return ScanResult(items=[], total_count=0, total_size=0)

        results = []
        work_queue = Queue(maxsize=self.queue_size)
        stop_event = threading.Event()
        result_lock = threading.Lock()
        callback = progress_callback or self.progress_callback

        # Statistics
        stats = {"count": 0, "errors": 0, "size": 0}

        def worker(thread_id: int):
            """Worker thread: process directories from queue."""
            while not stop_event.is_set():
                try:
                    dir_path = work_queue.get(timeout=0.1)
                except Empty:
                    continue

                # Check memory
                if self.memory_monitor and self.memory_monitor.should_pause():
                    stop_event.set()
                    break

                # Scan single directory
                try:
                    with os.scandir(dir_path) as entries:
                        dir_entries = []

                        for entry in entries:
                            if stop_event.is_set():
                                break

                            try:
                                stat = entry.stat()
                                item = FileInfo(
                                    path=entry.path,
                                    name=entry.name,
                                    size=stat.st_size,
                                    mtime=stat.st_mtime,
                                    is_dir=entry.is_dir(follow_symlinks=False),
                                )

                                with result_lock:
                                    results.append(item)
                                    stats["count"] += 1
                                    stats["size"] += item.size

                                # Add subdirectories to work queue
                                if entry.is_dir(follow_symlinks=False):
                                    if not self.strategy.should_exclude(entry.path):
                                        dir_entries.append(entry.path)

                            except (OSError, PermissionError):
                                with result_lock:
                                    stats["errors"] += 1
                                continue

                        # Add subdirectories to queue
                        for subdir in dir_entries:
                            try:
                                work_queue.put(subdir, timeout=1.0)
                            except queue.Full:
                                # Queue full, stop scanning
                                stop_event.set()

                except Exception:
                    pass

                finally:
                    work_queue.task_done()

                # Progress callback
                if callback and stats["count"] % 100 == 0:
                    callback(
                        {
                            "count": stats["count"],
                            "errors": stats["errors"],
                            "size": stats["size"],
                        }
                    )

        # Start worker threads
        workers = [
            threading.Thread(target=worker, args=(i,), daemon=True) for i in range(self.max_workers)
        ]

        for w in workers:
            w.start()

        # Main thread: scan top level and seed queue
        start_time = time.time()

        try:
            with os.scandir(str(path)) as entries:
                for entry in entries:
                    if stop_event.is_set():
                        break

                    try:
                        stat = entry.stat()
                        item = FileInfo(
                            path=entry.path,
                            name=entry.name,
                            size=stat.st_size,
                            mtime=stat.st_mtime,
                            is_dir=entry.is_dir(follow_symlinks=False),
                        )

                        with result_lock:
                            results.append(item)
                            stats["count"] += 1
                            stats["size"] += item.size

                        # Add directory to work queue
                        if entry.is_dir(follow_symlinks=False):
                            if not self.strategy.should_exclude(entry.path):
                                work_queue.put(entry.path)

                    except (OSError, PermissionError):
                        stats["errors"] += 1
                        continue

            # Wait for all work to complete
            work_queue.join()
            stop_event.set()

            # Wait for workers to finish
            for w in workers:
                w.join(timeout=5.0)

        except Exception:
            stop_event.set()

        scan_time = time.time() - start_time

        return ScanResult(
            items=results,
            total_count=stats["count"],
            total_size=stats["size"],
            error_count=stats["errors"],
            scan_time=scan_time,
            stopped_early=stop_event.is_set(),
        )

    def _optimal_workers(self) -> int:
        """Calculate optimal worker thread count."""
        cpu_count = os.cpu_count() or 1
        # I/O bound, can use more threads
        return min(32, cpu_count * 4)


class ScanStrategy:
    """
    Scanning strategy configuration.

    Defines which optimizations to apply.
    """

    # Default exclude patterns
    DEFAULT_EXCLUDES = [
        # Windows
        "C:\\Windows",
        "C:\\Program Files",
        "C:\\Program Files (x86)",
        "C:\\ProgramData",
        # macOS
        "/System",
        "/Library",
        "/.Spotlight-V100",
        "/.fseventsd",
        "/.vol",
        "/private/var/vm",
        # Linux
        "/proc",
        "/sys",
        "/dev",
        "/run",
        "/boot",
    ]

    def __init__(self):
        """Initialize with default strategy."""
        self.concurrent = True
        self.cache_enabled = True
        self.early_stop = False
        self.max_files = 50000
        self.max_time = 25  # seconds
        self.excludes = list(self.DEFAULT_EXCLUDES)

    def should_exclude(self, path: str) -> bool:
        """
        Check if path should be excluded.

        Args:
            path: Path to check

        Returns:
            True if path should be excluded
        """
        path_normalized = os.path.normpath(path)

        for exclude in self.excludes:
            if path_normalized.startswith(exclude):
                return True

        return False

    def should_stop_early(self, current_count: int, elapsed_time: float) -> bool:
        """
        Check if scanning should stop early.

        Args:
            current_count: Number of items scanned
            elapsed_time: Time elapsed in seconds

        Returns:
            True if should stop
        """
        if not self.early_stop:
            return False

        if current_count >= self.max_files:
            return True

        if elapsed_time >= self.max_time:
            return True

        return False


class IncrementalCache:
    """
    Incremental scan cache.

    Caches scan results to speed up repeat scans.
    """

    def __init__(self, cache_dir: Optional[Path] = None, ttl_days: int = 7):
        """
        Initialize cache.

        Args:
            cache_dir: Cache directory path (None for default)
            ttl_days: Time-to-live for cache entries in days
        """
        self.cache_dir = cache_dir or Path.home() / ".disk-cleaner" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = ttl_days * 24 * 3600  # Convert to seconds
        self._memory_cache: Dict[str, ScanSnapshot] = {}

    def _get_cache_path(self, path: str) -> Path:
        """Get cache file path for a directory."""
        # Use hash of path as cache key
        path_hash = hashlib.md5(str(path).encode()).hexdigest()
        return self.cache_dir / f"{path_hash}.json"

    def get_cached_snapshot(self, path: Path) -> Optional[ScanSnapshot]:
        """
        Get cached snapshot if available and valid.

        Args:
            path: Directory path

        Returns:
            ScanSnapshot if cached and valid, None otherwise
        """
        # Check memory cache first
        cache_key = str(path)
        if cache_key in self._memory_cache:
            snapshot = self._memory_cache[cache_key]
            if self._is_valid(snapshot):
                return snapshot
            else:
                del self._memory_cache[cache_key]

        # Check disk cache
        cache_file = self._get_cache_path(str(path))

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, "r") as f:
                data = json.load(f)
            snapshot = ScanSnapshot.from_dict(data)

            if not self._is_valid(snapshot):
                cache_file.unlink()  # Remove expired cache
                return None

            # Store in memory cache
            self._memory_cache[cache_key] = snapshot
            return snapshot

        except (json.JSONDecodeError, KeyError, IOError):
            return None

    def save_snapshot(self, path: Path, snapshot: ScanSnapshot) -> None:
        """
        Save a snapshot to cache.

        Args:
            path: Directory path
            snapshot: Snapshot to save
        """
        cache_key = str(path)

        # Store in memory
        self._memory_cache[cache_key] = snapshot

        # Store on disk
        cache_file = self._get_cache_path(str(path))

        try:
            with open(cache_file, "w") as f:
                json.dump(snapshot.to_dict(), f)
        except IOError:
            pass  # Fail silently

    def _is_valid(self, snapshot: ScanSnapshot) -> bool:
        """Check if snapshot is still valid."""
        age = time.time() - snapshot.timestamp
        return age < self.ttl

    def invalidate(self, path: Path) -> None:
        """
        Invalidate cache for a path.

        Args:
            path: Directory path to invalidate
        """
        cache_key = str(path)

        # Remove from memory
        if cache_key in self._memory_cache:
            del self._memory_cache[cache_key]

        # Remove from disk
        cache_file = self._get_cache_path(str(path))
        if cache_file.exists():
            cache_file.unlink()

    def clear_all(self) -> None:
        """Clear all cache."""
        self._memory_cache.clear()

        # Clear disk cache
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()

    def get_cache_size(self) -> int:
        """Get total cache size in bytes."""
        size = 0
        for cache_file in self.cache_dir.glob("*.json"):
            size += cache_file.stat().st_size
        return size
