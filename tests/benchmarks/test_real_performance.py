"""
Real-world performance test on D drive.

Tests actual performance on real directories with thousands of files.
"""

import json
from datetime import datetime
from pathlib import Path

from diskcleaner.optimization.profiler import PerformanceProfiler
from diskcleaner.optimization.scan import ConcurrentScanner, QuickProfiler


def scan_real_directory(path: Path, name: str) -> dict:
    """
    Scan a real directory and return performance metrics.

    Args:
        path: Directory to scan
        name: Test name

    Returns:
        Performance results
    """
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"Path: {path}")
    print(f"{'='*60}")

    if not path.exists():
        print(f"❌ Path does not exist: {path}")
        return {"error": "Path does not exist", "name": name}

    # Quick profiling first
    print("\n[1/2] Quick Profiling (0.5s sampling)...")
    profiler = QuickProfiler(sample_time=0.5)
    profile = profiler.profile(path)

    print(f"  Estimated files: {profile.file_count:,}")
    print(f"  Estimated size: {profile.total_size / 1024 / 1024:.2f} MB")
    print(f"  Estimated depth: {profile.max_depth}")
    print(f"  Estimated time: {profile.estimated_time:.2f}s")

    # Actual scan
    print("\n[2/2] Full Scan...")
    scanner = ConcurrentScanner()
    profiler_perf = PerformanceProfiler()

    with profiler_perf.profile("scan"):
        result = scanner.scan(path)

    scan_time = profiler_perf.get_operation_time("scan")
    throughput = result.total_count / scan_time if scan_time > 0 else 0

    print(f"\n  Files scanned: {result.total_count:,}")
    print(f"  Total size: {result.total_size / 1024 / 1024:.2f} MB")
    print(f"  Directories: {sum(1 for item in result.items if item.is_dir)}")
    print(f"  Errors: {result.error_count}")
    print(f"  Time: {scan_time:.3f} seconds")
    print(f"  Throughput: {throughput:,.0f} files/second")

    return {
        "name": name,
        "path": str(path),
        "file_count": result.total_count,
        "total_size_mb": result.total_size / 1024 / 1024,
        "scan_time": scan_time,
        "throughput": throughput,
        "error_count": result.error_count,
        "estimated_count": profile.file_count,
        "estimated_time": profile.estimated_time,
        "estimation_accuracy": (
            profile.file_count / result.total_count if result.total_count > 0 else 0
        ),
    }


def main():
    """Run real-world performance tests on D drive."""

    print("=" * 60)
    print("REAL-WORLD PERFORMANCE TEST - D DRIVE")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Platform: {os.name}")
    print()

    # Test directories on D drive
    test_paths = [
        # Adjust these paths to match your actual D drive structure
        ("D:\\", "D Root (limited)"),
        ("D:\\Projects", "Projects Folder"),
        ("D:\\other_pj", "Other Projects"),
        # Add more paths as needed
    ]

    results = []
    for path_str, name in test_paths:
        path = Path(path_str)
        try:
            result = scan_real_directory(path, name)
            if "error" not in result:
                results.append(result)
        except Exception as e:
            print(f"\n❌ Error scanning {path_str}: {e}")

    # Summary
    print("\n\n" + "=" * 60)
    print("PERFORMANCE SUMMARY")
    print("=" * 60)

    if results:
        total_files = sum(r["file_count"] for r in results)
        total_time = sum(r["scan_time"] for r in results)
        avg_throughput = total_files / total_time if total_time > 0 else 0

        print("\nTotal Statistics:")
        print(f"  Total files scanned: {total_files:,}")
        print(f"  Total time: {total_time:.3f} seconds")
        print(f"  Average throughput: {avg_throughput:,.0f} files/second")

        print("\nIndividual Results:")
        header = f"{'Name':<30} {'Files':>10} {'Time (s)':>10} {'Throughput':>15}"
        print(header)
        print("-" * 65)
        for r in results:
            line = (
                f"{r['name']:<30} {r['file_count']:>10,} "
                f"{r['scan_time']:>10.3f} {r['throughput']:>15,.0f}"
            )
            print(line)

        # Find performance targets
        print("\nPerformance vs Targets:")
        for r in results:
            if r["file_count"] >= 10000:
                target_met = r["scan_time"] < 30
                status = "✅ PASS" if target_met else "❌ FAIL"
                print(f"  {r['name']}: {r['scan_time']:.2f}s vs 30s target {status}")

        # Save results
        output_file = (
            Path("benchmark_results")
            / f"d_drive_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)

        print(f"\nResults saved to: {output_file}")

    else:
        print("\nNo successful tests to report.")

    print("\n[Test complete]")


if __name__ == "__main__":
    import os

    main()
