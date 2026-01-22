#!/usr/bin/env python3
"""
Disk Cleaner - Cross-platform junk file cleaner
Safely removes temporary files, caches, logs, and other junk files
"""

import os
import sys
import platform
import shutil
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Set, Tuple


class DiskCleaner:
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.platform = platform.system()
        self.system = platform.system().lower()
        self.cleaned_files = []
        self.freed_space = 0
        self.errors = []

        # Safety: paths to never delete
        self.protected_paths = self._get_protected_paths()

        # Safety: file extensions to never delete
        self.protected_extensions = {
            '.exe', '.dll', '.sys', '.drv', '.bat', '.cmd', '.ps1',
            '.sh', '.bash', '.zsh', '.app', '.dmg', '.pkg', '.deb',
            '.rpm', '.msi', '.iso', '.vhd', '.vhdx'
        }

    def _get_protected_paths(self) -> Set[str]:
        """Get paths that should never be deleted"""
        protected = set()

        if self.system == "windows":
            protected.update([
                "C:\\Windows",
                "C:\\Program Files",
                "C:\\Program Files (x86)",
                "C:\\ProgramData",
            ])
            # User profiles
            if "USERPROFILE" in os.environ:
                protected.add(os.environ["USERPROFILE"])

        elif self.system == "darwin":
            protected.update([
                "/System",
                "/Library",
                "/Applications",
                "/usr",
                "/bin",
                "/sbin",
            ])
            protected.add(os.path.expanduser("~"))

        else:  # Linux
            protected.update([
                "/usr", "/bin", "/sbin", "/lib", "/lib64",
                "/etc", "/boot", "/sys", "/proc", "/dev"
            ])
            protected.add(os.path.expanduser("~"))

        return protected

    def _is_safe_to_delete(self, path: Path) -> bool:
        """Check if a path is safe to delete"""
        # Check if path is in protected locations
        for protected in self.protected_paths:
            try:
                if str(path).startswith(protected):
                    return False
            except:
                continue

        # Check file extension
        if path.suffix.lower() in self.protected_extensions:
            return False

        return True

    def get_cleanable_locations(self) -> Dict[str, List[str]]:
        """Get platform-specific locations that can be cleaned"""
        locations = {
            "temp": [],
            "cache": [],
            "logs": [],
            "recycle": [],
            "downloads_old": []
        }

        if self.system == "windows":
            # Temp directories
            temp_dirs = [
                os.environ.get("TEMP", ""),
                os.environ.get("TMP", ""),
                os.path.join(os.environ.get("LOCALAPPDATA", ""), "Temp"),
            ]
            locations["temp"].extend([d for d in temp_dirs if d and os.path.exists(d)])

            # Cache directories
            cache_dirs = [
                os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "INetCache"),
                os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google", "Chrome", "User Data", "Default", "Cache"),
                os.path.join(os.environ.get("APPDATA", ""), "Mozilla", "Firefox", "Profiles"),
                os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Edge", "User Data", "Default", "Cache"),
            ]
            locations["cache"].extend([d for d in cache_dirs if d and os.path.exists(d)])

            # Windows specific
            locations["logs"].extend([
                os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "History"),
                os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "WebCache"),
            ])

            # Recycle Bin
            recycle_path = os.path.join(os.environ.get("SYSTEMDRIVE", "C:"), "$Recycle.Bin")
            if os.path.exists(recycle_path):
                locations["recycle"].append(recycle_path)

            # Prefetch
            prefetch = os.path.join(os.environ.get("WINDIR", ""), "Prefetch")
            if os.path.exists(prefetch):
                locations["temp"].append(prefetch)

            # Windows Update cache
            update_cache = os.path.join(os.environ.get("WINDIR", ""), "SoftwareDistribution", "Download")
            if os.path.exists(update_cache):
                locations["temp"].append(update_cache)

        elif self.system == "darwin":
            # macOS temp and cache
            locations["temp"].extend([
                "/tmp",
                "/private/tmp",
            ])
            locations["cache"].extend([
                os.path.expanduser("~/Library/Caches"),
            ])

            # User logs
            locations["logs"].append(os.path.expanduser("~/Library/Logs"))

            # iOS device backups
            backup_path = os.path.expanduser("~/Library/Application Support/MobileSync/Backup")
            if os.path.exists(backup_path):
                locations["cache"].append(backup_path)

        else:  # Linux
            # System temp and cache
            locations["temp"].extend([
                "/tmp",
                "/var/tmp",
            ])
            locations["cache"].extend([
                "/var/cache",
            ])

            # User cache
            user_cache = os.path.expanduser("~/.cache")
            if os.path.exists(user_cache):
                locations["cache"].append(user_cache)

        return locations

    def clean_directory(self, path: str, older_than_days: int = 0,
                       max_size_mb: int = None, pattern: str = "*") -> Dict:
        """Clean a directory with safety checks"""
        result = {
            "path": path,
            "files_deleted": 0,
            "space_freed_mb": 0,
            "errors": []
        }

        dir_path = Path(path)
        if not dir_path.exists():
            return result

        cutoff_date = datetime.now() - timedelta(days=older_than_days)

        try:
            for item in dir_path.glob(pattern):
                if not item.exists():
                    continue

                try:
                    # Safety check
                    if not self._is_safe_to_delete(item):
                        continue

                    # Age check
                    if older_than_days > 0:
                        mtime = datetime.fromtimestamp(item.stat().st_mtime)
                        if mtime > cutoff_date:
                            continue

                    # Size check
                    if max_size_mb:
                        size_mb = item.stat().st_size / (1024 * 1024)
                        if size_mb > max_size_mb:
                            continue

                    # Calculate size
                    size = item.stat().st_size

                    # Delete (or simulate)
                    if self.dry_run:
                        result["files_deleted"] += 1
                        result["space_freed_mb"] += size / (1024 * 1024)
                    else:
                        if item.is_dir():
                            shutil.rmtree(item, ignore_errors=True)
                        else:
                            item.unlink()

                        result["files_deleted"] += 1
                        result["space_freed_mb"] += size / (1024 * 1024)

                except (PermissionError, OSError) as e:
                    result["errors"].append(str(e))
                    self.errors.append(f"{item}: {e}")

        except (PermissionError, OSError) as e:
            result["errors"].append(str(e))

        result["space_freed_mb"] = round(result["space_freed_mb"], 2)
        return result

    def clean_temp_files(self) -> Dict:
        """Clean temporary files"""
        locations = self.get_cleanable_locations()
        results = {"category": "temp_files", "locations": []}

        for temp_dir in locations.get("temp", []):
            result = self.clean_directory(temp_dir, older_than_days=0)
            results["locations"].append(result)

        return results

    def clean_cache_files(self) -> Dict:
        """Clean cache files"""
        locations = self.get_cleanable_locations()
        results = {"category": "cache", "locations": []}

        for cache_dir in locations.get("cache", []):
            result = self.clean_directory(cache_dir, older_than_days=30)
            results["locations"].append(result)

        return results

    def clean_log_files(self) -> Dict:
        """Clean log files"""
        locations = self.get_cleanable_locations()
        results = {"category": "logs", "locations": []}

        for log_dir in locations.get("logs", []):
            result = self.clean_directory(log_dir, older_than_days=30, pattern="*.log")
            results["locations"].append(result)

        return results

    def clean_recycle_bin(self) -> Dict:
        """Clean recycle bin/trash"""
        locations = self.get_cleanable_locations()
        results = {"category": "recycle_bin", "locations": []}

        for recycle_dir in locations.get("recycle", []):
            result = self.clean_directory(recycle_dir, older_than_days=30)
            results["locations"].append(result)

        return results

    def clean_old_downloads(self, days: int = 90) -> Dict:
        """Clean old download files"""
        downloads_path = os.path.expanduser("~/Downloads")
        results = {"category": "old_downloads", "locations": []}

        if os.path.exists(downloads_path):
            result = self.clean_directory(downloads_path, older_than_days=days)
            results["locations"].append(result)

        return results

    def clean_all(self) -> Dict:
        """Run all cleaning operations"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "platform": self.platform,
            "dry_run": self.dry_run,
            "categories": []
        }

        # Clean temp files
        temp_result = self.clean_temp_files()
        results["categories"].append(temp_result)

        # Clean cache
        cache_result = self.clean_cache_files()
        results["categories"].append(cache_result)

        # Clean logs
        log_result = self.clean_log_files()
        results["categories"].append(log_result)

        # Clean recycle bin
        recycle_result = self.clean_recycle_bin()
        results["categories"].append(recycle_result)

        # Calculate totals
        total_files = 0
        total_space_mb = 0

        for category in results["categories"]:
            for location in category["locations"]:
                total_files += location["files_deleted"]
                total_space_mb += location["space_freed_mb"]

        results["summary"] = {
            "total_files_deleted": total_files,
            "total_space_freed_mb": round(total_space_mb, 2),
            "total_space_freed_gb": round(total_space_mb / 1024, 2),
            "total_errors": len(self.errors)
        }

        return results


def print_report(results: Dict):
    """Print formatted cleaning report"""
    mode = "DRY RUN" if results["dry_run"] else "CLEAN"

    print("\n" + "="*60)
    print(f"DISK CLEANING REPORT ({mode}) - {results['timestamp']}")
    print("="*60)

    for category in results["categories"]:
        print(f"\n🗑️  {category['category'].upper().replace('_', ' ')}:")

        for location in category["locations"]:
            if location["files_deleted"] > 0:
                space_mb = location["space_freed_mb"]
                space_str = f"{space_mb:.2f} MB" if space_mb < 1024 else f"{space_mb/1024:.2f} GB"
                print(f"  ✅ {location['path']}")
                print(f"     Files: {location['files_deleted']}, Space: {space_str}")
            elif location["errors"]:
                print(f"  ⚠️  {location['path']}: {len(location['errors'])} errors")

    summary = results["summary"]
    print(f"\n📊 SUMMARY:")
    print(f"  Total files: {summary['total_files_deleted']}")
    print(f"  Space freed: {summary['total_space_freed_gb']:.2f} GB")

    if summary["total_errors"] > 0:
        print(f"  ⚠️  Errors: {summary['total_errors']}")

    if results["dry_run"]:
        print("\n💡 This was a DRY RUN. No files were actually deleted.")
        print("   Run without --dry-run to perform actual cleaning.")

    print("="*60)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Clean disk junk files")
    parser.add_argument("--dry-run", action="store_true", default=True,
                       help="Simulate cleaning without deleting (default: True)")
    parser.add_argument("--force", action="store_true",
                       help="Actually delete files (disables dry-run)")
    parser.add_argument("--temp", action="store_true", help="Clean only temp files")
    parser.add_argument("--cache", action="store_true", help="Clean only cache")
    parser.add_argument("--logs", action="store_true", help="Clean only logs")
    parser.add_argument("--recycle", action="store_true", help="Clean only recycle bin")
    parser.add_argument("--downloads", type=int, metavar="DAYS",
                       help="Clean downloads older than N days")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--output", "-o", help="Save report to file")

    args = parser.parse_args()

    dry_run = args.dry_run and not args.force
    cleaner = DiskCleaner(dry_run=dry_run)

    # Run specific or all cleaning
    if args.temp:
        results = {"timestamp": datetime.now().isoformat(), "dry_run": dry_run,
                   "categories": [cleaner.clean_temp_files()]}
    elif args.cache:
        results = {"timestamp": datetime.now().isoformat(), "dry_run": dry_run,
                   "categories": [cleaner.clean_cache_files()]}
    elif args.logs:
        results = {"timestamp": datetime.now().isoformat(), "dry_run": dry_run,
                   "categories": [cleaner.clean_log_files()]}
    elif args.recycle:
        results = {"timestamp": datetime.now().isoformat(), "dry_run": dry_run,
                   "categories": [cleaner.clean_recycle_bin()]}
    elif args.downloads:
        results = {"timestamp": datetime.now().isoformat(), "dry_run": dry_run,
                   "categories": [cleaner.clean_old_downloads(args.downloads)]}
    else:
        results = cleaner.clean_all()

    # Calculate summary if not already present
    if "summary" not in results:
        total_files = sum(c["locations"][0]["files_deleted"] for c in results["categories"])
        total_space = sum(c["locations"][0]["space_freed_mb"] for c in results["categories"])
        results["summary"] = {
            "total_files_deleted": total_files,
            "total_space_freed_mb": round(total_space, 2),
            "total_space_freed_gb": round(total_space / 1024, 2),
            "total_errors": 0
        }

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print_report(results)

    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n✅ Report saved to {args.output}")


if __name__ == "__main__":
    main()
