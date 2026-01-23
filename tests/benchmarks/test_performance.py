"""
Performance benchmark suite for disk-cleaner optimization.

Compares performance before and after optimizations.
"""

import json
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Dict, Optional

from diskcleaner.optimization.hash import (
    AdaptiveHasher,
    DuplicateFinder,
)
from diskcleaner.optimization.scan import (
    ConcurrentScanner,
    FileInfo,
)


class PerformanceBenchmark:
    """Performance benchmark suite."""

    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize benchmark suite.

        Args:
            output_dir: Directory to save results (None for temp)
        """
        self.output_dir = output_dir or Path("benchmark_results")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results: Dict[str, Dict] = {}

    def create_test_environment(
        self,
        base_dir: Path,
        small_files: int = 100,
        medium_files: int = 50,
        large_files: int = 10,
        nested_dirs: int = 5,
    ) -> Path:
        """
        Create test directory structure.

        Args:
            base_dir: Base directory for test files
            small_files: Number of small files (< 10KB)
            medium_files: Number of medium files (10KB-1MB)
            large_files: Number of large files (> 1MB)
            nested_dirs: Number of nested directory levels

        Returns:
            Path to created test directory
        """
        base_dir.mkdir(parents=True, exist_ok=True)

        # Create small files
        for i in range(small_files):
            file = base_dir / f"small_{i}.txt"
            file.write_text("x" * 1000)  # 1KB

        # Create medium files
        for i in range(medium_files):
            file = base_dir / f"medium_{i}.dat"
            file.write_bytes(b"x" * (100 * 1024))  # 100KB

        # Create large files
        for i in range(large_files):
            file = base_dir / f"large_{i}.bin"
            file.write_bytes(b"x" * (2 * 1024 * 1024))  # 2MB

        # Create nested directories
        for level in range(nested_dirs):
            level_dir = base_dir / f"level_{level}"
            level_dir.mkdir()
            for i in range(10):
                file = level_dir / f"nested_{i}.txt"
                file.write_text(f"level_{level}_file_{i}" * 100)

        return base_dir

    def benchmark_scan(self, test_dir: Path, name: str) -> Dict:
        """
        Benchmark scanning performance.

        Args:
            test_dir: Directory to scan
            name: Test name

        Returns:
            Benchmark results
        """
        print(f"\n{'='*60}")
        print(f"Scanning Benchmark: {name}")
        print(f"{'='*60}")

        # Concurrent scan
        scanner = ConcurrentScanner()
        start = time.time()
        result = scanner.scan(test_dir)
        elapsed = time.time() - start

        stats = {
            "test_name": name,
            "operation": "scan",
            "total_count": result.total_count,
            "total_size": result.total_size,
            "elapsed_time": elapsed,
            "throughput": result.total_count / elapsed if elapsed > 0 else 0,
        }

        print(f"Files scanned: {stats['total_count']}")
        print(f"Total size: {stats['total_size'] / 1024 / 1024:.2f} MB")
        print(f"Time: {stats['elapsed_time']:.3f} seconds")
        print(f"Throughput: {stats['throughput']:.0f} files/second")

        return stats

    def benchmark_hash(self, test_dir: Path, name: str) -> Dict:
        """
        Benchmark hash computation performance.

        Args:
            test_dir: Directory with files to hash
            name: Test name

        Returns:
            Benchmark results
        """
        print(f"\n{'='*60}")
        print(f"Hashing Benchmark: {name}")
        print(f"{'='*60}")

        # Collect files
        files = []
        for file in test_dir.rglob("*"):
            if file.is_file():
                files.append(
                    FileInfo(
                        path=str(file),
                        name=file.name,
                        size=file.stat().st_size,
                        mtime=file.stat().st_mtime,
                    )
                )

        if not files:
            return {"test_name": name, "operation": "hash", "error": "No files found"}

        # Adaptive hash
        hasher = AdaptiveHasher()
        start = time.time()
        hash_count = 0
        for file_info in files[:50]:  # Limit to 50 for speed
            hash_value = hasher.compute_hash(Path(file_info.path))
            if hash_value:
                hash_count += 1
        elapsed = time.time() - start

        stats = {
            "test_name": name,
            "operation": "hash_adaptive",
            "files_hashed": hash_count,
            "elapsed_time": elapsed,
            "avg_time_per_file": elapsed / hash_count if hash_count > 0 else 0,
        }

        print(f"Files hashed: {stats['files_hashed']}")
        print(f"Time: {stats['elapsed_time']:.3f} seconds")
        print(f"Avg time per file: {stats['avg_time_per_file']*1000:.2f} ms")

        return stats

    def benchmark_duplicate_detection(self, test_dir: Path, name: str) -> Dict:
        """
        Benchmark duplicate detection performance.

        Args:
            test_dir: Directory with files
            name: Test name

        Returns:
            Benchmark results
        """
        print(f"\n{'='*60}")
        print(f"Duplicate Detection Benchmark: {name}")
        print(f"{'='*60}")

        # Collect files
        files = []
        for file in test_dir.rglob("*"):
            if file.is_file():
                files.append(
                    FileInfo(
                        path=str(file),
                        name=file.name,
                        size=file.stat().st_size,
                        mtime=file.stat().st_mtime,
                    )
                )

        if len(files) < 2:
            return {"test_name": name, "operation": "duplicate", "error": "Not enough files"}

        finder = DuplicateFinder(use_parallel=False, use_cache=True)
        start = time.time()
        duplicates = finder.find_duplicates(files[:20])  # Limit for speed
        elapsed = time.time() - start

        stats = {
            "test_name": name,
            "operation": "duplicate_detection",
            "files_scanned": len(files[:20]),
            "duplicate_groups": len(duplicates),
            "elapsed_time": elapsed,
            "duplicates_found": sum(g.count for g in duplicates),
        }

        print(f"Files scanned: {stats['files_scanned']}")
        print(f"Duplicate groups: {stats['duplicate_groups']}")
        print(f"Time: {stats['elapsed_time']:.3f} seconds")

        return stats

    def run_all_benchmarks(self) -> Dict:
        """
        Run complete benchmark suite.

        Returns:
            All benchmark results
        """
        print("\n" + "=" * 60)
        print("PERFORMANCE BENCHMARK SUITE")
        print("=" * 60)

        with TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Test scenarios
            scenarios = [
                ("small", 100, 10, 2, 2),
                ("medium", 500, 50, 5, 3),
                ("large", 1000, 100, 10, 4),
            ]

            all_results = {}

            for name, small, medium, large, nested in scenarios:
                print(f"\n\n{'#'*60}")
                print(f"# Scenario: {name.upper()}")
                print(f"{'#'*60}")

                # Create test environment
                test_dir = tmpdir / name
                self.create_test_environment(
                    test_dir,
                    small_files=small,
                    medium_files=medium,
                    large_files=large,
                    nested_dirs=nested,
                )

                # Run benchmarks
                scenario_results = {}

                # Scan benchmark
                scan_result = self.benchmark_scan(test_dir, f"{name}_scan")
                scenario_results["scan"] = scan_result

                # Hash benchmark
                hash_result = self.benchmark_hash(test_dir, f"{name}_hash")
                scenario_results["hash"] = hash_result

                # Duplicate detection benchmark
                dup_result = self.benchmark_duplicate_detection(test_dir, f"{name}_dup")
                scenario_results["duplicate"] = dup_result

                all_results[name] = scenario_results

        # Save results
        self.save_results(all_results)

        return all_results

    def save_results(self, results: Dict) -> None:
        """
        Save benchmark results to file.

        Args:
            results: Benchmark results
        """
        output_file = self.output_dir / f"benchmark_{int(time.time())}.json"

        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)

        print(f"\n\nResults saved to: {output_file}")

    def print_summary(self, results: Dict) -> None:
        """
        Print benchmark summary.

        Args:
            results: Benchmark results
        """
        print("\n\n" + "=" * 60)
        print("BENCHMARK SUMMARY")
        print("=" * 60)

        for scenario_name, scenario in results.items():
            print(f"\n{scenario_name.upper()}:")

            if "scan" in scenario:
                scan = scenario["scan"]
                print(f"  Scan: {scan['throughput']:.0f} files/sec")

            if "hash" in scenario:
                hash_result = scenario["hash"]
                if "avg_time_per_file" in hash_result:
                    print(f"  Hash: {hash_result['avg_time_per_file']*1000:.2f} ms/file")

            if "duplicate" in scenario:
                dup = scenario["duplicate"]
                if "elapsed_time" in dup:
                    print(
                        f"  Duplicate: {dup['elapsed_time']:.3f}s for {dup.get('files_scanned', 0)} files"
                    )

        print("\n" + "=" * 60)


def main():
    """Run benchmark suite."""
    benchmark = PerformanceBenchmark()

    # Run benchmarks
    results = benchmark.run_all_benchmarks()

    # Print summary
    benchmark.print_summary(results)

    print("\n[Benchmarks complete!]")


if __name__ == "__main__":
    main()
