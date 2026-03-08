"""
Duplicate file detector with adaptive strategy.

Detects duplicate files using two strategies:
- Fast: Size + mtime pre-filtering for large directories
- Accurate: SHA-256 hash comparison for smaller directories
"""

import hashlib
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from diskcleaner.core.scanner import FileInfo


@dataclass
class DuplicateGroup:
    """A group of duplicate files."""

    files: List[FileInfo]
    size: int
    hash_value: Optional[str] = None

    @property
    def count(self) -> int:
        """Number of duplicate files."""
        return len(self.files)

    @property
    def reclaimable_space(self) -> int:
        """Space that can be reclaimed (keeping one copy)."""
        return self.size * (self.count - 1)


class DuplicateFinder:
    """
    Duplicate file detector with adaptive strategy.

    Features:
    - Adaptive strategy selection based on file count
    - Fast strategy: size + mtime pre-filtering
    - Accurate strategy: SHA-256 hash comparison
    - Sorted by reclaimable space (descending)
    """

    # Threshold for switching strategies
    ADAPTIVE_THRESHOLD = 1000

    def __init__(self, strategy: str = "adaptive", fast_similarity_threshold: float = 0.95):
        """
        Initialize duplicate finder.

        Args:
            strategy: Detection strategy ('adaptive', 'fast', 'accurate')
            fast_similarity_threshold: Min similarity ratio for fast strategy (0-1)
        """
        if strategy not in ("adaptive", "fast", "accurate"):
            raise ValueError(f"Invalid strategy: {strategy}")

        self.strategy = strategy
        self.fast_similarity_threshold = fast_similarity_threshold

    def find_duplicates(self, files: List[FileInfo]) -> List[DuplicateGroup]:
        """
        Find duplicate files in the given list.

        Args:
            files: List of FileInfo objects to check.

        Returns:
            List of DuplicateGroup objects, sorted by reclaimable space.
        """
        if not files:
            return []

        # Filter out directories (only check files)
        file_list = [f for f in files if not f.is_dir]

        if not file_list:
            return []

        # Determine which strategy to use
        use_accurate = self._should_use_accurate(len(file_list))

        # Find duplicates
        if use_accurate:
            duplicates = self._find_by_hash(file_list)
        else:
            duplicates = self._find_by_fast_strategy(file_list)

        # Sort by reclaimable space (descending)
        duplicates.sort(key=lambda d: d.reclaimable_space, reverse=True)

        return duplicates

    def _should_use_accurate(self, file_count: int) -> bool:
        """
        Determine whether to use accurate strategy.

        Args:
            file_count: Number of files to check.

        Returns:
            True if accurate strategy should be used.
        """
        if self.strategy == "accurate":
            return True
        if self.strategy == "fast":
            return False
        # Adaptive: use accurate for small directories
        return file_count < self.ADAPTIVE_THRESHOLD

    def _find_by_hash(self, files: List[FileInfo]) -> List[DuplicateGroup]:
        """
        Find duplicates using SHA-256 hash comparison.

        This is the most accurate method but slower for large directories.

        Args:
            files: List of FileInfo objects.

        Returns:
            List of DuplicateGroup objects.
        """
        # Group files by hash
        hash_groups: Dict[str, List[FileInfo]] = {}

        for file_info in files:
            try:
                # Calculate file hash
                file_hash = self._calculate_hash(file_info.path)

                if file_hash not in hash_groups:
                    hash_groups[file_hash] = []
                hash_groups[file_hash].append(file_info)
            except (OSError, IOError):
                # Skip files we can't read
                continue

        # Create duplicate groups (only groups with 2+ files)
        duplicates = []
        for hash_value, file_list in hash_groups.items():
            if len(file_list) > 1:
                # All files in this group have the same size
                size = file_list[0].size
                duplicates.append(DuplicateGroup(files=file_list, size=size, hash_value=hash_value))

        return duplicates

    def _find_by_fast_strategy(self, files: List[FileInfo]) -> List[DuplicateGroup]:
        """
        Find duplicates using fast size + mtime strategy.

        Strategy:
        1. Group by exact size (primary filter)
        2. Within size groups, check mtime similarity
        3. Hash verification only for likely duplicates

        This is much faster for large directories but may miss some duplicates
        or have false positives.

        Args:
            files: List of FileInfo objects.

        Returns:
            List of DuplicateGroup objects.
        """
        # Step 1: Group by exact size
        size_groups: Dict[int, List[FileInfo]] = {}
        for file_info in files:
            if file_info.size not in size_groups:
                size_groups[file_info.size] = []
            size_groups[file_info.size].append(file_info)

        # Step 2: For each size group with 2+ files, check mtime similarity
        potential_duplicates: List[Tuple[int, List[FileInfo]]] = []

        for size, file_list in size_groups.items():
            if len(file_list) < 2:
                continue

            # Check if files have similar mtimes (within threshold)
            # Group by mtime buckets (1-second granularity)
            mtime_groups: Dict[int, List[FileInfo]] = {}
            for file_info in file_list:
                mtime_bucket = int(file_info.mtime)
                if mtime_bucket not in mtime_groups:
                    mtime_groups[mtime_bucket] = []
                mtime_groups[mtime_bucket].append(file_info)

            # Find files in same mtime bucket (likely duplicates)
            for mtime_bucket, same_time_files in mtime_groups.items():
                if len(same_time_files) >= 2:
                    potential_duplicates.append((size, same_time_files))

        # Step 3: Hash verification for potential duplicates
        # (to avoid false positives from fast strategy)
        verified_duplicates: List[DuplicateGroup] = []

        for size, file_list in potential_duplicates:
            # Calculate hashes for these files
            hash_groups: Dict[str, List[FileInfo]] = {}

            for file_info in file_list:
                try:
                    file_hash = self._calculate_hash(file_info.path)

                    if file_hash not in hash_groups:
                        hash_groups[file_hash] = []
                    hash_groups[file_hash].append(file_info)
                except (OSError, IOError):
                    continue

            # Add verified duplicate groups
            for hash_value, same_hash_files in hash_groups.items():
                if len(same_hash_files) >= 2:
                    verified_duplicates.append(
                        DuplicateGroup(files=same_hash_files, size=size, hash_value=hash_value)
                    )

        return verified_duplicates

    def _calculate_hash(self, file_path: str, chunk_size: int = 8192) -> str:
        """
        Calculate SHA-256 hash of a file.

        Args:
            file_path: Path to file.
            chunk_size: Read chunk size in bytes.

        Returns:
            Hexadecimal hash string.
        """
        sha256_hash = hashlib.sha256()

        with open(file_path, "rb") as f:
            # Read file in chunks to handle large files
            while chunk := f.read(chunk_size):
                sha256_hash.update(chunk)

        return sha256_hash.hexdigest()

    def get_duplicate_stats(self, duplicates: List[DuplicateGroup]) -> Dict[str, int]:
        """
        Calculate statistics about duplicate files.

        Args:
            duplicates: List of DuplicateGroup objects.

        Returns:
            Dictionary with statistics:
            {
                "group_count": number of duplicate groups,
                "file_count": total duplicate files,
                "total_size": total size of all duplicates,
                "reclaimable": space that can be reclaimed
            }
        """
        if not duplicates:
            return {
                "group_count": 0,
                "file_count": 0,
                "total_size": 0,
                "reclaimable": 0,
            }

        total_files = sum(d.count for d in duplicates)
        total_size = sum(d.size * d.count for d in duplicates)
        total_reclaimable = sum(d.reclaimable_space for d in duplicates)

        return {
            "group_count": len(duplicates),
            "file_count": total_files,
            "total_size": total_size,
            "reclaimable": total_reclaimable,
        }
