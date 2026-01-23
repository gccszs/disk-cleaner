"""
Optimized hash computation components.

Provides:
- AdaptiveHasher: Size-based adaptive hashing
- ParallelHasher: Concurrent hash computation
- FastFilter: Quick pre-filtering for duplicate detection
- HashCache: LRU cache for computed hashes
"""

import os
import hashlib
import threading
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple, Callable
from concurrent.futures import ProcessPoolExecutor, as_completed
from collections import OrderedDict
import time

from diskcleaner.optimization.scan import FileInfo


@dataclass
class DuplicateGroup:
    """Group of duplicate files."""
    files: List[FileInfo]
    size: int
    count: int
    hash_value: str
    reclaimable_space: int

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'files': [f.to_dict() for f in self.files],
            'size': self.size,
            'count': self.count,
            'hash': self.hash_value,
            'reclaimable': self.reclaimable_space,
        }


class AdaptiveHasher:
    """
    Adaptive hash computation based on file size.

    Automatically selects optimal hashing strategy:
    - Small files (< 1MB): Full hash
    - Medium files (1-100MB): Sampled hash (head, middle, tail)
    - Large files (> 100MB): Multi-segment sampling
    """

    def __init__(self, algorithm: str = 'auto', chunk_size: int = 1024 * 1024):
        """
        Initialize adaptive hasher.

        Args:
            algorithm: Hash algorithm ('auto', 'sha256', 'xxhash')
            chunk_size: Chunk size for reading (1MB default)
        """
        self.algorithm = self._choose_algorithm(algorithm)
        self.chunk_size = chunk_size

    def compute_hash(self, file: Path) -> str:
        """
        Compute hash using adaptive strategy.

        Args:
            file: File to hash

        Returns:
            Hexadecimal hash string
        """
        if not file.exists() or not file.is_file():
            return ""

        try:
            size = file.stat().st_size

            # Choose strategy based on size
            if size < 1 * 1024 * 1024:  # < 1MB
                return self._full_hash(file)
            elif size < 100 * 1024 * 1024:  # 1-100MB
                return self._sample_hash(file, chunks=[0.0, 0.5, 1.0])
            else:  # > 100MB
                return self._multi_sample_hash(file, chunks=10)
        except (OSError, IOError):
            return ""

    def _full_hash(self, file: Path) -> str:
        """Compute full file hash."""
        h = self.algorithm()

        with open(file, 'rb') as f:
            # Use large chunk reading for efficiency
            for chunk in iter(lambda: f.read(self.chunk_size), b''):
                h.update(chunk)

        return h.hexdigest()

    def _sample_hash(self, file: Path, chunks: List[float]) -> str:
        """
        Compute sampled hash from specific positions.

        Args:
            file: File to hash
            chunks: List of chunk positions (0.0-1.0)

        Returns:
            Hexadecimal hash string
        """
        h = self.algorithm()
        size = file.stat().st_size

        with open(file, 'rb') as f:
            for chunk_pos in chunks:
                offset = int(size * chunk_pos)
                f.seek(offset)
                data = f.read(self.chunk_size)
                h.update(data)

        return h.hexdigest()

    def _multi_sample_hash(self, file: Path, chunks: int) -> str:
        """
        Compute hash from multiple segments.

        Args:
            file: File to hash
            chunks: Number of segments

        Returns:
            Hexadecimal hash string
        """
        h = self.algorithm()
        size = file.stat().st_size

        with open(file, 'rb') as f:
            for i in range(chunks):
                offset = int(size * i / chunks)
                f.seek(offset)
                data = f.read(self.chunk_size)
                h.update(data)

        return h.hexdigest()

    def _choose_algorithm(self, algorithm: str) -> Callable:
        """
        Choose hash algorithm.

        Args:
            algorithm: Algorithm name

        Returns:
            Hash constructor function
        """
        if algorithm == 'auto':
            # Try fastest available
            try:
                import xxhash
                return xxhash.xxh3_128
            except ImportError:
                pass

            try:
                import blake3
                return blake3.blake3
            except ImportError:
                pass

            return hashlib.sha256

        elif algorithm == 'sha256':
            return hashlib.sha256

        elif algorithm == 'xxhash':
            try:
                import xxhash
                return xxhash.xxh3_128
            except ImportError:
                return hashlib.sha256

        elif algorithm == 'blake3':
            try:
                import blake3
                return blake3.blake3
            except ImportError:
                return hashlib.sha256

        else:
            return hashlib.sha256


