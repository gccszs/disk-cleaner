#!/usr/bin/env python3
"""
Disk Growth Analyzer - Track and analyze disk space growth trends

This script analyzes disk usage over time to:
- Calculate growth rates (daily, weekly, monthly)
- Predict when disk will be full
- Identify unusual growth patterns
- Generate trend reports

Features:
- JSON-based historical data storage
- ASCII-safe output
- Cross-platform compatibility
- Progress bars for large operations
"""

import argparse
import json
import os
import platform
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict

# Add parent directory to path for imports
script_dir = Path(__file__).parent.parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

try:
    from diskcleaner.core.growth_analyzer import GrowthAnalyzer, format_size
    from diskcleaner.core.progress import ProgressBar

    PROGRESS_AVAILABLE = True
except ImportError:
    print("Warning: diskcleaner modules not available", file=sys.stderr)
    PROGRESS_AVAILABLE = False


def capture_snapshot(path: str, analyzer: GrowthAnalyzer) -> Dict:
    """
    Capture current disk usage snapshot.

    Args:
        path: Path to analyze
        analyzer: GrowthAnalyzer instance

    Returns:
        Snapshot dictionary
    """
    print(f"\n[*] Capturing disk usage snapshot for {path}...")

    # Get disk usage
    try:
        if hasattr(os, 'statvfs'):
            # Unix-like systems
            stat = os.statvfs(path)
            total_bytes = stat.f_frsize * stat.f_blocks
            free_bytes = stat.f_frsize * stat.f_bavail
            used_bytes = total_bytes - free_bytes
        else:
            # Windows
            import ctypes
            total_bytes = ctypes.c_ulonglong(0)
            free_bytes = ctypes.c_ulonglong(0)
            ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                ctypes.c_wchar_p(path),
                None,
                ctypes.byref(total_bytes),
                ctypes.byref(free_bytes),
            )
            total_bytes = total_bytes.value
            free_bytes = free_bytes.value
            used_bytes = total_bytes - free_bytes

        # Create metadata
        metadata = {
            "platform": platform.system(),
            "hostname": platform.node(),
        }

        # Add snapshot to history
        success = analyzer.add_snapshot(
            path=path,
            used_bytes=used_bytes,
            total_bytes=total_bytes,
            free_bytes=free_bytes,
            metadata=metadata,
        )

        if success:
            print(f"[OK] Snapshot captured successfully")
            print(f"  Total: {format_size(total_bytes)}")
            print(f"  Used:  {format_size(used_bytes)} ({used_bytes/total_bytes*100:.1f}%)")
            print(f"  Free:  {format_size(free_bytes)}")

            return {
                "path": path,
                "used_bytes": used_bytes,
                "total_bytes": total_bytes,
                "free_bytes": free_bytes,
                "used_percent": round((used_bytes / total_bytes * 100), 2),
            }
        else:
            print("[!] Failed to save snapshot")
            return {"error": "Failed to save snapshot"}

    except Exception as e:
        print(f"[!] Error capturing snapshot: {e}")
        return {"error": str(e)}


def print_growth_report(report: Dict):
    """
    Print formatted growth analysis report.

    Args:
        report: Report dictionary from generate_report()
    """
    print("\n" + "=" * 80)
    print("DISK GROWTH ANALYSIS REPORT")
    print("=" * 80)

    if "error" in report:
        print(f"\n[!] Error: {report['error']}")
        if "message" in report:
            print(f"[*] {report['message']}")
        print("\n" + "=" * 80)
        return

    # Basic info
    print(f"\n[*] Analysis Date: {report['analysis_date']}")
    print(f"[*] Path: {report['path']}")
    print(f"[*] Data Points: {report['snapshots_count']} snapshots")
    print(f"[*] Date Range: {report['date_range']['earliest']} to {report['date_range']['latest']}")

    # Latest snapshot
    latest = report['latest_snapshot']
    print(f"\n[*] Current Usage:")
    print(f"  Total: {format_size(latest['total_bytes'])}")
    print(f"  Used:  {format_size(latest['used_bytes'])} ({latest['used_percent']:.1f}%)")
    print(f"  Free:  {format_size(latest['free_bytes'])}")

    # Growth rates
    print(f"\n[*] Growth Rates:")

    for period in ['daily', 'weekly', 'monthly']:
        rate_data = report['growth_rates'][period]

        if 'error' not in rate_data:
            period_name = period.capitalize()
            growth_mb = rate_data['avg_growth_mb_per_period']
            growth_gb = rate_data['avg_growth_gb_per_period']

            # Use appropriate unit
            if growth_gb >= 0.01:
                growth_str = f"{growth_gb:.2f} GB"
            else:
                growth_str = f"{growth_mb:.2f} MB"

            print(f"  {period_name}: {growth_str} / {period}")

            # Show trend if available
            if 'trend' in rate_data:
                trend = rate_data['trend']
                if trend == 'accelerating':
                    print(f"    Trend: Accelerating (+)")
                elif trend == 'decelerating':
                    print(f"    Trend: Decelerating (-)")
                else:
                    print(f"    Trend: Stable")

    # Prediction
    prediction = report['prediction']

    if 'error' not in prediction:
        print(f"\n[*] Prediction:")

        if 'message' in prediction:
            print(f"  {prediction['message']}")
        else:
            daily_growth_mb = prediction['daily_growth_mb']
            daily_growth_gb = prediction['daily_growth_gb']

            if daily_growth_gb >= 0.01:
                growth_str = f"{daily_growth_gb:.2f} GB"
            else:
                growth_str = f"{daily_growth_mb:.2f} MB"

            print(f"  Daily growth: {growth_str}")
            print(f"  Days until full: {prediction['days_until_full']:.0f}")

            if prediction['days_until_full'] < 30:
                print(f"  [!] WARNING: Disk will be full on {prediction['predicted_full_date_human']}")
                print(f"      ({prediction['weeks_until_full']:.1f} weeks)")
            elif prediction['days_until_full'] < 90:
                print(f"  [!] Caution: Disk will be full on {prediction['predicted_full_date_human']}")
                print(f"      ({prediction['months_until_full']:.1f} months)")
            else:
                print(f"  Estimated full date: {prediction['predicted_full_date_human']}")
                print(f"      ({prediction['months_until_full']:.1f} months)")

    # Warnings
    if latest['used_percent'] > 90:
        print(f"\n[!] CRITICAL: Disk is {latest['used_percent']:.1f}% full!")
    elif latest['used_percent'] > 80:
        print(f"\n[!] WARNING: Disk is {latest['used_percent']:.1f}% full")

    print("\n" + "=" * 80)


