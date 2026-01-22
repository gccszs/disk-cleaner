#!/usr/bin/env python3
"""
Disk Monitor - Cross-platform disk usage monitoring tool
Monitors disk usage and alerts when thresholds are exceeded
"""

import os
import sys
import platform
import json
import time
import signal
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class DiskMonitor:
    def __init__(self, warning_threshold: int = 80, critical_threshold: int = 90):
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.platform = platform.system()
        self.running = True

        # Setup signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print("\n\n🛑 Shutting down monitor...")
        self.running = False

    def get_mount_points(self) -> List[str]:
        """Get all mount points/drives"""
        mount_points = []

        if self.platform == "Windows":
            # Get all drive letters
            import string
            for letter in string.ascii_uppercase:
                drive = f"{letter}:\\"
                if os.path.exists(drive):
                    mount_points.append(drive)

        elif self.platform == "Darwin":  # macOS
            # Common macOS mount points
            mount_points = ["/"]
            # Also check /Volumes for external drives
            volumes = Path("/Volumes")
            if volumes.exists():
                for item in volumes.iterdir():
                    if item.is_dir() and not item.is_symlink():
                        mount_points.append(str(item))

        else:  # Linux
            # Read from /proc/mounts or /etc/mtab
            try:
                with open("/proc/mounts", "r") as f:
                    for line in f:
                        parts = line.split()
                        if len(parts) >= 2:
                            mount_point = parts[1]
                            # Filter out virtual filesystems
                            if not mount_point.startswith("/proc") and \
                               not mount_point.startswith("/sys") and \
                               not mount_point.startswith("/dev"):
                                mount_points.append(mount_point)
            except:
                # Fallback to common locations
                mount_points = ["/", "/home"]

        return mount_points

    def get_disk_usage(self, path: str) -> Dict:
        """Get disk usage for a path"""
        try:
            if hasattr(os, 'statvfs'):
                # Unix-like systems
                stat = os.statvfs(path)
                total = stat.f_frsize * stat.f_blocks
                used = stat.f_frsize * (stat.f_blocks - stat.f_bavail)
                free = stat.f_frsize * stat.f_bavail
            else:
                # Windows
                import ctypes
                total_bytes = ctypes.c_ulonglong(0)
                free_bytes = ctypes.c_ulonglong(0)
                ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                    ctypes.c_wchar_p(path),
                    None,
                    ctypes.byref(total_bytes),
                    ctypes.byref(free_bytes)
                )
                total = total_bytes.value
                free = free_bytes.value
                used = total - free

            usage_percent = (used / total * 100) if total > 0 else 0

            return {
                "path": path,
                "total_gb": round(total / (1024**3), 2),
                "used_gb": round(used / (1024**3), 2),
                "free_gb": round(free / (1024**3), 2),
                "usage_percent": round(usage_percent, 2),
                "status": self._get_status(usage_percent)
            }

        except Exception as e:
            return {
                "path": path,
                "error": str(e),
                "status": "error"
            }

    def _get_status(self, usage_percent: float) -> str:
        """Get status based on usage percentage"""
        if usage_percent >= self.critical_threshold:
            return "critical"
        elif usage_percent >= self.warning_threshold:
            return "warning"
        else:
            return "ok"

    def monitor_all(self) -> Dict:
        """Monitor all mount points"""
        mount_points = self.get_mount_points()
        results = {
            "timestamp": datetime.now().isoformat(),
            "platform": self.platform,
            "drives": []
        }

        for mount_point in mount_points:
            usage = self.get_disk_usage(mount_point)
            results["drives"].append(usage)

        # Calculate summary
        critical_count = sum(1 for d in results["drives"]
                            if d.get("status") == "critical")
        warning_count = sum(1 for d in results["drives"]
                           if d.get("status") == "warning")

        results["summary"] = {
            "total_drives": len(results["drives"]),
            "critical": critical_count,
            "warning": warning_count,
            "overall_status": "critical" if critical_count > 0 else
                             "warning" if warning_count > 0 else "ok"
        }

        return results

    def print_status(self, results: Dict):
        """Print status to console"""
        print(f"\n{'='*70}")
        print(f"DISK MONITOR - {results['timestamp']}")
        print(f"{'='*70}")

        for drive in results["drives"]:
            if "error" in drive:
                print(f"\n❌ {drive['path']}: ERROR - {drive['error']}")
                continue

            path = drive["path"]
            usage = drive["usage_percent"]
            free_gb = drive["free_gb"]
            status = drive["status"]

            # Status indicator
            if status == "critical":
                indicator = "🔴 CRITICAL"
            elif status == "warning":
                indicator = "🟡 WARNING"
            else:
                indicator = "🟢 OK"

            # Build usage bar
            bar_length = 30
            filled = int(bar_length * usage / 100)
            bar = "█" * filled + "░" * (bar_length - filled)

            print(f"\n{indicator} {path}")
            print(f"  Usage: [{bar}] {usage}%")
            print(f"  Free: {free_gb} GB / {drive['total_gb']} GB")

            if status == "critical":
                print(f"  ⚠️  CRITICAL: Disk is {usage}% full!")
            elif status == "warning":
                print(f"  ⚠️  WARNING: Disk is {usage}% full")

        # Summary
        summary = results["summary"]
        print(f"\n{'─'*70}")
        print(f"Summary: {summary['total_drives']} drive(s), "
              f"{summary['critical']} critical, {summary['warning']} warning")
        print(f"Overall Status: {summary['overall_status'].upper()}")
        print(f"{'='*70}\n")

    def continuous_monitor(self, interval: int = 60):
        """Continuously monitor disk usage at specified interval"""
        print(f"\n🔍 Monitoring disk usage every {interval} seconds...")
        print("Press Ctrl+C to stop\n")

        while self.running:
            results = self.monitor_all()
            self.print_status(results)

            # Check for critical issues
            if results["summary"]["overall_status"] == "critical":
                print("🚨 CRITICAL DISK SPACE ISSUES DETECTED!")
                print("   Immediate action required!\n")

            # Wait for next interval
            for _ in range(interval):
                if not self.running:
                    break
                time.sleep(1)

    def check_thresholds(self) -> bool:
        """Check if any thresholds are exceeded"""
        results = self.monitor_all()
        return results["summary"]["overall_status"] in ["warning", "critical"]

    def get_drive_details(self, path: str) -> Dict:
        """Get detailed information about a specific drive"""
        usage = self.get_disk_usage(path)

        # Add additional details
        details = {**usage}

        # Get inode info for Unix
        if self.platform != "Windows" and "error" not in usage:
            try:
                stat = os.statvfs(path)
                details["inodes_total"] = stat.f_files
                details["inodes_free"] = stat.f_ffree
                details["inodes_used"] = stat.f_files - stat.f_ffree
                details["inodes_percent"] = round(
                    (details["inodes_used"] / stat.f_files * 100) if stat.f_files > 0 else 0, 2
                )
            except:
                pass

        return details