class ParallelHasher:
    """
    Concurrent hash computation using process pool.

    Optimized for CPU-bound hash computation.
    """

    def __init__(self, max_workers: Optional[int] = None, algorithm: str = 'auto'):
        """
        Initialize parallel hasher.

        Args:
            max_workers: Number of worker processes (None = CPU count)
            algorithm: Hash algorithm to use
        """
        self.max_workers = max_workers or os.cpu_count()
        self.algorithm = algorithm
        self.executor: Optional[ProcessPoolExecutor] = None

    def hash_files_parallel(self,
                           files: List[Path],
                           progress_callback=None) -> Dict[Path, str]:
        """
        Compute hashes for multiple files in parallel.

        Args:
            files: Files to hash
            progress_callback: Optional progress callback

        Returns:
            Dict mapping file paths to hash values
        """
        if not files:
            return {}

        result: Dict[Path, str] = {}
        self.executor = ProcessPoolExecutor(max_workers=self.max_workers)

        # Submit all tasks
        futures = {}
        for file in files:
            future = self.executor.submit(self._hash_single_file, str(file), self.algorithm)
            futures[future] = file

        # Collect results
        completed = 0
        for future in as_completed(futures):
            file = futures[future]
            try:
                hash_value = future.result(timeout=60.0)
                result[file] = hash_value
            except Exception:
                result[file] = ""  # Mark as failed

            completed += 1

            if progress_callback:
                progress_callback({
                    'current': completed,
                    'total': len(files),
                    'file': str(file),
                })

        # Cleanup
        self.executor.shutdown(wait=True)
        self.executor = None

        return result

    @staticmethod
    def _hash_single_file(file_path: str, algorithm: str = 'auto') -> str:
        """
        Static method: Compute hash for a single file.

        Runs in worker process.

        Args:
            file_path: Path to file
            algorithm: Hash algorithm

        Returns:
            Hexadecimal hash string
        """
        hasher = AdaptiveHasher(algorithm=algorithm)
        return hasher.compute_hash(Path(file_path))

    def shutdown(self):
        """Shutdown executor."""
        if self.executor:
            self.executor.shutdown(wait=False)
            self.executor = None


class FastFilter:
    """
    Fast pre-filtering for duplicate file detection.

    Eliminates obvious non-duplicates before expensive hashing.
    """

    def __init__(self):
        """Initialize fast filter."""
        pass

    def quick_dedup(self, files: List[FileInfo]) -> List[List[FileInfo]]:
        """
        Quick pre-filtering using size grouping.

        Args:
            files: Files to filter

        Returns:
            List of file groups that might be duplicates
        """
        # Group by size
        by_size: Dict[int, List[FileInfo]] = {}

        for file in files:
            size = file.size
            if size not in by_size:
                by_size[size] = []
            by_size[size].append(file)

        # Only keep groups with multiple files
        candidates = [group for group in by_size.values() if len(group) > 1]

        return candidates

    def filter_by_extension(self,
                           files: List[FileInfo],
                           extensions: Optional[List[str]] = None) -> List[FileInfo]:
        """
        Filter files by extension.

        Args:
            files: Files to filter
            extensions: List of extensions to keep (None = all)

        Returns:
            Filtered file list
        """
        if extensions is None:
            return files

        ext_set = set(ext.lower() for ext in extensions)
        return [f for f in files if Path(f.path).suffix.lower() in ext_set]

    def filter_by_size(self,
                      files: List[FileInfo],
                      min_size: int = 0,
                      max_size: Optional[int] = None) -> List[FileInfo]:
        """
        Filter files by size range.

        Args:
            files: Files to filter
            min_size: Minimum file size (bytes)
            max_size: Maximum file size (None = no limit)

        Returns:
            Filtered file list
        """
        result = [f for f in files if f.size >= min_size]

        if max_size is not None:
            result = [f for f in result if f.size <= max_size]

        return result