def print_history(snapshots: list, limit: int = 20):
    """
    Print historical snapshots.

    Args:
        snapshots: List of snapshot dictionaries
        limit: Maximum number to show
    """
    if not snapshots:
        print("\n[*] No historical data available")
        return

    print(f"\n[*] Historical Data (showing last {min(limit, len(snapshots))} of {len(snapshots)} snapshots):")
    print("-" * 80)

    for snapshot in snapshots[-limit:]:
        timestamp = snapshot['timestamp']
        used_percent = snapshot['used_percent']
        used_mb = snapshot['used_bytes'] / (1024**2)

        print(f"  {timestamp}: {used_percent:.1f}% used ({used_mb:.0f} MB)")

    print("-" * 80)


def main():
    """Main entry point"""
    # Fix Windows console encoding
    if sys.platform == "win32":
        import codecs
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
        sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")

    parser = argparse.ArgumentParser(
        description="Analyze disk space growth trends",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Capture a snapshot and analyze growth
  python scripts/analyze_growth.py --capture

  # Analyze existing growth data
  python scripts/analyze_growth.py

  # Analyze specific path
  python scripts/analyze_growth.py --path "/home"

  # Show historical data
  python scripts/analyze_growth.py --history

  # Capture snapshot without analysis
  python scripts/analyze_growth.py --capture --no-analyze

  # Use custom data file
  python scripts/analyze_growth.py --data-file /path/to/growth.json

  # Clean up old data (keep last year)
  python scripts/analyze_growth.py --cleanup 365
        """,
    )

    parser.add_argument(
        "--path",
        "-p",
        default=None,
        help="Path to analyze (default: auto-detect)",
    )
    parser.add_argument(
        "--capture",
        action="store_true",
        help="Capture current disk usage snapshot",
    )
    parser.add_argument(
        "--no-analyze",
        action="store_true",
        help="Skip analysis after capturing (only useful with --capture)",
    )
    parser.add_argument(
        "--history",
        action="store_true",
        help="Show historical snapshot data",
    )
    parser.add_argument(
        "--data-file",
        help="Path to JSON file for storing data (default: ~/.diskcleaner/growth_history.json)",
    )
    parser.add_argument(
        "--cleanup",
        type=int,
        metavar="DAYS",
        help="Remove snapshots older than N days",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON instead of human-readable",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Save report to file (JSON format)",
    )

    args = parser.parse_args()

    # Initialize analyzer
    try:
        analyzer = GrowthAnalyzer(data_file=args.data_file)
        print(f"[*] Data file: {analyzer.data_file}")
    except Exception as e:
        print(f"[!] Error initializing analyzer: {e}", file=sys.stderr)
        sys.exit(2)

    # Capture snapshot if requested
    if args.capture:
        # Determine path
        if args.path:
            path = args.path
        else:
            # Auto-detect default path
            system = platform.system()
            if system == "Windows":
                path = "C:\\"
            elif system == "Darwin":  # macOS
                path = "/"
            else:  # Linux
                path = "/"

        snapshot = capture_snapshot(path, analyzer)

        if "error" in snapshot:
            sys.exit(2)

        # Skip analysis if requested
        if args.no_analyze:
            print("[OK] Snapshot captured, analysis skipped")
            sys.exit(0)

    # Cleanup old data if requested
    if args.cleanup:
        removed = analyzer.cleanup_old_data(days=args.cleanup)
        print(f"[OK] Removed {removed} old snapshots")
        sys.exit(0)

    # Show history if requested
    if args.history:
        snapshots = analyzer.get_snapshots(path=args.path)
        print_history(snapshots, limit=50)
        sys.exit(0)

    # Generate and display report
    if not args.capture and not args.history and not args.cleanup:
        print("[*] Analyzing growth trends...")

    report = analyzer.generate_report(path=args.path)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_growth_report(report)

    # Save to file if requested
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"\n[OK] Report saved to {args.output}")

    # Exit code based on disk usage
    if "error" not in report and "latest_snapshot" in report:
        usage_percent = report["latest_snapshot"]["used_percent"]
        if usage_percent > 90:
            sys.exit(2)  # Critical
        elif usage_percent > 80:
            sys.exit(1)  # Warning
        else:
            sys.exit(0)  # OK
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
