"""
Strategic D drive scan - test largest directories only.

Based on analysis, scan the top 10 largest directories to validate performance.
"""

import sys
import time
from pathlib import Path

from diskcleaner.optimization.scan import ConcurrentScanner, QuickProfiler


def get_top_directories(d_path: Path, top_n: int = 10) -> list:
    """Get top N directories by estimated file count."""
    print(f"Analyzing D:\\ structure...")

    profiler = QuickProfiler(sample_time=0.5)
    profile = profiler.profile(d_path)

    # Get subdirectories
    try:
        subdirs = [d for d in d_path.iterdir() if d.is_dir() and not d.is_symlink()]
    except PermissionError:
        subdirs = []

    # Quick profile each and sort
    dir_stats = []
    for subdir in subdirs:
        try:
            sub_profile = profiler.profile(subdir)
            if sub_profile.file_count > 100:  # Only include dirs with >100 files
                dir_stats.append({
                    'path': subdir,
                    'name': subdir.name,
                    'files': sub_profile.file_count,
                    'size': sub_profile.total_size,
                })
        except (PermissionError, Exception):
            pass

    # Sort by file count
    dir_stats.sort(key=lambda x: x['files'], reverse=True)
    return dir_stats[:top_n]


def main():
    """Run strategic scan of top directories."""
    divider = "=" * 60

    print(divider)
    print("STRATEGIC D DRIVE SCAN - Top Directories")
    print(divider)
    print(f"Starting: {time.strftime('%H:%M:%S')}")
    print(divider)

    # Get top directories
    top_dirs = get_top_directories(Path("D:/"), top_n=10)

    if not top_dirs:
        print("❌ No directories found to scan")
        return

    print(f"\nSelected {len(top_dirs)} largest directories:")
    total_estimated = 0
    for i, d in enumerate(top_dirs, 1):
        total_estimated += d['files']
        print(f"  {i}. {d['name']:<30} ~{d['files']:7,} files | {d['size'] / 1024 / 1024:7.2f} MB")

    print(f"\nEstimated total: {total_estimated:,} files")

    # Scan each directory
    print(f"\n{'='*60}")
    print("Scanning directories...")
    print(f"{'='*60}")

    scanner = ConcurrentScanner()
    all_results = []

    for i, dir_info in enumerate(top_dirs, 1):
        path = dir_info['path']
        name = dir_info['name']

        print(f"\n[{i}/{len(top_dirs)}] {name}")

        start = time.time()
        result = scanner.scan(path)
        elapsed = time.time() - start

        throughput = result.total_count / elapsed if elapsed > 0 else 0

        print(f"  Files: {result.total_count:,}")
        print(f"  Time: {elapsed:.3f}s")
        print(f"  Speed: {throughput:,.0f} files/s")
        print(f"  Errors: {result.error_count}")

        all_results.append({
            'name': name,
            'files': result.total_count,
            'time': elapsed,
            'throughput': throughput,
            'errors': result.error_count,
        })

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")

    total_files = sum(r['files'] for r in all_results)
    total_time = sum(r['time'] for r in all_results)
    avg_throughput = total_files / total_time if total_time > 0 else 0

    print(f"Directories scanned: {len(all_results)}")
    print(f"Total files: {total_files:,}")
    print(f"Total time: {total_time:.3f}s")
    print(f"Average throughput: {avg_throughput:,.0f} files/s")

    # Check target
    if total_files >= 400000:
        status = "✅ PASS" if total_time < 30 else "❌ FAIL"
        print(f"\nTarget (400K < 30s): {total_time:.2f}s - {status}")
    elif total_files >= 100000:
        status = "✅ PASS" if total_time < 15 else "❌ FAIL"
        print(f"\nTarget (100K < 15s): {total_time:.2f}s - {status}")

    print(f"\n{'='*60}")
    print(f"Complete: {time.strftime('%H:%M:%S')}")
    print(f"{'='*60}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
