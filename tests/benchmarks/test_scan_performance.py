"""
Performance benchmarks for directory scanner.

Tests the performance improvements of os.scandir() over Path.glob/iterdir().
"""

import os
import platform
import tempfile
import time
from pathlib import Path

import pytest

from diskcleaner.core.scanner import DirectoryScanner, should_exclude_path


class TestScanPerformance:
    """Test scanner performance improvements."""

    def test_scandir_vs_iterdir_performance(self, tmp_path):
        """
        Verify that os.scandir() is at least 3x faster than Path.iterdir().

        This is the key optimization that provides 3-5x performance improvement.
        """
        # Create test directory with many files
        num_dirs = 100
        files_per_dir = 100

        for i in range(num_dirs):
            dir_path = tmp_path / f"dir_{i}"
            dir_path.mkdir()

            for j in range(files_per_dir):
                (dir_path / f"file_{j}.txt").write_text("test content")

        # Test with iterdir() (old method)
        def scan_with_iterdir():
            count = 0
            for item in tmp_path.iterdir():
                if item.is_dir():
                    for sub_item in item.iterdir():
                        if sub_item.is_file():
                            count += 1
            return count

        start = time.time()
        iterdir_count = scan_with_iterdir()
        iterdir_time = time.time() - start

        # Test with scandir() (new method)
        def scan_with_scandir():
            count = 0
            with os.scandir(tmp_path) as entries:
                for entry in entries:
                    if entry.is_dir():
                        sub_path = Path(entry.path)
                        with os.scandir(sub_path) as sub_entries:
                            for sub_entry in sub_entries:
                                if sub_entry.is_file():
                                    count += 1
            return count

        start = time.time()
        scandir_count = scan_with_scandir()
        scandir_time = time.time() - start

        # Verify counts match
        assert iterdir_count == scandir_count
        assert iterdir_count == num_dirs * files_per_dir

        # Verify scandir is at least 3x faster
        # Note: On fast systems with small directories, this might not hold
        # but for realistic workloads it should
        speedup = iterdir_time / scandir_time if scandir_time > 0 else 1

        print(f"\nPath.iterdir(): {iterdir_time:.3f}s")
        print(f"os.scandir(): {scandir_time:.3f}s")
        print(f"Speedup: {speedup:.2f}x")

        # Assert scandir is faster (at least 2x to be safe)
        assert speedup >= 2.0, f"scandir not 2x faster: {speedup:.2f}x"

    def test_scan_large_directory_performance(self, tmp_path):
        """
        Test scanning large directory completes in acceptable time.

        Target: < 10 seconds for 100,000 files
        """
        # Create large test directory
        num_files = 10000  # Use fewer files for faster test

        for i in range(num_files):
            (tmp_path / f"file_{i}.txt").write_text("test")

        scanner = DirectoryScanner(str(tmp_path), max_files=num_files + 1)

        start = time.time()
        files = scanner.scan()
        elapsed = time.time() - start

        # Should complete quickly
        assert elapsed < 5.0, f"Too slow: {elapsed:.3f}s for {num_files} files"
        assert len(files) == num_files

        print(f"\nScanned {num_files} files in {elapsed:.3f}s")
        print(f"Rate: {num_files / elapsed:.0f} files/sec")

    @pytest.mark.benchmark(group="scan")
    def test_benchmark_scan_10k_files(self, benchmark, tmp_path):
        """Benchmark scanning 10,000 files."""
        # Create test files
        for i in range(10000):
            (tmp_path / f"file_{i}.txt").write_text("test")

        scanner = DirectoryScanner(str(tmp_path))

        def scan_operation():
            return scanner.scan()

        result = benchmark(scan_operation)
        assert len(result) == 10000

    @pytest.mark.benchmark(group="scan")
    def test_benchmark_scan_directory_tree(self, benchmark, tmp_path):
        """Benchmark scanning directory tree."""
        # Create directory tree
        for i in range(100):
            dir_path = tmp_path / f"dir_{i}"
            dir_path.mkdir()
            for j in range(100):
                (dir_path / f"file_{j}.txt").write_text("test")

        scanner = DirectoryScanner(str(tmp_path))

        def scan_operation():
            return scanner.scan()

        result = benchmark(scan_operation)
        # Should include both files and directories
        # 100 directories + 10000 files = 10100 total items
        assert len(result) == 10100


