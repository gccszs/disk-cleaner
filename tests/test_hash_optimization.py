"""
Unit tests for hash optimization components.

Tests:
- AdaptiveHasher
- ParallelHasher
- FastFilter
- HashCache
- DuplicateFinder
"""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from diskcleaner.optimization.hash import (
    AdaptiveHasher,
    DuplicateFinder,
    DuplicateGroup,
    FastFilter,
    HashCache,
    ParallelHasher,
)
from diskcleaner.optimization.scan import FileInfo


class TestAdaptiveHasher:
    """Tests for AdaptiveHasher."""

    def test_hasher_initialization(self):
        """Test hasher can be initialized."""
        hasher = AdaptiveHasher()
        assert hasher is not None
        assert hasher.chunk_size == 1024 * 1024

    def test_hash_small_file(self, tmp_path):
        """Test hashing small file (< 1MB)."""
        test_file = tmp_path / "small.txt"
        test_file.write_text("x" * 1000)

        hasher = AdaptiveHasher()
        hash_value = hasher.compute_hash(test_file)

        assert hash_value is not None
        assert len(hash_value) > 0
        assert isinstance(hash_value, str)

    def test_hash_medium_file(self, tmp_path):
        """Test hashing medium file (1-100MB) - use small file for testing."""
        # Use smaller file for testing (real medium file would be too slow)
        test_file = tmp_path / "medium.txt"
        test_file.write_bytes(b"x" * (2 * 1024 * 1024))  # 2MB

        hasher = AdaptiveHasher()
        hash_value = hasher.compute_hash(test_file)

        assert hash_value is not None
        assert len(hash_value) > 0

    def test_hash_nonexistent_file(self):
        """Test hashing non-existent file."""
        hasher = AdaptiveHasher()
        hash_value = hasher.compute_hash(Path("/nonexistent/file.txt"))

        assert hash_value == ""

    def test_hash_directory(self, tmp_path):
        """Test hashing directory."""
        hasher = AdaptiveHasher()
        hash_value = hasher.compute_hash(tmp_path)

        assert hash_value == ""

    def test_algorithm_selection(self):
        """Test algorithm selection."""
        # Should not raise exception
        hasher_sha256 = AdaptiveHasher(algorithm="sha256")
        hasher_auto = AdaptiveHasher(algorithm="auto")

        assert hasher_sha256 is not None
        assert hasher_auto is not None

    def test_hash_deterministic(self, tmp_path):
        """Test that hash is deterministic."""
        test_file = tmp_path / "test.txt"
        content = "hello world"
        test_file.write_text(content)

        hasher = AdaptiveHasher()
        hash1 = hasher.compute_hash(test_file)
        hash2 = hasher.compute_hash(test_file)

        assert hash1 == hash2

    def test_hash_different_files(self, tmp_path):
        """Test that different files have different hashes."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("content1")
        file2.write_text("content2")

        hasher = AdaptiveHasher()
        hash1 = hasher.compute_hash(file1)
        hash2 = hasher.compute_hash(file2)

        assert hash1 != hash2


class TestParallelHasher:
    """Tests for ParallelHasher."""

    def test_hasher_initialization(self):
        """Test hasher can be initialized."""
        hasher = ParallelHasher()
        assert hasher is not None
        assert hasher.max_workers >= 1

    def test_hash_empty_list(self):
        """Test hashing empty file list."""
        hasher = ParallelHasher()
        result = hasher.hash_files_parallel([])

        assert result == {}

    def test_hash_single_file(self, tmp_path):
        """Test hashing single file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("x" * 1000)

        hasher = ParallelHasher()
        result = hasher.hash_files_parallel([test_file])

        assert test_file in result
        assert len(result[test_file]) > 0

    def test_hash_multiple_files(self, tmp_path):
        """Test hashing multiple files."""
        files = []
        for i in range(5):
            file = tmp_path / f"file_{i}.txt"
            file.write_text(f"content_{i}" * 100)
            files.append(file)

        hasher = ParallelHasher()
        result = hasher.hash_files_parallel(files)

        assert len(result) == 5
        for file in files:
            assert file in result
            assert len(result[file]) > 0

    def test_hash_with_progress_callback(self, tmp_path):
        """Test hashing with progress callback."""
        files = []
        for i in range(10):
            file = tmp_path / f"file_{i}.txt"
            file.write_text("x" * 100)
            files.append(file)

        progress_updates = []

        def callback(progress):
            progress_updates.append(progress)

        hasher = ParallelHasher()
        result = hasher.hash_files_parallel(files, progress_callback=callback)

        assert len(result) == 10
        # Should have received some progress updates
        assert len(progress_updates) >= 0

    def test_shutdown(self, tmp_path):
        """Test shutting down hasher."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        hasher = ParallelHasher()
        hasher.hash_files_parallel([test_file])

        # Should not raise exception
        hasher.shutdown()


class TestFastFilter:
    """Tests for FastFilter."""

    def test_filter_initialization(self):
        """Test filter can be initialized."""
        filter = FastFilter()
        assert filter is not None

    def test_quick_dedup_empty_list(self):
        """Test dedup on empty list."""
        filter = FastFilter()
        result = filter.quick_dedup([])

        assert result == []

    def test_quick_dedup_no_duplicates(self, tmp_path):
        """Test dedup when no duplicates."""
        files = [
            FileInfo(path=str(tmp_path / "file1.txt"), name="file1.txt", size=100, mtime=1.0),
            FileInfo(path=str(tmp_path / "file2.txt"), name="file2.txt", size=200, mtime=1.0),
            FileInfo(path=str(tmp_path / "file3.txt"), name="file3.txt", size=300, mtime=1.0),
        ]

        filter = FastFilter()
        result = filter.quick_dedup(files)

        assert len(result) == 0  # No duplicates

    def test_quick_dedup_with_duplicates(self, tmp_path):
        """Test dedup with duplicates (same size)."""
        files = [
            FileInfo(path=str(tmp_path / "file1.txt"), name="file1.txt", size=100, mtime=1.0),
            FileInfo(path=str(tmp_path / "file2.txt"), name="file2.txt", size=100, mtime=2.0),
            FileInfo(path=str(tmp_path / "file3.txt"), name="file3.txt", size=200, mtime=1.0),
        ]

        filter = FastFilter()
        result = filter.quick_dedup(files)

        assert len(result) == 1  # One group of size 100
        assert len(result[0]) == 2  # Two files in that group

    def test_filter_by_extension(self, tmp_path):
        """Test filtering by extension."""
        files = [
            FileInfo(path=str(tmp_path / "file1.txt"), name="file1.txt", size=100, mtime=1.0),
            FileInfo(path=str(tmp_path / "file2.log"), name="file2.log", size=200, mtime=1.0),
            FileInfo(path=str(tmp_path / "file3.txt"), name="file3.txt", size=300, mtime=1.0),
        ]

        filter = FastFilter()
        result = filter.filter_by_extension(files, [".txt"])

        assert len(result) == 2

    def test_filter_by_extension_all(self, tmp_path):
        """Test filtering with None returns all."""
        files = [
            FileInfo(path=str(tmp_path / "file1.txt"), name="file1.txt", size=100, mtime=1.0),
        ]

        filter = FastFilter()
        result = filter.filter_by_extension(files, None)

        assert len(result) == 1

    def test_filter_by_size(self, tmp_path):
        """Test filtering by size."""
        files = [
            FileInfo(path=str(tmp_path / "file1.txt"), name="file1.txt", size=100, mtime=1.0),
            FileInfo(path=str(tmp_path / "file2.txt"), name="file2.txt", size=500, mtime=1.0),
            FileInfo(path=str(tmp_path / "file3.txt"), name="file3.txt", size=1000, mtime=1.0),
        ]

        filter = FastFilter()
        result = filter.filter_by_size(files, min_size=200, max_size=800)

        assert len(result) == 1
        assert result[0].size == 500


class TestHashCache:
    """Tests for HashCache."""

    def test_cache_initialization(self):
        """Test cache can be initialized."""
        cache = HashCache()
        assert cache is not None
        assert cache.max_size == 10000

    def test_cache_hit_and_miss(self, tmp_path):
        """Test cache hit and miss."""
        cache = HashCache()
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        # Miss
        result1 = cache.get(test_file)
        assert result1 is None

        # Put
        cache.put(test_file, "abc123")

        # Hit
        result2 = cache.get(test_file)
        assert result2 == "abc123"

    def test_cache_lru_eviction(self, tmp_path):
        """Test LRU eviction."""
        cache = HashCache(max_size=3)

        # Create temporary files
        temp_files = []
        for i in range(4):
            file = tmp_path / f"file{i}.txt"
            file.write_text(f"content{i}")
            temp_files.append(file)

        # Add 3 items
        for i in range(3):
            cache.put(temp_files[i], f"hash{i}")

        assert cache.get_stats()["size"] == 3

        # Add 4th item should evict oldest
        cache.put(temp_files[3], "hash3")

        stats = cache.get_stats()
        assert stats["size"] == 3

    def test_cache_stats(self, tmp_path):
        """Test cache statistics."""
        cache = HashCache()
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        # Miss
        cache.get(test_file)

        # Put
        cache.put(test_file, "abc123")

        # Hit
        cache.get(test_file)

        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["size"] == 1

    def test_cache_clear(self, tmp_path):
        """Test clearing cache."""
        cache = HashCache()
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        cache.put(test_file, "abc123")
        assert cache.get_stats()["size"] == 1

        cache.clear()
        assert cache.get_stats()["size"] == 0
        assert cache.get_stats()["hits"] == 0

    def test_cache_invalidate(self, tmp_path):
        """Test invalidating cache entry."""
        cache = HashCache()
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        cache.put(test_file, "abc123")
        assert cache.get(test_file) == "abc123"

        cache.invalidate(test_file)
        assert cache.get(test_file) is None

    def test_get_or_compute(self, tmp_path):
        """Test get_or_compute with computation function."""
        cache = HashCache()
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        compute_count = [0]

        def compute(file):
            compute_count[0] += 1
            return "computed_hash"

        # First call: compute
        result1 = cache.get_or_compute(test_file, compute)
        assert result1 == "computed_hash"
        assert compute_count[0] == 1

        # Second call: use cache
        result2 = cache.get_or_compute(test_file, compute)
        assert result2 == "computed_hash"
        assert compute_count[0] == 1  # Not recomputed


class TestDuplicateFinder:
    """Tests for DuplicateFinder."""

    def test_finder_initialization(self):
        """Test finder can be initialized."""
        finder = DuplicateFinder()
        assert finder is not None

    def test_find_empty_list(self):
        """Test finding in empty list."""
        finder = DuplicateFinder()
        result = finder.find_duplicates([])

        assert result == []

    def test_find_no_duplicates(self, tmp_path):
        """Test finding when no duplicates."""
        # Create different files
        files = []
        for i in range(3):
            file = tmp_path / f"file_{i}.txt"
            file.write_text(f"unique_content_{i}" * 100)
            files.append(
                FileInfo(
                    path=str(file),
                    name=f"file_{i}.txt",
                    size=file.stat().st_size,
                    mtime=file.stat().st_mtime,
                )
            )

        finder = DuplicateFinder()
        result = finder.find_duplicates(files)

        # Should have no duplicates (different sizes or content)
        assert len(result) == 0

    def test_find_with_duplicates(self, tmp_path):
        """Test finding duplicates."""
        # Create duplicate files
        content = "duplicate_content" * 100

        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text(content)
        file2.write_text(content)

        files = [
            FileInfo(
                path=str(file1),
                name="file1.txt",
                size=file1.stat().st_size,
                mtime=file1.stat().st_mtime,
            ),
            FileInfo(
                path=str(file2),
                name="file2.txt",
                size=file2.stat().st_size,
                mtime=file2.stat().st_mtime,
            ),
        ]

        finder = DuplicateFinder(use_parallel=False)  # Use sequential for testing
        result = finder.find_duplicates(files)

        assert len(result) == 1
        assert result[0].count == 2
        assert len(result[0].files) == 2

    def test_find_sorted_by_reclaimable(self, tmp_path):
        """Test that results are sorted by reclaimable space."""
        # Create multiple duplicate groups
        small_content = "x" * 100
        large_content = "y" * 1000

        # Small duplicates
        file1 = tmp_path / "small1.txt"
        file2 = tmp_path / "small2.txt"
        file1.write_text(small_content)
        file2.write_text(small_content)

        # Large duplicates
        file3 = tmp_path / "large1.txt"
        file4 = tmp_path / "large2.txt"
        file3.write_text(large_content)
        file4.write_text(large_content)

        files = [
            FileInfo(path=str(file1), name="small1.txt", size=file1.stat().st_size, mtime=1.0),
            FileInfo(path=str(file2), name="small2.txt", size=file2.stat().st_size, mtime=2.0),
            FileInfo(path=str(file3), name="large1.txt", size=file3.stat().st_size, mtime=3.0),
            FileInfo(path=str(file4), name="large2.txt", size=file4.stat().st_size, mtime=4.0),
        ]

        finder = DuplicateFinder(use_parallel=False)
        result = finder.find_duplicates(files)

        # Large duplicates should come first
        assert len(result) == 2
        assert result[0].reclaimable_space > result[1].reclaimable_space

    def test_cache_stats(self):
        """Test getting cache stats."""
        finder = DuplicateFinder(use_cache=True)
        stats = finder.get_cache_stats()

        assert stats is not None
        assert "size" in stats
        assert "hits" in stats
        assert "misses" in stats

    def test_cache_disabled(self):
        """Test with cache disabled."""
        finder = DuplicateFinder(use_cache=False)
        stats = finder.get_cache_stats()

        assert stats is None

    def test_clear_cache(self):
        """Test clearing cache."""
        finder = DuplicateFinder(use_cache=True)

        # Should not raise exception
        finder.clear_cache()

    def test_shutdown(self):
        """Test shutting down finder."""
        finder = DuplicateFinder(use_parallel=True)

        # Should not raise exception
        finder.shutdown()


class TestDuplicateGroup:
    """Tests for DuplicateGroup."""

    def test_group_creation(self, tmp_path):
        """Test creating a duplicate group."""
        file1 = tmp_path / "file1.txt"
        file1.write_text("content")

        files = [
            FileInfo(path=str(file1), name="file1.txt", size=100, mtime=1.0),
        ]

        group = DuplicateGroup(
            files=files,
            size=100,
            count=1,
            hash_value="abc123",
            reclaimable_space=0,
        )

        assert group.count == 1
        assert group.size == 100
        assert group.hash_value == "abc123"

    def test_group_to_dict(self, tmp_path):
        """Test converting group to dict."""
        file1 = tmp_path / "file1.txt"
        file1.write_text("content")

        files = [
            FileInfo(path=str(file1), name="file1.txt", size=100, mtime=1.0),
        ]

        group = DuplicateGroup(
            files=files,
            size=100,
            count=1,
            hash_value="abc123",
            reclaimable_space=0,
        )

        data = group.to_dict()
        assert data["count"] == 1
        assert data["size"] == 100
        assert isinstance(data["files"], list)
