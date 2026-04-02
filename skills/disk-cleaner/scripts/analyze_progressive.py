#!/usr/bin/env python3
"""
Progressive Disk Analyzer

Analysis tool optimized for large disks:
1. Quick sampling estimation (0.5-1 second)
2. Display estimated scan time
3. Progressive result display
4. Can interrupt anytime to view partial results
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Use smart bootstrap module import
try:
    script_dir = Path(__file__).parent.resolve()
    if str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))

    from skill_bootstrap import init_console, safe_print, setup_skill_environment

    # Initialize console encoding
    init_console()
    _, bootstrap = setup_skill_environment(require_modules=False)
    IMPORT_SUCCESS, MODULES = bootstrap.import_diskcleaner_modules()

    if IMPORT_SUCCESS:
        DirectoryScanner = MODULES.get("DirectoryScanner")
        Config = MODULES.get("Config")
    else:
        DirectoryScanner = None
        Config = None

except Exception as e:
    safe_print(f"Warning: Import failed - {e}")
    DirectoryScanner = None
    Config = None


class ProgressiveDiskAnalyzer:
    """Progressive disk analyzer - provides real-time feedback and early results"""

    def __init__(self, target_path: str = None):
        self.target_path = Path(target_path or self._get_default_path()).resolve()
        self.platform = sys.platform
        self.results_shown = 0
        self.start_time = None
        self.last_update_time = 0

    def _get_default_path(self) -> str:
        """Get default scan path"""
        if sys.platform == "Windows":
            return "C:\\"
        else:
            return "/"

    def quick_sample(self, sample_time: float = 1.0) -> Dict:
        """
        Quick sampling analysis - estimate directory characteristics within 1 second

        Returns:
            Dictionary containing estimation information
        """
        safe_print(f"\n[*] Quick sampling analysis... ({sample_time}s)")

        file_count = 0
        total_size = 0
        sample_dirs = 0
        start = time.time()

        try:
            # Use os.scandir for quick sampling
            for root, dirs, files in os.walk(str(self.target_path)):
                if time.time() - start > sample_time:
                    break

                sample_dirs += len(dirs)
                file_count += len(files)

                # Sample file sizes (max 100)
                for i, f in enumerate(files[:100]):
                    try:
                        file_path = Path(root) / f
                        if file_path.is_file():
                            total_size += file_path.stat().st_size
                    except (OSError, PermissionError):
                        pass

        except Exception as e:
            safe_print(f"Sampling error: {e}")

        elapsed = time.time() - start

        # Calculate estimates
        if elapsed > 0:
            files_per_second = file_count / elapsed
        else:
            files_per_second = 0

        # Estimate total time (2x safety margin)
        if files_per_second > 0:
            estimated_seconds = (file_count / files_per_second) * 2
        else:
            estimated_seconds = 0

        result = {
            "sample_file_count": file_count,
            "sample_size_gb": round(total_size / (1024**3), 2),
            "sample_dirs": sample_dirs,
            "files_per_second": round(files_per_second, 0),
            "estimated_time_seconds": round(estimated_seconds, 1),
        }

        # Display sampling results
        safe_print("\n[i] Sampling results:")
        safe_print(f"   Files found: {file_count:,}")
        safe_print(f"   Directories: {sample_dirs:,}")
        safe_print(f"   Scan speed: {result['files_per_second']:,} files/sec")

        if estimated_seconds > 0:
            if estimated_seconds < 60:
                safe_print(f"   Estimated full scan: {estimated_seconds:.0f} seconds")
            else:
                safe_print(f"   Estimated full scan: {estimated_seconds/60:.1f} minutes")

        return result

    def progressive_scan(
        self, max_files: int = None, max_seconds: int = None, show_progress: bool = True
    ) -> Dict:
        """
        Progressive scan - display results in real-time

        Args:
            max_files: Maximum file count limit
            max_seconds: Maximum time limit (seconds)
            show_progress: Whether to show progress

        Returns:
            Scan result dictionary
        """
        if DirectoryScanner is None:
            safe_print("[X] Advanced scanning not available, using basic method")
            return self._basic_scan()

        # Set limits
        if max_files is None:
            max_files = 50000  # Default 50k files
        if max_seconds is None:
            max_seconds = 30  # Default 30 seconds

        safe_print("\n[*] Progressive scan started")
        safe_print(f"   Limits: {max_files:,} files or {max_seconds} seconds")
        safe_print("   Press Ctrl+C anytime to interrupt and view partial results\n")

        self.start_time = time.time()
        results = {"directories": [], "files": [], "scanned": 0}

        try:
            scanner = DirectoryScanner(
                str(self.target_path),
                max_files=max_files,
                max_seconds=max_seconds,
                cache_enabled=False,
            )

            # Use generator for progressive processing
            file_count = 0
            last_display_time = 0
            display_interval = 2.0  # Display progress every 2 seconds

            for file_info in scanner.scan_generator():
                file_count += 1
                elapsed = time.time() - self.start_time

                # Progressive progress display
                if show_progress and elapsed - last_display_time > display_interval:
                    self._show_progress(file_count, elapsed, scanner.stopped_early)
                    last_display_time = elapsed

                # Collect large files (>10MB)
                if not file_info.is_dir and file_info.size > 10 * 1024 * 1024:
                    results["files"].append(
                        {
                            "path": file_info.path,
                            "name": file_info.name,
                            "size_gb": round(file_info.size / (1024**3), 2),
                            "size_mb": round(file_info.size / (1024**2), 2),
                        }
                    )

                # Collect directories (top-level only)
                if file_info.is_dir and Path(file_info.path).parent == self.target_path:
                    results["directories"].append(
                        {
                            "path": file_info.path,
                            "name": file_info.name,
                        }
                    )

            # Scan complete
            elapsed = time.time() - self.start_time
            self._show_progress(file_count, elapsed, True)

            # Calculate directory sizes
            results["directories"] = self._calculate_dir_sizes(results["directories"][:20])

            # Sort and limit result count
            results["files"].sort(key=lambda x: x["size_gb"], reverse=True)
            results["directories"].sort(key=lambda x: x["size_gb"], reverse=True)

            results["files"] = results["files"][:50]
            results["directories"] = results["directories"][:50]

            # Add scan information
            results["scan_info"] = {
                "files_scanned": file_count,
                "scan_time_seconds": round(elapsed, 1),
                "stopped_early": scanner.stopped_early,
                "stop_reason": scanner.stop_reason if scanner.stopped_early else "",
            }

        except KeyboardInterrupt:
            safe_print("\n\n[!] Scan interrupted by user")
            elapsed = time.time() - self.start_time
            safe_print(f"   Scanned: {results.get('scanned', 0):,} files")
            safe_print(f"   Time: {elapsed:.1f} seconds")

        except Exception as e:
            safe_print(f"\n[X] Scan error: {e}")
            return self._basic_scan()

        return results

    def _show_progress(self, file_count: int, elapsed: float, complete: bool = False):
        """Display scan progress"""
        if complete:
            safe_print(f"\n[OK] Scan complete: {file_count:,} files, {elapsed:.1f} seconds")
        else:
            safe_print(f"   Scanning: {file_count:,} files, {elapsed:.1f} seconds... (continuing)")

    def _calculate_dir_sizes(self, dirs: List[Dict], max_depth: int = 1) -> List[Dict]:
        """Calculate directory sizes"""
        results = []

        for dir_info in dirs:
            dir_path = Path(dir_info["path"])
            try:
                size = self._get_dir_size_fast(dir_path, max_depth)
                if size > 0:
                    results.append(
                        {
                            **dir_info,
                            "size_gb": round(size / (1024**3), 2),
                            "size_mb": round(size / (1024**2), 2),
                        }
                    )
            except (PermissionError, OSError):
                pass

        return results

    def _get_dir_size_fast(self, path: Path, max_depth: int = 1) -> int:
        """Fast directory size calculation"""
        total_size = 0
        try:
            with os.scandir(path) as it:
                for entry in it:
                    try:
                        if entry.is_file(follow_symlinks=False):
                            total_size += entry.stat().st_size
                        elif entry.is_dir(follow_symlinks=False) and max_depth > 0:
                            total_size += self._get_dir_size_fast(Path(entry.path), max_depth - 1)
                    except (PermissionError, OSError):
                        continue
        except (PermissionError, OSError):
            pass
        return total_size

    def _basic_scan(self) -> Dict:
        """Basic scan method (when advanced features unavailable)"""
        safe_print("\nUsing basic scan method...")

        results = {"directories": [], "files": []}
        file_count = 0

        try:
            # Only scan top level
            for item in self.target_path.iterdir():
                if item.is_dir() and not item.is_symlink():
                    try:
                        size = self._get_dir_size_fast(item, max_depth=1)
                        if size > 1024 * 1024:  # > 1MB
                            results["directories"].append(
                                {
                                    "path": str(item),
                                    "name": item.name,
                                    "size_gb": round(size / (1024**3), 2),
                                    "size_mb": round(size / (1024**2), 2),
                                }
                            )
                    except (PermissionError, OSError):
                        pass
                    file_count += 1
                elif item.is_file():
                    try:
                        size = item.stat().st_size
                        if size > 10 * 1024 * 1024:  # > 10MB
                            results["files"].append(
                                {
                                    "path": str(item),
                                    "name": item.name,
                                    "size_gb": round(size / (1024**3), 2),
                                    "size_mb": round(size / (1024**2), 2),
                                }
                            )
                    except (PermissionError, OSError):
                        pass
                    file_count += 1

        except Exception as e:
            safe_print(f"Basic scan also failed: {e}")

        results["directories"].sort(key=lambda x: x["size_gb"], reverse=True)
        results["files"].sort(key=lambda x: x["size_gb"], reverse=True)

        results["scan_info"] = {
            "files_scanned": file_count,
            "scan_time_seconds": 0,
            "stopped_early": False,
            "stop_reason": "",
        }

        return results

    def format_report(self, results: Dict) -> str:
        """Format report"""
        lines = []
        lines.append("\n" + "=" * 60)
        lines.append(f"DISK ANALYSIS REPORT - {self.target_path}")
        lines.append("=" * 60)

        # Scan info
        if "scan_info" in results:
            info = results["scan_info"]
            lines.append("\n[i] Scan Info:")
            lines.append(f"   Files scanned: {info.get('files_scanned', 0):,}")
            lines.append(f"   Time: {info.get('scan_time_seconds', 0):.1f} seconds")
            if info.get("stopped_early"):
                lines.append(f"   Stopped early: {info.get('stop_reason', 'Unknown')}")

        # Large directories
        if results.get("directories"):
            lines.append("\n[DIR] Largest Directories:")
            for i, d in enumerate(results["directories"][:20], 1):
                size_str = f"{d['size_gb']} GB" if d["size_gb"] > 0 else f"{d['size_mb']} MB"
                lines.append(f"   {i}. {d['name']}: {size_str}")

        # Large files
        if results.get("files"):
            lines.append("\n[FILE] Largest Files:")
            for i, f in enumerate(results["files"][:20], 1):
                size_str = f"{f['size_gb']} GB" if f["size_gb"] > 0 else f"{f['size_mb']} MB"
                # Shorten path
                path_str = f"...{f['path'][-50:]}" if len(f["path"]) > 50 else f["path"]
                lines.append(f"   {i}. {f['name']}: {size_str}")
                lines.append(f"      {path_str}")

        lines.append("\n" + "=" * 60)
        return "\n".join(lines)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Progressive disk analyzer - suitable for large disks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick sampling (1 second)
  python scripts/analyze_progressive.py --sample

  # Progressive scan (30 second limit)
  python scripts/analyze_progressive.py --max-seconds 30

  # Limit file count (fast)
  python scripts/analyze_progressive.py --max-files 10000

  # Full scan (long time)
  python scripts/analyze_progressive.py --max-seconds 300

  # Custom path
  python scripts/analyze_progressive.py --path "D:\\Projects" --sample
        """,
    )

    parser.add_argument("--path", "-p", help="Scan path")
    parser.add_argument("--sample", action="store_true", help="Quick sample only (1 second)")
    parser.add_argument(
        "--max-files", type=int, default=50000, help="Maximum file count limit (default: 50000)"
    )
    parser.add_argument("--max-seconds", type=int, default=30, help="Maximum time limit-seconds (default: 30)")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--no-progress", action="store_true", help="Disable progress")

    args = parser.parse_args()

    analyzer = ProgressiveDiskAnalyzer(args.path)

    # Quick sample mode
    if args.sample:
        sample_result = analyzer.quick_sample(sample_time=1.0)

        if args.json:
            print(json.dumps(sample_result, indent=2))
        return 0

    # Perform quick sampling first
    sample_result = analyzer.quick_sample(sample_time=1.0)

    # Ask whether to continue
    estimated_time = sample_result.get("estimated_time_seconds", 0)
    if estimated_time > 60:  # Over 1 minute
        safe_print(f"\n[!] Estimated scan time: {estimated_time/60:.1f} minutes")
        safe_print("Recommendations:")
        safe_print("   1. Use --sample for quick sample mode")
        safe_print("   2. Use --max-seconds to reduce time limit")
        safe_print("   3. Use --max-files to limit file count")

        # Non-interactive mode, return directly
        if args.json:
            print(json.dumps({"sample": sample_result}, indent=2))
        return 0

    # Progressive scan
    results = analyzer.progressive_scan(
        max_files=args.max_files, max_seconds=args.max_seconds, show_progress=not args.no_progress
    )

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        print(analyzer.format_report(results))

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        safe_print("\n\n[*] User interrupted")
        sys.exit(0)