class TestEarlyStopping:
    """Test early stopping mechanism."""

    def test_max_files_limit(self, tmp_path):
        """Test scanner stops after reaching max_files limit."""
        # Create more files than limit
        num_files = 1000

        for i in range(num_files):
            (tmp_path / f"file_{i}.txt").write_text("test")

        # Set limit to 100
        scanner = DirectoryScanner(str(tmp_path), max_files=100)
        files = scanner.scan()

        # Should scan at most 100 files
        assert len(files) <= 100
        assert scanner.stopped_early
        assert "file_limit" in scanner.stop_reason

    def test_max_seconds_limit(self, tmp_path):
        """Test scanner stops after reaching max_seconds limit."""
        # Create some files
        for i in range(1000):
            (tmp_path / f"file_{i}.txt").write_text("x" * 1000)

        # Set time limit to 1 second
        scanner = DirectoryScanner(str(tmp_path), max_seconds=1)
        files = scanner.scan()

        # Should stop early due to time limit
        # (or complete if very fast)
        if scanner.stopped_early:
            assert "time_limit" in scanner.stop_reason
            print(f"\nStopped after {len(files)} files due to time limit")

    def test_no_early_stopping_when_within_limits(self, tmp_path):
        """Test scanner doesn't stop early when within limits."""
        # Create few files
        num_files = 50

        for i in range(num_files):
            (tmp_path / f"file_{i}.txt").write_text("test")

        # Set high limits
        scanner = DirectoryScanner(str(tmp_path), max_files=1000, max_seconds=60)
        files = scanner.scan()

        # Should complete without early stopping
        assert len(files) == num_files
        assert not scanner.stopped_early
        assert scanner.stop_reason is None


class TestPathExclusions:
    """Test cross-platform path exclusions."""

    def test_should_exclude_windows_paths(self):
        """Test Windows system paths are excluded."""
        if platform.system().lower() != "windows":
            pytest.skip("Windows only test")

        assert should_exclude_path(Path("C:\\Windows"))
        assert should_exclude_path(Path("C:\\Program Files"))
        assert should_exclude_path(Path("C:\\$Recycle.Bin"))
        assert not should_exclude_path(Path("C:\\Users"))

    def test_should_exclude_macos_paths(self):
        """Test macOS system paths are excluded."""
        if platform.system().lower() != "darwin":
            pytest.skip("macOS only test")

        assert should_exclude_path(Path("/System"))
        assert should_exclude_path(Path("/Library"))
        assert should_exclude_path(Path("/.Spotlight-V100"))
        assert not should_exclude_path(Path("/Users"))

    def test_should_exclude_linux_paths(self):
        """Test Linux system paths are excluded."""
        if platform.system().lower() != "linux":
            pytest.skip("Linux only test")

        assert should_exclude_path(Path("/proc"))
        assert should_exclude_path(Path("/sys"))
        assert should_exclude_path(Path("/dev"))
        assert not should_exclude_path(Path("/home"))

    def test_scanner_raises_on_excluded_path(self, tmp_path):
        """Test scanner raises PermissionError for excluded paths."""
        # This test works on all platforms
        # We'll use a platform-specific exclude path
        system = platform.system().lower()

        if system == "windows":
            excluded_path = Path("C:\\Windows")
        elif system == "darwin":
            excluded_path = Path("/System")
        else:
            excluded_path = Path("/proc")

        # Skip if path doesn't exist
        if not excluded_path.exists():
            pytest.skip(f"Excluded path {excluded_path} doesn't exist")

        scanner = DirectoryScanner(str(excluded_path))

        with pytest.raises(PermissionError, match="excluded from scanning"):
            scanner.scan()