class HashCache:
    """
    LRU cache for computed hash values.

    Reduces redundant hash computations.
    """

    def __init__(self, max_size: int = 10000):
        """
        Initialize hash cache.

        Args:
            max_size: Maximum number of cached entries
        """
        self.cache: OrderedDict[Tuple[str, int, float], str] = OrderedDict()
        self.max_size = max_size
        self.lock = threading.Lock()
        self.hits = 0
        self.misses = 0

    def get_or_compute(self,
                      file: Path,
                      compute_func: Optional[Callable] = None) -> Optional[str]:
        """
        Get cached hash or compute if not cached.

        Args:
            file: File to get hash for
            compute_func: Optional function to compute hash if not cached

        Returns:
            Hash string, or None if not cached and no compute_func provided
        """
        try:
            stat = file.stat()
            key = (str(file), stat.st_size, stat.st_mtime)
        except OSError:
            if compute_func:
                return compute_func(file)
            return None

        with self.lock:
            # Check cache
            if key in self.cache:
                self.hits += 1
                # Move to end (most recently used)
                self.cache.move_to_end(key)
                return self.cache[key]

            self.misses += 1

            # Compute if function provided
            if compute_func:
                hash_value = compute_func(file)

                if hash_value:
                    # Add to cache
                    self.cache[key] = hash_value
                    self.cache.move_to_end(key)

                    # Evict oldest if over limit
                    if len(self.cache) > self.max_size:
                        self.cache.popitem(last=False)

                return hash_value

        return None

    def get(self, file: Path) -> Optional[str]:
        """
        Get cached hash without computing.

        Args:
            file: File to get hash for

        Returns:
            Cached hash string, or None if not cached
        """
        try:
            stat = file.stat()
            key = (str(file), stat.st_size, stat.st_mtime)
        except OSError:
            return None

        with self.lock:
            if key in self.cache:
                self.hits += 1
                self.cache.move_to_end(key)
                return self.cache[key]
            else:
                self.misses += 1
                return None

    def put(self, file: Path, hash_value: str) -> None:
        """
        Add hash to cache.

        Args:
            file: File path
            hash_value: Hash value to cache
        """
        try:
            stat = file.stat()
            key = (str(file), stat.st_size, stat.st_mtime)
        except OSError:
            return

        with self.lock:
            self.cache[key] = hash_value
            self.cache.move_to_end(key)

            # Evict oldest if over limit
            if len(self.cache) > self.max_size:
                self.cache.popitem(last=False)

    def invalidate(self, file: Path) -> None:
        """
        Invalidate cached hash for a file.

        Args:
            file: File to invalidate
        """
        try:
            stat = file.stat()
            key = (str(file), stat.st_size, stat.st_mtime)
        except OSError:
            return

        with self.lock:
            if key in self.cache:
                del self.cache[key]

    def clear(self) -> None:
        """Clear all cached entries."""
        with self.lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0

    def get_stats(self) -> Dict[str, int]:
        """
        Get cache statistics.

        Returns:
            Dict with cache stats
        """
        with self.lock:
            total = self.hits + self.misses
            hit_rate = self.hits / total if total > 0 else 0

            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'hits': self.hits,
                'misses': self.misses,
                'hit_rate': int(hit_rate * 100),  # percentage
            }


