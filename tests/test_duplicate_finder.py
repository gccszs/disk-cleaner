"""
Tests for duplicate file finder.
"""

import tempfile
from pathlib import Path

from diskcleaner.core import DirectoryScanner, DuplicateFinder


def test_duplicate_finder_accurate_strategy():
    """Test duplicate finder with accurate strategy."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create duplicate files with same content
        (temp_path / "file1.txt").write_text("duplicate content")
        (temp_path / "file2.txt").write_text("duplicate content")
        (temp_path / "unique.txt").write_text("unique content")

        # Scan directory
        scanner = DirectoryScanner(str(temp_path))
        files = scanner.scan()

        # Find duplicates with accurate strategy
        finder = DuplicateFinder(strategy="accurate")
        duplicates = finder.find_duplicates(files)

        # Should find one duplicate group with 2 files
        assert len(duplicates) == 1
        assert duplicates[0].count == 2
        assert duplicates[0].reclaimable_space == len("duplicate content")
        print("Accurate strategy: PASS (found {} duplicate groups)".format(len(duplicates)))


def test_duplicate_finder_fast_strategy():
    """Test duplicate finder with fast strategy."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create duplicate files
        (temp_path / "file1.txt").write_text("x" * 1000)
        (temp_path / "file2.txt").write_text("x" * 1000)
        (temp_path / "file3.txt").write_text("y" * 1000)

        # Scan directory
        scanner = DirectoryScanner(str(temp_path))
        files = scanner.scan()

        # Find duplicates with fast strategy
        finder = DuplicateFinder(strategy="fast")
        duplicates = finder.find_duplicates(files)

        # Should find one duplicate group with 2 files
        assert len(duplicates) == 1
        assert duplicates[0].count == 2
        print("Fast strategy: PASS (found {} duplicate groups)".format(len(duplicates)))


def test_duplicate_finder_adaptive_strategy():
    """Test duplicate finder with adaptive strategy."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create a few duplicate files (below threshold)
        for i in range(3):
            (temp_path / f"dup{i}.txt").write_text("same content")

        (temp_path / "unique.txt").write_text("different")

        # Scan directory
        scanner = DirectoryScanner(str(temp_path))
        files = scanner.scan()

        # Find duplicates with adaptive strategy
        finder = DuplicateFinder(strategy="adaptive")
        duplicates = finder.find_duplicates(files)

        # Should use accurate strategy (file count < 1000)
        assert len(duplicates) == 1
        assert duplicates[0].count == 3
        print("Adaptive strategy (<1000 files): PASS")


def test_duplicate_finder_sorted_by_reclaimable():
    """Test that duplicates are sorted by reclaimable space."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create duplicate groups with different sizes
        (temp_path / "small1.txt").write_text("a")
        (temp_path / "small2.txt").write_text("a")

        (temp_path / "large1.txt").write_text("x" * 1000)
        (temp_path / "large2.txt").write_text("x" * 1000)
        (temp_path / "large3.txt").write_text("x" * 1000)

        # Scan directory
        scanner = DirectoryScanner(str(temp_path))
        files = scanner.scan()

        # Find duplicates
        finder = DuplicateFinder(strategy="accurate")
        duplicates = finder.find_duplicates(files)

        # Should return 2 groups, sorted by reclaimable space
        assert len(duplicates) == 2

        # First group should be the large one (more reclaimable space)
        assert duplicates[0].reclaimable_space > duplicates[1].reclaimable_space
        assert duplicates[0].count == 3  # large files
        assert duplicates[1].count == 2  # small files
        print("Sorting by reclaimable space: PASS")


def test_duplicate_finder_stats():
    """Test duplicate statistics calculation."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create duplicate files
        (temp_path / "file1.txt").write_text("x" * 100)
        (temp_path / "file2.txt").write_text("x" * 100)

        # Scan and find duplicates
        scanner = DirectoryScanner(str(temp_path))
        files = scanner.scan()

        finder = DuplicateFinder(strategy="accurate")
        duplicates = finder.find_duplicates(files)

        # Calculate stats
        stats = finder.get_duplicate_stats(duplicates)

        assert stats["group_count"] == 1
        assert stats["file_count"] == 2
        assert stats["total_size"] == 200  # 2 files * 100 bytes
        assert stats["reclaimable"] == 100  # 1 file * 100 bytes
        print("Duplicate stats: PASS ({})".format(stats))


def test_duplicate_finder_no_duplicates():
    """Test behavior when no duplicates exist."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create unique files
        (temp_path / "file1.txt").write_text("content1")
        (temp_path / "file2.txt").write_text("content2")
        (temp_path / "file3.txt").write_text("content3")

        # Scan and find duplicates
        scanner = DirectoryScanner(str(temp_path))
        files = scanner.scan()

        finder = DuplicateFinder(strategy="accurate")
        duplicates = finder.find_duplicates(files)

        # Should return empty list
        assert len(duplicates) == 0
        print("No duplicates: PASS")


def test_duplicate_finder_empty_directory():
    """Test behavior with empty directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Scan empty directory
        scanner = DirectoryScanner(temp_dir)
        files = scanner.scan()

        finder = DuplicateFinder(strategy="accurate")
        duplicates = finder.find_duplicates(files)

        # Should return empty list
        assert len(duplicates) == 0
        print("Empty directory: PASS")


if __name__ == "__main__":
    print("Running duplicate finder tests...\n")
    test_duplicate_finder_accurate_strategy()
    test_duplicate_finder_fast_strategy()
    test_duplicate_finder_adaptive_strategy()
    test_duplicate_finder_sorted_by_reclaimable()
    test_duplicate_finder_stats()
    test_duplicate_finder_no_duplicates()
    test_duplicate_finder_empty_directory()
    print("\nAll duplicate finder tests passed!")