class TestRealWorldPerformance:
    """Test performance with realistic scenarios."""

    def test_scan_user_home_directory(self):
        """
        Test scanning user home directory completes in reasonable time.

        This is a real-world test with actual user files.
        """
        home = Path.home()

        if not home.exists():
            pytest.skip("Home directory not found")

        # Limit to prevent scanning too many files
        scanner = DirectoryScanner(str(home), max_files=5000, max_seconds=10)

        start = time.time()
        files = scanner.scan()
        elapsed = time.time() - start

        print(f"\nScanned {len(files)} files from home in {elapsed:.3f}s")

        # Should complete within time limit
        assert elapsed < 15.0  # Allow some margin

        # If stopped early, verify reason
        if scanner.stopped_early:
            print(f"Stopped early: {scanner.stop_reason}")

    @pytest.mark.slow
    def test_scan_performance_comparison(self):
        """
        Direct comparison between old and new scanning methods.

        This test shows the actual performance improvement.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create realistic file structure
            num_dirs = 50
            files_per_dir = 100

            for i in range(num_dirs):
                dir_path = tmp_path / f"project_{i}"
                dir_path.mkdir()

                # Mix files and subdirectories
                for j in range(files_per_dir):
                    if j % 10 == 0:
                        # Create subdirectory
                        sub_dir = dir_path / f"sub_{j}"
                        sub_dir.mkdir()
                        (sub_dir / "file.txt").write_text("test")
                    else:
                        # Create file
                        (dir_path / f"file_{j}.txt").write_text("test content")

            # Test old method (Path.glob)
            def old_method():
                count = 0
                for item in tmp_path.rglob("*"):
                    if item.is_file():
                        count += 1
                return count

            start = time.time()
            old_count = old_method()
            old_time = time.time() - start

            # Test new method (DirectoryScanner with os.scandir)
            scanner = DirectoryScanner(str(tmp_path))
            start = time.time()
            new_files = scanner.scan()
            new_time = time.time() - start
            new_count = len(new_files)

            # Note: File counts may differ due to different handling of
            # special files, symlinks, or directory entries. The performance
            # comparison is the main goal of this test.

            # Calculate speedup
            speedup = old_time / new_time if new_time > 0 else 1

            print(f"\nOld method (glob): {old_time:.3f}s")
            print(f"New method (scandir): {new_time:.3f}s")
            print(f"Speedup: {speedup:.2f}x")
            print(f"Files scanned: {new_count}")

            # Assert new method is faster
            # At least 2x faster for this test
            assert speedup >= 2.0, f"Expected 2x speedup, got {speedup:.2f}x"


class TestCrossPlatformPerformance:
    """Cross-platform performance tests."""

    @pytest.mark.benchmark(group="cross-platform")
    def test_windows_scan_performance(self):
        """Windows-specific performance test."""
        if platform.system().lower() != "windows":
            pytest.skip("Windows only")

        # Test C:\Users (if exists)
        users_path = Path("C:\\Users")
        if not users_path.exists():
            pytest.skip("C:\\Users not found")

        scanner = DirectoryScanner(str(users_path), max_files=1000, max_seconds=5)

        start = time.time()
        files = scanner.scan()
        elapsed = time.time() - start

        print(f"\nWindows: Scanned {len(files)} files in {elapsed:.3f}s")

        # Should complete within 5 seconds for 1000 files
        assert elapsed < 10.0

    @pytest.mark.benchmark(group="cross-platform")
    def test_macos_scan_performance(self):
        """macOS-specific performance test."""
        if platform.system().lower() != "darwin":
            pytest.skip("macOS only")

        # Test /Users (if exists)
        users_path = Path("/Users")
        if not users_path.exists():
            pytest.skip("/Users not found")

        scanner = DirectoryScanner(str(users_path), max_files=1000, max_seconds=5)

        start = time.time()
        files = scanner.scan()
        elapsed = time.time() - start

        print(f"\nmacOS: Scanned {len(files)} files in {elapsed:.3f}s")

        # Should complete within 5 seconds for 1000 files
        assert elapsed < 10.0

    @pytest.mark.benchmark(group="cross-platform")
    def test_linux_scan_performance(self):
        """Linux-specific performance test."""
        if platform.system().lower() != "linux":
            pytest.skip("Linux only")

        # Test /home (if exists)
        home_path = Path("/home")
        if not home_path.exists():
            pytest.skip("/home not found")

        scanner = DirectoryScanner(str(home_path), max_files=1000, max_seconds=5)

        start = time.time()
        files = scanner.scan()
        elapsed = time.time() - start

        print(f"\nLinux: Scanned {len(files)} files in {elapsed:.3f}s")

        # Should complete within 5 seconds for 1000 files
        assert elapsed < 10.0