class DuplicateFinder:
    """
    High-level duplicate file finder.

    Combines all optimization components for efficient duplicate detection.
    """

    def __init__(self,
                 use_parallel: bool = True,
                 use_cache: bool = True,
                 algorithm: str = 'auto'):
        """
        Initialize duplicate finder.

        Args:
            use_parallel: Whether to use parallel hashing
            use_cache: Whether to use hash caching
            algorithm: Hash algorithm to use
        """
        self.use_parallel = use_parallel
        self.use_cache = use_cache
        self.algorithm = algorithm

        self.hasher = AdaptiveHasher(algorithm=algorithm)
        self.parallel_hasher: Optional[ParallelHasher] = None
        self.cache: Optional[HashCache] = None
        self.filter = FastFilter()

        if use_parallel:
            self.parallel_hasher = ParallelHasher(algorithm=algorithm)

        if use_cache:
            self.cache = HashCache()

    def find_duplicates(self,
                       files: List[FileInfo],
                       progress_callback=None) -> List[DuplicateGroup]:
        """
        Find duplicate files using adaptive strategy.

        Args:
            files: Files to check
            progress_callback: Optional progress callback

        Returns:
            List of duplicate groups, sorted by reclaimable space
        """
        if not files:
            return []

        # Step 1: Fast pre-filtering
        if progress_callback:
            progress_callback({'stage': 'filtering', 'message': 'Quick pre-filtering'})

        candidates = self.filter.quick_dedup(files)

        if not candidates:
            return []

        # Flatten candidates for hashing
        files_to_hash = []
        for group in candidates:
            files_to_hash.extend(group)

        # Step 2: Compute hashes
        if progress_callback:
            progress_callback({'stage': 'hashing', 'message': 'Computing hashes'})

        if self.use_parallel and len(files_to_hash) > 10:
            hashes = self._hash_parallel(files_to_hash, progress_callback)
        else:
            hashes = self._hash_sequential(files_to_hash, progress_callback)

        # Step 3: Group by hash
        hash_groups: Dict[str, List[FileInfo]] = {}
        for file in files_to_hash:
            hash_value = hashes.get(file.path, "")
            if not hash_value:
                continue

            if hash_value not in hash_groups:
                hash_groups[hash_value] = []
            hash_groups[hash_value].append(file)

        # Step 4: Create duplicate groups (only actual duplicates)
        duplicates = []
        for hash_value, group in hash_groups.items():
            if len(group) > 1:  # Only if multiple files have same hash
                size = group[0].size
                duplicates.append(DuplicateGroup(
                    files=group,
                    size=size,
                    count=len(group),
                    hash_value=hash_value,
                    reclaimable_space=size * (len(group) - 1),
                ))

        # Sort by reclaimable space (descending)
        duplicates.sort(key=lambda d: d.reclaimable_space, reverse=True)

        return duplicates

    def _hash_sequential(self,
                        files: List[FileInfo],
                        progress_callback=None) -> Dict[str, str]:
        """Compute hashes sequentially."""
        hashes = {}

        for i, file_info in enumerate(files):
            file = Path(file_info.path)

            if self.cache:
                hash_value = self.cache.get_or_compute(
                    file,
                    self.hasher.compute_hash
                )
            else:
                hash_value = self.hasher.compute_hash(file)

            hashes[file_info.path] = hash_value

            if progress_callback and i % 10 == 0:
                progress_callback({
                    'current': i,
                    'total': len(files),
                })

        return hashes

    def _hash_parallel(self,
                      files: List[FileInfo],
                      progress_callback=None) -> Dict[str, str]:
        """Compute hashes in parallel."""
        file_paths = [Path(f.path) for f in files]

        hashes = self.parallel_hasher.hash_files_parallel(
            file_paths,
            progress_callback
        )

        return hashes

    def get_cache_stats(self) -> Optional[Dict[str, int]]:
        """Get cache statistics if caching is enabled."""
        if self.cache:
            return self.cache.get_stats()
        return None

    def clear_cache(self) -> None:
        """Clear hash cache if caching is enabled."""
        if self.cache:
            self.cache.clear()

    def shutdown(self) -> None:
        """Cleanup resources."""
        if self.parallel_hasher:
            self.parallel_hasher.shutdown()
