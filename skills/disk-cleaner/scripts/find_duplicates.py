#!/usr/bin/env python3
"""
Duplicate File Finder - Find and report duplicate files

This script finds duplicate files using SHA-256 hash comparison.
It supports multiple strategies:
- adaptive: Automatically choose between fast and accurate (default)
- fast: Size + mtime pre-filtering for large directories
- accurate: SHA-256 hash comparison for smaller directories

Features:
- Progress bars for large scans
- ASCII-safe output for cross-platform compatibility
- Detailed statistics and reclaimable space calculation
"""

import argparse
import json
import os
import platform
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

# Add parent directory to path for imports
script_dir = Path(__file__).parent.parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

try:
    from diskcleaner.core.duplicate_finder import DuplicateFinder, DuplicateGroup
    from diskcleaner.core.progress import ProgressBar
    from diskcleaner.core.scanner import DirectoryScanner

    PROGRESS_AVAILABLE = True
except ImportError:
    print("Warning: diskcleaner modules not available", file=sys.stderr)
    PROGRESS_AVAILABLE = False


def format_size(bytes_size: int) -> str:
    """
    Format byte size to human-readable string.

    Args:
        bytes_size: Size in bytes

    Returns:
        Formatted string (e.g., "1.5 GB", "500 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} PB"


def print_duplicates(duplicates: List[DuplicateGroup], show_all: bool = False):
    """
    Print duplicate file groups to console.

    Args:
        duplicates: List of DuplicateGroup objects
        show_all: Show all files or just summary
    """
    if not duplicates:
        print("\nNo duplicate files found!")
        return

    print(f"\nFound {len(duplicates)} groups of duplicate files:")
    print("=" * 80)

    for i, group in enumerate(duplicates, 1):
        print(f"\nGroup {i}: {group.count} files x {format_size(group.size)}")
        print(f"  Reclaimable: {format_size(group.reclaimable_space)}")
        print(f"  Files:")

        for j, file_info in enumerate(group.files, 1):
            print(f"    {j}. {file_info.path}")

        # Only show first 10 groups unless --all is specified
        if i >= 10 and not show_all:
            remaining = len(duplicates) - 10
            print(f"\n... and {remaining} more groups (use --all to see all)")
            break


def print_statistics(duplicates: List[DuplicateGroup]):
    """
    Print statistics about duplicate files.

    Args:
        duplicates: List of DuplicateGroup objects
    """
    if not duplicates:
        print("\nNo duplicate files found!")
        return

    # Calculate statistics
    group_count = len(duplicates)
    total_files = sum(g.count for g in duplicates)
    total_size = sum(g.size * g.count for g in duplicates)
    total_reclaimable = sum(g.reclaimable_space for g in duplicates)

    # Find largest group
    largest_group = max(duplicates, key=lambda g: g.reclaimable_space)

    print("\n" + "=" * 80)
    print("DUPLICATE FILE STATISTICS")
    print("=" * 80)
    print(f"Total duplicate groups: {group_count}")
    print(f"Total duplicate files: {total_files}")
    print(f"Total size of duplicates: {format_size(total_size)}")
    print(f"Total reclaimable space: {format_size(total_reclaimable)}")
    print(f"\nLargest duplicate group:")
    print(f"  Files: {largest_group.count}")
    print(f"  Size per file: {format_size(largest_group.size)}")
    print(f"  Reclaimable: {format_size(largest_group.reclaimable_space)}")
    print("=" * 80)


def find_duplicates(
    path: str,
    strategy: str = "adaptive",
    show_progress: bool = True,
    max_files: int = None,
    max_seconds: int = None,
) -> tuple[List[DuplicateGroup], Dict]:
    """
    Find duplicate files in the specified path.

    Args:
        path: Path to scan for duplicates
        strategy: Detection strategy ('adaptive', 'fast', 'accurate')
        show_progress: Show progress bar
        max_files: Maximum number of files to scan
        max_seconds: Maximum scan time in seconds

    Returns:
        Tuple of (duplicates list, statistics dict)
    """
    scan_path = Path(path)

    if not scan_path.exists():
        raise ValueError(f"Path does not exist: {path}")

    if not scan_path.is_dir():
        raise ValueError(f"Path is not a directory: {path}")

    print(f"Scanning {scan_path} for duplicates...")

    # Collect all files using DirectoryScanner if available
    all_files = []

    if PROGRESS_AVAILABLE:
        try:
            scanner = DirectoryScanner(
                str(scan_path),
                max_files=max_files or 1000000,
                max_seconds=max_seconds or 300,
                cache_enabled=False,
            )

            if show_progress and sys.stdout.isatty():
                progress = ProgressBar(None, prefix="Scanning files")
                file_count = 0

                for file_info in scanner.scan_generator():
                    if not file_info.is_dir:
                        all_files.append(file_info)
                        file_count += 1
                        if file_count % 100 == 0:
                            progress.update(file_count, f"Found {file_count} files")

                progress.close()
            else:
                for file_info in scanner.scan_generator():
                    if not file_info.is_dir:
                        all_files.append(file_info)

            if scanner.stopped_early:
                print(f"\nWarning: Scan stopped early - {scanner.stop_reason}")

        except Exception as e:
            print(f"Scanner error: {e}", file=sys.stderr)
            print("Falling back to basic scan...", file=sys.stderr)
            # Fallback to basic scan
            all_files = _basic_scan(scan_path)
    else:
        # Basic scan without DirectoryScanner
        all_files = _basic_scan(scan_path)

    if not all_files:
        print("No files found in directory")
        return [], {}

    print(f"Analyzing {len(all_files)} files for duplicates...")

    # Find duplicates
    finder = DuplicateFinder(strategy=strategy)
    duplicates = finder.find_duplicates(all_files)

    # Get statistics
    stats = finder.get_duplicate_stats(duplicates)

    return duplicates, stats


def _basic_scan(scan_path: Path) -> List:
    """
    Basic file scan without DirectoryScanner.

    Args:
        scan_path: Path to scan

    Returns:
        List of file info objects
    """
    # Import FileInfo for creating objects
    from diskcleaner.core.scanner import FileInfo

    all_files = []

    try:
        for root, dirs, files in os.walk(scan_path):
            for filename in files:
                try:
                    filepath = os.path.join(root, filename)
                    stat = os.stat(filepath)

                    # Create FileInfo object
                    file_info = FileInfo(
                        path=filepath,
                        name=filename,
                        size=stat.st_size,
                        is_dir=False,
                        mtime=stat.st_mtime,
                    )
                    all_files.append(file_info)

                except (OSError, PermissionError):
                    continue

    except (OSError, PermissionError) as e:
        print(f"Error scanning directory: {e}", file=sys.stderr)

    return all_files


def generate_report(
    path: str,
    duplicates: List[DuplicateGroup],
    stats: Dict,
) -> Dict:
    """
    Generate a comprehensive report.

    Args:
        path: Path that was scanned
        duplicates: List of duplicate groups
        stats: Statistics dictionary

    Returns:
        Report dictionary
    """
    report = {
        "timestamp": datetime.now().isoformat(),
        "platform": platform.system(),
        "path": path,
        "statistics": stats,
        "duplicates": [],
    }

    # Add duplicate group details
    for group in duplicates:
        group_data = {
            "count": group.count,
            "size": group.size,
            "size_human": format_size(group.size),
            "reclaimable_space": group.reclaimable_space,
            "reclaimable_human": format_size(group.reclaimable_space),
            "hash": group.hash_value,
            "files": [f.path for f in group.files],
        }
        report["duplicates"].append(group_data)

    return report


def main():
    """Main entry point"""
    # Fix Windows console encoding
    if sys.platform == "win32":
        import codecs
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
        sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")

    parser = argparse.ArgumentParser(
        description="Find duplicate files using hash comparison",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Find duplicates in current directory
  python scripts/find_duplicates.py

  # Find duplicates in specific path
  python scripts/find_duplicates.py --path "/path/to/directory"

  # Use fast strategy for large directories
  python scripts/find_duplicates.py --strategy fast

  # Show all duplicate groups (not just first 10)
  python scripts/find_duplicates.py --all

  # Output as JSON
  python scripts/find_duplicates.py --json --output duplicates.json

  # With scan limits for large directories
  python scripts/find_duplicates.py --file-limit 500000 --time-limit 180
        """,
    )

    parser.add_argument(
        "--path",
        "-p",
        default=".",
        help="Path to scan for duplicates (default: current directory)",
    )
    parser.add_argument(
        "--strategy",
        "-s",
        choices=["adaptive", "fast", "accurate"],
        default="adaptive",
        help="Duplicate detection strategy (default: adaptive)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Show all duplicate groups (not just first 10)",
    )
    parser.add_argument(
        "--json", action="store_true", help="Output as JSON instead of human-readable"
    )
    parser.add_argument(
        "--output", "-o", help="Save report to file (JSON format)"
    )
    parser.add_argument(
        "--file-limit",
        type=int,
        default=None,
        help="Maximum number of files to scan (default: 1000000)",
    )
    parser.add_argument(
        "--time-limit",
        type=int,
        default=None,
        help="Maximum scan time in seconds (default: 300)",
    )
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Disable progress bars (useful for scripting)",
    )

    args = parser.parse_args()

    try:
        # Find duplicates
        show_progress = not args.no_progress and not args.json
        duplicates, stats = find_duplicates(
            path=args.path,
            strategy=args.strategy,
            show_progress=show_progress,
            max_files=args.file_limit,
            max_seconds=args.time_limit,
        )

        # Output results
        if args.json:
            # Generate and output JSON report
            report = generate_report(args.path, duplicates, stats)
            print(json.dumps(report, indent=2))
        else:
            # Print human-readable output
            print_statistics(duplicates)
            print_duplicates(duplicates, show_all=args.all)

        # Save to file if requested
        if args.output:
            report = generate_report(args.path, duplicates, stats)
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)
            print(f"\nReport saved to {args.output}")

        # Exit code based on whether duplicates were found
        sys.exit(0 if len(duplicates) == 0 else 1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