def print_alerts(results: Dict):
    """Print only alerts for drives exceeding thresholds"""
    summary = results["summary"]

    if summary["overall_status"] == "ok":
        return

    print(f"\n🚨 DISK SPACE ALERTS - {results['timestamp']}")
    print("="*60)

    for drive in results["drives"]:
        status = drive.get("status")
        if status in ["warning", "critical"]:
            path = drive["path"]
            usage = drive["usage_percent"]
            free_gb = drive["free_gb"]

            if status == "critical":
                print(f"🔴 CRITICAL: {path}")
                print(f"   Usage: {usage}% | Free: {free_gb} GB")
                print(f"   ACTION REQUIRED IMMEDIATELY")
            else:
                print(f"🟡 WARNING: {path}")
                print(f"   Usage: {usage}% | Free: {free_gb} GB")
                print(f"   Consider cleaning up soon")

    print("="*60)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Monitor disk usage")
    parser.add_argument("--warning", "-w", type=int, default=80,
                       help="Warning threshold (default: 80%%)")
    parser.add_argument("--critical", "-c", type=int, default=90,
                       help="Critical threshold (default: 90%%)")
    parser.add_argument("--watch", action="store_true",
                       help="Continuous monitoring mode")
    parser.add_argument("--interval", "-i", type=int, default=60,
                       help="Monitoring interval in seconds (default: 60)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--alerts-only", action="store_true",
                       help="Only show drives exceeding thresholds")
    parser.add_argument("--output", "-o", help="Save report to file")

    args = parser.parse_args()

    monitor = DiskMonitor(
        warning_threshold=args.warning,
        critical_threshold=args.critical
    )

    if args.watch:
        monitor.continuous_monitor(interval=args.interval)
    else:
        results = monitor.monitor_all()

        if args.json:
            print(json.dumps(results, indent=2))
        elif args.alerts_only:
            monitor.print_status(results)
            print_alerts(results)
        else:
            monitor.print_status(results)

        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"✅ Report saved to {args.output}")

        # Exit with error code if thresholds exceeded
        if results["summary"]["overall_status"] == "critical":
            sys.exit(2)
        elif results["summary"]["overall_status"] == "warning":
            sys.exit(1)
        else:
            sys.exit(0)


if __name__ == "__main__":
    main()
