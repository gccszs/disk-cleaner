#!/usr/bin/env python3
"""
Disk Space Analyzer - Cross-platform disk space analysis tool
Analyzes disk usage and identifies large files and directories
"""

import json
import os
import platform
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List


class DiskAnalyzer:
    def __init__(self, path: str = None, top_n: int = 20):
        self.path = path or self._get_default_path()
        self.top_n = top_n
        self.platform = platform.system()
        self.system = platform.system().lower()

    def _get_default_path(self) -> str:
        """Get default path based on platform"""
        system = platform.system()
        if system == "Windows":
            return "C:\\"
        elif system == "Darwin":  # macOS
            return "/"
        else:  # Linux
            return "/"

    def get_disk_usage(self) -> Dict:
        """Get overall disk usage statistics"""
        usage = os.statvfs(self.path) if hasattr(os, "statvfs") else None

        if usage:
            total = usage.f_frsize * usage.f_blocks
            used = usage.f_frsize * (usage.f_blocks - usage.f_bavail)
            free = usage.f_frsize * usage.f_bavail
        else:
            # Windows fallback
            import ctypes

            total_bytes = ctypes.c_ulonglong(0)
            free_bytes = ctypes.c_ulonglong(0)
            ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                ctypes.c_wchar_p(self.path),
                None,
                ctypes.byref(total_bytes),
                ctypes.byref(free_bytes),
            )
            total = total_bytes.value
            free = free_bytes.value
            used = total - free

        return {
            "path": self.path,
            "total_gb": round(total / (1024**3), 2),
            "used_gb": round(used / (1024**3), 2),
            "free_gb": round(free / (1024**3), 2),
            "usage_percent": round((used / total) * 100, 2) if total > 0 else 0,
        }

    def scan_directory(self, path: str = None, max_depth: int = 3) -> List[Dict]:
        """Scan directory and find largest subdirectories and files"""
        scan_path = Path(path or self.path)
        results = {"directories": [], "files": []}

        try:
            # Scan directories
            for item in scan_path.iterdir():
                if item.is_dir() and not item.is_symlink():
                    try:
                        size = self._get_dir_size(item, max_depth=1)
                        if size > 0:
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

                elif item.is_file():
                    try:
                        size = item.stat().st_size
                        if size > 10 * 1024 * 1024:  # Only files > 10MB
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

        except (PermissionError, OSError) as e:
            print(f"Error scanning {scan_path}: {e}", file=sys.stderr)

        # Sort by size
        results["directories"].sort(key=lambda x: x["size_gb"], reverse=True)
        results["files"].sort(key=lambda x: x["size_gb"], reverse=True)

        # Keep only top N
        results["directories"] = results["directories"][: self.top_n]
        results["files"] = results["files"][: self.top_n]

        return results

    def _get_dir_size(self, path: Path, max_depth: int = 1) -> int:
        """Calculate directory size"""
        total_size = 0
        try:
            for item in path.rglob("*") if max_depth > 0 else path.iterdir():
                if item.is_file() and not item.is_symlink():
                    try:
                        total_size += item.stat().st_size
                    except (PermissionError, OSError):
                        continue
        except (PermissionError, OSError):
            pass
        return total_size

    def get_temp_directories(self) -> List[str]:
        """Get platform-specific temporary directories"""
        temp_dirs = []

        if self.system == "windows":
            temp_dirs = [
                os.environ.get("TEMP", ""),
                os.environ.get("TMP", ""),
                os.path.join(os.environ.get("LOCALAPPDATA", ""), "Temp"),
                os.path.join(os.environ.get("TEMP", ""), "..", "Prefetch"),
                os.path.join(os.environ.get("WINDIR", ""), "Temp"),
                os.path.join(os.environ.get("WINDIR", ""), "Prefetch"),
            ]
        elif self.system == "darwin":
            temp_dirs = [
                "/tmp",
                "/private/tmp",
                os.path.expanduser("~/Library/Caches"),
            ]
        else:  # Linux
            temp_dirs = [
                "/tmp",
                "/var/tmp",
                "/var/cache",
            ]

        return [d for d in temp_dirs if d and os.path.exists(d)]

    def analyze_temp_files(self) -> Dict:
        """Analyze temporary file usage"""
        temp_dirs = self.get_temp_directories()
        results = []

        for temp_dir in temp_dirs:
            size = self._get_dir_size(Path(temp_dir), max_depth=2)
            results.append(
                {
                    "path": temp_dir,
                    "size_gb": round(size / (1024**3), 2),
                    "size_mb": round(size / (1024**2), 2),
                }
            )

        return {"temp_directories": results}

    def generate_report(self) -> Dict:
        """Generate comprehensive analysis report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "platform": self.platform,
            "disk_usage": self.get_disk_usage(),
            "temp_analysis": self.analyze_temp_files(),
        }

        if os.path.isdir(self.path):
            report["scan_results"] = self.scan_directory()

        return report


def print_report(report: Dict):
    """Print formatted report to console"""
    print("\n" + "=" * 60)
    print(f"DISK SPACE ANALYSIS REPORT - {report['timestamp']}")
    print("=" * 60)

    # Disk usage
    usage = report["disk_usage"]
    print(f"\n📊 Disk Usage ({usage['path']}):")
    print(f"  Total: {usage['total_gb']} GB")
    print(f"  Used:  {usage['used_gb']} GB ({usage['usage_percent']}%)")
    print(f"  Free:  {usage['free_gb']} GB")

    # Alert if low on space
    if usage["usage_percent"] > 90:
        print("  ⚠️  WARNING: Disk critically full!")
    elif usage["usage_percent"] > 80:
        print("  ⚠️  WARNING: Disk running low on space")

    # Temp directories
    print("\n🗑️  Temporary Directories:")
    for temp in report["temp_analysis"]["temp_directories"]:
        size_str = f"{temp['size_gb']} GB" if temp["size_gb"] > 0 else f"{temp['size_mb']} MB"
        print(f"  {temp['path']}: {size_str}")

    # Large directories
    if "scan_results" in report:
        print("\n📁 Largest Directories:")
        for i, d in enumerate(report["scan_results"]["directories"][:10], 1):
            size_str = f"{d['size_gb']} GB" if d["size_gb"] > 0 else f"{d['size_mb']} MB"
            print(f"  {i}. {d['name']}: {size_str}")

        print("\n📄 Largest Files:")
        for i, f in enumerate(report["scan_results"]["files"][:10], 1):
            size_str = f"{f['size_gb']} GB" if f["size_gb"] > 0 else f"{f['size_mb']} MB"
            print(f"  {i}. {f['name']}: {size_str}")

    print("\n" + "=" * 60)


def main():
    # Fix Windows console encoding for emoji support
    import sys

    if sys.platform == "win32":
        import codecs

        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
        sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")

    import argparse

    parser = argparse.ArgumentParser(description="Analyze disk space usage")
    parser.add_argument("--path", "-p", help="Path to analyze", default=None)
    parser.add_argument("--top", "-n", type=int, default=20, help="Number of top items to show")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--output", "-o", help="Save report to file")

    args = parser.parse_args()

    analyzer = DiskAnalyzer(path=args.path, top_n=args.top)
    report = analyzer.generate_report()

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_report(report)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\n✅ Report saved to {args.output}")


if __name__ == "__main__":
    main()
