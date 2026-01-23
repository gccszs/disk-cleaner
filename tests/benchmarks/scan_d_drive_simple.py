"""
Full D drive scan with real-time progress.
"""

import sys
import time
from pathlib import Path

from diskcleaner.optimization.scan import ConcurrentScanner, QuickProfiler


def main():
    """Run full D drive scan with progress."""
    divider = "=" * 60

    print(divider)
    print("FULL D DRIVE SCAN TEST")
    print(divider)
    print(f"Target: D:\\")
    print(f"Starting: {time.strftime('%H:%M:%S')}")
    print(divider)

    # Quick profiling
    print("\n[1/2] Quick Profiling (1s)...")
    profiler = QuickProfiler(sample_time=1.0)
    profile = profiler.profile(Path("D:/"))
    print(f"  Estimated: {profile.file_count:,} files, {profile.total_size / 1024 / 1024 / 1024:.2f} GB")

    # Full scan
    print(f"\n[2/2] Full D:\\ Scan...")
    scanner = ConcurrentScanner()

    start_time = time.time()
    last_update = start_time

    def progress_callback(progress):
        """Show progress every 1 second."""
        nonlocal last_update
        now = time.time()
        count = progress.get('count', 0)
        errors = progress.get('errors', 0)

        if now - last_update >= 1.0:
            elapsed = now - start_time
            throughput = count / elapsed if elapsed > 0 else 0
            print(f"\r  Scanned: {count:,} files | {throughput:,.0f}/s | {elapsed:.1f}s | {errors} errors",
                  end='', flush=True)
            last_update = now

    start = time.time()
    result = scanner.scan(Path("D:/"), progress_callback=progress_callback)
    elapsed = time.time() - start

    # Clear line and show results
    print('\r' + ' ' * 100 + '\r', end='')

    print(f"\n\n{'='*60}")
    print("SCAN RESULTS")
    print(f"{'='*60}")
    print(f"  Files:     {result.total_count:,}")
    print(f"  Size:      {result.total_size / 1024 / 1024 / 1024:.2f} GB")
    print(f"  Dirs:      {sum(1 for item in result.items if item.is_dir):,}")
    print(f"  Errors:    {result.error_count}")
    print(f"  Time:      {elapsed:.3f}s")
    print(f"  Throughput:{result.total_count / elapsed:,.0f} files/s")

    # Target check
    if result.total_count >= 100000:
        status = "✅ PASS" if elapsed < 30 else "❌ FAIL"
        print(f"\n  Target (100K < 30s): {elapsed:.2f}s - {status}")

    # Estimation accuracy
    if profile.file_count > 0 and result.total_count > 0:
        accuracy = (profile.file_count / result.total_count) * 100
        print(f"  Estimation: {accuracy:.1f}% accurate")

    print(f"\n{'='*60}")
    print(f"Complete at: {time.strftime('%H:%M:%S')}")
    print(f"{'='*60}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Scan interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
