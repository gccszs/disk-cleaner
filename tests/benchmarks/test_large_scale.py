"""
Large-scale performance test with intelligent sampling.

Tests real-world scenarios with emoji-enhanced terminal UI and graceful fallback.
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from diskcleaner.optimization.profiler import PerformanceProfiler
from diskcleaner.optimization.scan import ConcurrentScanner, QuickProfiler


class SafeTerminal:
    """Safe terminal output with encoding detection and emoji fallback."""

    def __init__(self):
        """Detect terminal encoding capabilities."""
        self.encoding = sys.stdout.encoding or "utf-8"
        self.supports_emoji = self._check_emoji_support()

    def _check_emoji_support(self) -> bool:
        """Check if terminal supports emoji."""
        try:
            # Try to print emoji
            test_emoji = "✅"
            test_emoji.encode(self.encoding)
            return True
        except (UnicodeEncodeError, LookupError):
            return False

    def print(self, text: str):
        """Safe print with encoding fallback."""
        try:
            print(text)
        except UnicodeEncodeError:
            # Fallback to ASCII
            ascii_text = text.encode("ascii", "ignore").decode("ascii")
            print(ascii_text)

    def emoji(self, emoji_text: str, ascii_fallback: str) -> str:
        """Get appropriate symbol based on terminal support."""
        return emoji_text if self.supports_emoji else ascii_fallback


class LargeScalePerformanceTest:
    """Large-scale real-world performance testing with intelligent sampling."""

    def __init__(self, output_dir: Optional[Path] = None):
        """Initialize test suite.

        Args:
            output_dir: Directory to save detailed results (None for temp)
        """
        self.terminal = SafeTerminal()
        self.output_dir = output_dir or Path("benchmark_results")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[Dict] = []
        self.start_time = time.time()

    def analyze_d_drive_structure(self, d_path: Path) -> List[Dict]:
        """Phase 1: Quick analysis of D drive structure.

        Args:
            d_path: D drive path

        Returns:
            List of directory info dicts
        """
        check = self.terminal.emoji("✓", "[OK]")
        search = self.terminal.emoji("🔍", "[SCAN]")
        divider = "=" * 60

        self.terminal.print(f"\n{divider}")
        self.terminal.print(f"{search} Phase 1: Analyzing D Drive Structure")
        self.terminal.print(divider)

        # Quick profiling
        self.terminal.print("\nRunning quick profiling (1s sampling)...")
        profiler = QuickProfiler(sample_time=1.0)
        profile = profiler.profile(d_path)

        self.terminal.print(f"{check} Estimated files: {profile.file_count:,}")
        self.terminal.print(
            f"{check} Estimated size: {profile.total_size / 1024 / 1024 / 1024:.2f} GB"
        )
        self.terminal.print(f"{check} Estimated depth: {profile.max_depth}")

        # Get top-level directories
        try:
            subdirs = [d for d in d_path.iterdir() if d.is_dir() and not d.is_symlink()]
        except PermissionError:
            self.terminal.print("⚠️ Permission denied for some directories")
            subdirs = []

        # Analyze each subdirectory
        dir_infos = []
        for subdir in sorted(subdirs):
            try:
                # Quick profile each subdir
                sub_profile = profiler.profile(subdir)

                dir_info = {
                    "path": str(subdir),
                    "name": subdir.name,
                    "estimated_files": sub_profile.file_count,
                    "estimated_size": sub_profile.total_size,
                    "is_system": subdir.name.lower()
                    in [
                        "$recycle",
                        "system volume information",
                        "system32",
                        "windows",
                        "program files",
                    ],
                }
                dir_infos.append(dir_info)

                # Print summary
                size_mb = sub_profile.total_size / 1024 / 1024
                self.terminal.print(
                    f"  {check} {subdir.name:<30} "
                    f"~{sub_profile.file_count:6,} files | {size_mb:8.2f} MB"
                )

            except (PermissionError, Exception) as e:
                # Graceful fallback - skip problematic directories
                dir_info = {
                    "path": str(subdir),
                    "name": subdir.name,
                    "estimated_files": 0,
                    "estimated_size": 0,
                    "error": str(e),
                }
                dir_infos.append(dir_info)
                self.terminal.print(f"  ⚠️ {subdir.name:<30} (skipped: {type(e).__name__})")

        return dir_infos

    def select_representative_directories(self, dir_infos: List[Dict]) -> List[Dict]:
        """Phase 2: Select representative directories for testing.

        Args:
            dir_infos: List of directory info dicts

        Returns:
            Selected directories for testing
        """
        rocket = self.terminal.emoji("🚀", "[SEL]")
        divider = "=" * 60

        self.terminal.print(f"\n{divider}")
        self.terminal.print(f"{rocket} Phase 2: Selecting Test Directories")
        self.terminal.print(divider)

        # Filter out system directories
        user_dirs = [d for d in dir_infos if not d.get("is_system", False)]

        # Sort by estimated file count
        user_dirs.sort(key=lambda x: x.get("estimated_files", 0), reverse=True)

        # Categorize by size
        small = [d for d in user_dirs if d.get("estimated_files", 0) < 1000]
        medium = [d for d in user_dirs if 1000 <= d.get("estimated_files", 0) < 10000]
        large = [d for d in user_dirs if d.get("estimated_files", 0) >= 10000]

        # Select representatives (up to 3 from each category)
        selected = []

        if large:
            selected.extend(large[: min(3, len(large))])
        if medium:
            selected.extend(medium[: min(3, len(medium))])
        if small:
            selected.extend(small[: min(2, len(small))])

        self.terminal.print(f"\nSelected {len(selected)} directories for testing:")
        large_count = len([d for d in selected if d.get("estimated_files", 0) >= 10000])
        medium_count = len([d for d in selected if 1000 <= d.get("estimated_files", 0) < 10000])
        small_count = len([d for d in selected if d.get("estimated_files", 0) < 1000])
        self.terminal.print(f"  Large dirs (≥10K): {large_count}")
        self.terminal.print(f"  Medium dirs (1K-10K): {medium_count}")
        self.terminal.print(f"  Small dirs (<1K): {small_count}")

        return selected

    def test_directory(self, dir_info: Dict, index: int, total: int) -> Optional[Dict]:
        """Test a single directory with real-time progress.

        Args:
            dir_info: Directory info dict
            index: Current test index
            total: Total number of tests

        Returns:
            Test result dict or None if failed
        """
        path = Path(dir_info["path"])
        name = dir_info["name"]
        search = self.terminal.emoji("🔍", "[TEST]")

        self.terminal.print(f"\n[{index}/{total}] {search} Testing: {name}")

        try:
            # Create progress callback
            progress_data = {"files_scanned": 0, "start_time": time.time()}

            def progress_callback(progress):
                """Real-time progress update."""
                # progress is a dict with keys: count, errors, size
                files_scanned = progress.get("count", 0)
                errors = progress.get("errors", 0)
                progress_data["files_scanned"] = files_scanned
                elapsed = time.time() - progress_data["start_time"]

                if elapsed > 0.5:  # Only show after 0.5s to avoid flicker
                    throughput = files_scanned / elapsed
                    # Can't show percentage without total estimate
                    bar_length = min(20, int((elapsed % 5) / 5 * 20))  # Animated bar based on time

                    bar = self.terminal.emoji("█", "=") * bar_length
                    bar += self.terminal.emoji("░", "-") * (20 - bar_length)

                    stats = (
                        f"\r     {bar} | "
                        f"📊 {files_scanned:,} files | "
                        f"⚡ {throughput:,.0f}/s | "
                        f"⏱️ {elapsed:.2f}s | "
                        f"❌ {errors}"
                    )

                    try:
                        print(stats, end="", flush=True)
                    except UnicodeEncodeError:
                        # Fallback to simple progress
                        print(
                            f"\r     Scanning: {files_scanned:,} files | {throughput:,.0f}/s",
                            end="",
                            flush=True,
                        )

            # Scan with progress
            scanner = ConcurrentScanner()
            perf_profiler = PerformanceProfiler()

            with perf_profiler.profile("scan"):
                result = scanner.scan(path, progress_callback=progress_callback)

            # Clear progress line
            print("\r" + " " * 100 + "\r", end="")

            # Calculate metrics
            scan_time = perf_profiler.get_operation_time("scan")
            throughput = result.total_count / scan_time if scan_time > 0 else 0
            target_met = self._check_target(result.total_count, scan_time)

            check = (
                self.terminal.emoji("✅", "[OK]")
                if target_met
                else self.terminal.emoji("⚠️", "[WARN]")
            )

            # Print result
            self.terminal.print(
                f"     {check} {result.total_count:>8,} files | "
                f"{scan_time:>6.3f}s | "
                f"{throughput:>8,.0f}/s | "
                f"{result.error_count} errors"
            )

            return {
                "name": name,
                "path": str(path),
                "file_count": result.total_count,
                "scan_time": scan_time,
                "throughput": throughput,
                "error_count": result.error_count,
                "target_met": target_met,
                "estimated_files": dir_info.get("estimated_files", 0),
                "estimation_accuracy": (
                    dir_info.get("estimated_files", 0) / result.total_count
                    if result.total_count > 0
                    else 0
                ),
            }

        except Exception as e:
            # Graceful error handling
            self.terminal.print(f"     ⚠️ Failed: {type(e).__name__}: {e}")
            return {
                "name": name,
                "path": str(path),
                "error": str(e),
                "failed": True,
            }

    def _check_target(self, file_count: int, scan_time: float) -> bool:
        """Check if scan meets performance target.

        Args:
            file_count: Number of files scanned
            scan_time: Time taken

        Returns:
            True if target met
        """
        if file_count >= 10000:
            return scan_time < 30
        elif file_count >= 5000:
            return scan_time < 15
        elif file_count >= 1000:
            return scan_time < 5
        else:
            return scan_time < 5

    def evaluate_results(self) -> Tuple[bool, str]:
        """Phase 4: Evaluate results and provide recommendation.

        Returns:
            (all_passed, recommendation)
        """
        chart = self.terminal.emoji("📊", "[STAT]")
        divider = "=" * 60

        self.terminal.print(f"\n{divider}")
        self.terminal.print(f"{chart} Test Results Summary")
        self.terminal.print(divider)

        if not self.results:
            return False, "No successful tests - cannot recommend full scan"

        # Calculate statistics
        successful = [r for r in self.results if not r.get("failed", False)]
        failed = [r for r in self.results if r.get("failed", False)]

        total_files = sum(r.get("file_count", 0) for r in successful)
        total_time = sum(r.get("scan_time", 0) for r in successful)
        avg_throughput = total_files / total_time if total_time > 0 else 0
        targets_passed = sum(1 for r in successful if r.get("target_met", False))

        # Print summary
        self.terminal.print(f"\nDirectories tested: {len(successful)}")
        if failed:
            self.terminal.print(f"Directories failed: {len(failed)}")

        self.terminal.print(f"Total files scanned: {total_files:,}")
        self.terminal.print(f"Total time: {total_time:.2f}s")
        self.terminal.print(f"Average throughput: {avg_throughput:,.0f} files/s")

        # Target status
        all_passed = targets_passed == len(successful) and len(failed) == 0
        status = (
            self.terminal.emoji("✅", "[PASS]")
            if all_passed
            else self.terminal.emoji("⚠️", "[WARN]")
        )
        self.terminal.print(f"\n{status} Targets: {targets_passed}/{len(successful)} passed")

        # Recommendation
        if all_passed and avg_throughput > 10000:
            recommendation = "All tests passed - READY for full D:\\ scan (est. <5s)"
        elif all_passed:
            recommendation = "All tests passed - Ready for full D:\\ scan"
        elif len(failed) > len(successful):
            recommendation = "Multiple failures - Investigate errors before full scan"
        else:
            recommendation = "Some targets missed - Review results before full scan"

        self.terminal.print(f"\n💡 Recommendation: {recommendation}")

        return all_passed, recommendation

    def save_detailed_results(self):
        """Save detailed results to JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"large_scale_test_{timestamp}.json"

        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "total_tests": len(self.results),
                        "successful_tests": len(
                            [r for r in self.results if not r.get("failed", False)]
                        ),
                        "results": self.results,
                    },
                    f,
                    indent=2,
                    ensure_ascii=False,
                )

            self.terminal.print(f"\n💾 Detailed results saved to: {output_file}")
        except Exception as e:
            self.terminal.print(f"\n⚠️ Failed to save results: {e}")

    def run_full_test(self, d_path: Path = None) -> bool:
        """Run complete large-scale test suite.

        Args:
            d_path: D drive path (default: D:/)

        Returns:
            True if all tests passed
        """
        if d_path is None:
            d_path = Path("D:/")

        rocket = self.terminal.emoji("🚀", "[START]")
        divider = "=" * 60

        self.terminal.print(f"\n{divider}")
        self.terminal.print(f"{rocket} Large-Scale Performance Test")
        self.terminal.print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.terminal.print(f"Target: {d_path}")
        self.terminal.print(divider)

        # Phase 1: Analyze structure
        dir_infos = self.analyze_d_drive_structure(d_path)

        # Phase 2: Select representative directories
        selected = self.select_representative_directories(dir_infos)

        # Phase 3: Test directories
        test = self.terminal.emoji("🧪", "[TEST]")
        self.terminal.print(f"\n{divider}")
        self.terminal.print(f"{test} Phase 3: Testing Selected Directories")
        self.terminal.print(divider)

        for i, dir_info in enumerate(selected, 1):
            result = self.test_directory(dir_info, i, len(selected))
            if result:
                self.results.append(result)

        # Phase 4: Evaluate and recommend
        all_passed, recommendation = self.evaluate_results()

        # Save detailed results
        self.save_detailed_results()

        # Final summary
        total_elapsed = time.time() - self.start_time
        self.terminal.print(f"\n{divider}")
        self.terminal.print(f"⏱️ Total test time: {total_elapsed:.2f}s")
        self.terminal.print(divider)

        return all_passed


def main():
    """Run large-scale performance test."""
    import argparse

    parser = argparse.ArgumentParser(description="Large-scale performance test")
    parser.add_argument("--path", type=str, default="D:/", help="Path to test (default: D:/)")
    parser.add_argument("--output", type=str, default=None, help="Output directory for results")

    args = parser.parse_args()

    test = LargeScalePerformanceTest(output_dir=Path(args.output) if args.output else None)
    success = test.run_full_test(Path(args.path))

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
