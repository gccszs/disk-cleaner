"""
Full D drive scan test.

Scans the entire D drive and measures performance.
"""

import time
from pathlib import Path

from diskcleaner.optimization.scan import ConcurrentScanner, QuickProfiler
from diskcleaner.optimization.profiler import PerformanceProfiler


def main():
    """Run full D drive scan."""
    divider = "=" * 60

    print(divider)
    print("FULL D DRIVE SCAN TEST")
    print(divider)
    print(f"Target: D:\\")
    print(f"Starting at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(divider)

    # Phase 1: Quick profiling
    print("\n[1/2] Quick Profiling (1s sampling)...")
    profiler = QuickProfiler(sample_time=1.0)
    profile = profiler.profile(Path("D:/"))
    print(f"Estimated files: {profile.file_count:,}")
    print(f"Estimated size: {profile.total_size / 1024 / 1024 / 1024:.2f} GB")
    print(f"Estimated depth: {profile.max_depth}")

    # Phase 2: Full scan
    print(f"\n[2/2] Full Scan...")
    scanner = ConcurrentScanner()

    progress_data = {"count": 0, "start": time.time()}

    def progress_callback(progress):
        """Display progress."""
        count = progress.get("count", 0)
        errors = progress.get("errors", 0)
        elapsed = time.time() - progress_data["start"]

        if elapsed > 1.0:  # Show after 1 second
            throughput = count / elapsed
            print(f"\r  Progress: {count:,} files | {throughput:,.0f} files/s | {elapsed:.1f}s | {errors} errors",
                  end="", flush=True)

    start = time.time()
    result = scanner.scan(Path("D:/"), progress_callback=progress_callback)
    elapsed = time.time() - start

    print(f"\n\n✅ Scan Complete!")
    print(f"  Files scanned: {result.total_count:,}")
    print(f"  Total size: {result.total_size / 1024 / 1024 / 1024:.2f} GB")
    print(f"  Directories: {sum(1 for item in result.items if item.is_dir):,}")
    print(f"  Errors: {result.error_count}")
    print(f"  Time: {elapsed:.3f} seconds")
    print(f"  Throughput: {result.total_count / elapsed:,.0f} files/second")

    # Check targets
    print(f"\n📊 Performance vs Targets:")
    if result.total_count >= 100000:
        target_met = elapsed < 30
        status = "✅ PASS" if target_met else "❌ FAIL"
        print(f"  100K files < 30s: {elapsed:.2f}s - {status}")
    elif result.total_count >= 50000:
        target_met = elapsed < 15
        status = "✅ PASS" if target_met else "❌ FAIL"
        print(f"  50K files < 15s: {elapsed:.2f}s - {status}")

    # Estimation accuracy
    if profile.file_count > 0:
        accuracy = profile.file_count / result.total_count * 100
        print(f"\n📈 Estimation accuracy: {accuracy:.1f}%")

    print(f"\n{divider}")
    print("Test Complete!")
    print(divider)


if __name__ == "__main__":
    main()
