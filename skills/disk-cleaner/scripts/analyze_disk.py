#!/usr/bin/env python3
"""
Disk Space Analyzer - Cross-platform disk space analysis tool
Analyzes disk usage and identifies large files and directories

Enhanced with progress bars and performance optimizations.
"""

import json
import os
import platform
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# 使用智能引导模块导入 diskcleaner
try:
    # 添加当前脚本的父目录到路径，以便导入 skill_bootstrap
    script_dir = Path(__file__).parent.resolve()
    if str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))

    from skill_bootstrap import import_diskcleaner_modules, setup_skill_environment

    # 设置技能环境并导入模块
    IMPORT_SUCCESS, MODULES = import_diskcleaner_modules()
    PROGRESS_AVAILABLE = IMPORT_SUCCESS

    if IMPORT_SUCCESS:
        ProgressBar = MODULES["ProgressBar"]
        DirectoryScanner = MODULES["DirectoryScanner"]
    else:
        ProgressBar = None
        DirectoryScanner = None

except Exception as e:
    # 如果引导模块也失败，尝试直接导入（可能已安装）
    try:
        from diskcleaner.core.progress import ProgressBar
        from diskcleaner.core.scanner import DirectoryScanner

        PROGRESS_AVAILABLE = True
        print(f"[Warning] 技能包引导失败，使用已安装版本: {e}", file=sys.stderr)
    except ImportError:
        PROGRESS_AVAILABLE = False
        ProgressBar = None
        DirectoryScanner = None
        print(f"[Warning] 无法导入 diskcleaner 模块，部分功能将不可用: {e}", file=sys.stderr)


class DiskAnalyzer:
    def __init__(
        self,
        path: str = None,
        top_n: int = 20,
        show_progress: bool = True,
        max_files: int = None,
        max_seconds: int = None,
    ):
        self.path = path or self._get_default_path()
        self.top_n = top_n
        self.platform = platform.system()
        self.system = platform.system().lower()
        self.show_progress = show_progress and PROGRESS_AVAILABLE and sys.stdout.isatty()
        # 更合理的默认值，适合大磁盘
        self.max_files = max_files if max_files is not None else 50000
        self.max_seconds = max_seconds if max_seconds is not None else 30

    def _get_default_path(self) -> str:
        """Get default path based on platform"""
        system = platform.system()
        if system == "Windows":
            return "C:\\"
        elif system == "Darwin":  # macOS
            return "/"
        else:  # Linux
            return "/"

    def quick_sample(self, sample_time: float = 1.0) -> Dict:
        """
        快速采样分析 - 在1秒内估算目录特征

        Args:
            sample_time: 采样时间（秒）

        Returns:
            包含估算信息的字典
        """
        import time

        print(f"\n[*] 快速采样分析中... ({sample_time}秒)")

        file_count = 0
        total_size = 0
        sample_dirs = 0
        start = time.time()

        scan_path = Path(self.path)

        try:
            # 使用 os.scandir 进行快速采样
            for root, dirs, files in os.walk(str(scan_path)):
                if time.time() - start > sample_time:
                    break

                sample_dirs += len(dirs)
                file_count += len(files)

                # 采样文件大小（最多100个）
                for i, f in enumerate(files[:100]):
                    try:
                        file_path = Path(root) / f
                        if file_path.is_file():
                            total_size += file_path.stat().st_size
                    except (OSError, PermissionError):
                        pass

        except Exception as e:
            print(f"采样出错: {e}")

        elapsed = time.time() - start

        # 计算估算值
        if elapsed > 0:
            files_per_second = file_count / elapsed
        else:
            files_per_second = 0

        # 估算总时间（2倍安全边际）
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

        # 显示采样结果
        print("\n[i] 采样结果:")
        print(f"   发现文件: {file_count:,} 个")
        print(f"   目录数: {sample_dirs:,} 个")
        print(f"   扫描速度: {result['files_per_second']:,} 文件/秒")

        if estimated_seconds > 0:
            if estimated_seconds < 60:
                print(f"   预计完整扫描: {estimated_seconds:.0f} 秒")
            else:
                print(f"   预计完整扫描: {estimated_seconds/60:.1f} 分钟")

            if estimated_seconds > 120:  # 超过2分钟
                print("\n[i] 建议:")
                print("   使用 --file-limit 限制文件数")
                print("   使用 --time-limit 限制时间")
                print("   或者使用 --sample 仅查看采样结果")

        return result

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
        """
        Scan directory and find largest subdirectories and files.

        Uses optimized DirectoryScanner with progress bar if available.
        """
        scan_path = Path(path or self.path)
        results = {"directories": [], "files": []}

        try:
            # Use optimized scanner if available
            if PROGRESS_AVAILABLE:
                try:
                    # Use DirectoryScanner with progress tracking
                    # Use instance limits if provided, otherwise use sensible defaults
                    max_files = self.max_files if self.max_files is not None else 1000000
                    max_seconds = self.max_seconds if self.max_seconds is not None else 300

                    scanner = DirectoryScanner(
                        str(scan_path),
                        max_files=max_files,
                        max_seconds=max_seconds,
                        cache_enabled=False,  # Disable cache for one-time scan
                    )

                    print(f"\n[*] Scanning {scan_path}...")

                    # Collect all entries with progress
                    all_dirs = {}
                    all_files = []

                    for file_info in scanner.scan_generator():
                        if file_info.is_dir:
                            # Store directory info for later size calculation
                            all_dirs[file_info.path] = file_info
                        elif not file_info.is_dir and file_info.size > 10 * 1024 * 1024:
                            # Only track files > 10MB
                            all_files.append(
                                {
                                    "path": file_info.path,
                                    "name": file_info.name,
                                    "size_gb": round(file_info.size / (1024**3), 2),
                                    "size_mb": round(file_info.size / (1024**2), 2),
                                }
                            )

                    # Now calculate directory sizes (top-level only)
                    print("[i] Analyzing directory sizes...")
                    for dir_path, dir_info in all_dirs.items():
                        if Path(dir_path).parent == scan_path:
                            # Only immediate subdirectories
                            try:
                                size = self._get_dir_size_fast(Path(dir_path))
                                if size > 0:
                                    results["directories"].append(
                                        {
                                            "path": dir_path,
                                            "name": dir_info.name,
                                            "size_gb": round(size / (1024**3), 2),
                                            "size_mb": round(size / (1024**2), 2),
                                        }
                                    )
                            except (PermissionError, OSError):
                                pass

                    results["files"] = all_files

                    if scanner.stopped_early:
                        print(f"[!] Scan stopped early: {scanner.stop_reason}")

                except (PermissionError, OSError) as e:
                    # Fallback to old method if scanner fails
                    print(f"Scanner failed, using fallback method: {e}", file=sys.stderr)
                    return self._scan_directory_fallback(scan_path, max_depth)
            else:
                # Fallback to old method
                return self._scan_directory_fallback(scan_path, max_depth)

        except (PermissionError, OSError) as e:
            print(f"Error scanning {scan_path}: {e}", file=sys.stderr)

        # Sort by size
        results["directories"].sort(key=lambda x: x["size_gb"], reverse=True)
        results["files"].sort(key=lambda x: x["size_gb"], reverse=True)

        # Keep only top N
        results["directories"] = results["directories"][: self.top_n]
        results["files"] = results["files"][: self.top_n]

        return results

    def _scan_directory_fallback(self, scan_path: Path, max_depth: int = 3) -> Dict:
        """Fallback scanning method using Path.iterdir()"""
        results = {"directories": [], "files": []}

        try:
            # Count total items for progress bar
            if self.show_progress:
                items = list(scan_path.iterdir())
                progress = ProgressBar(len(items), prefix="Scanning")
            else:
                items = scan_path.iterdir()
                progress = None

            # Scan directories
            for item in items:
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

                if progress:
                    progress.update(1, item.name)

            if progress:
                progress.close()

        except (PermissionError, OSError) as e:
            print(f"Error scanning {scan_path}: {e}", file=sys.stderr)

        return results

    def _get_dir_size(self, path: Path, max_depth: int = 1) -> int:
        """Calculate directory size (legacy method, kept for compatibility)"""
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

    def _get_dir_size_fast(self, path: Path, max_depth: int = 1) -> int:
        """
        Calculate directory size using os.scandir() for better performance.

        This is 3-5x faster than the rglob() method.
        """
        total_size = 0

        try:
            # Use os.scandir() for better performance
            with os.scandir(path) as it:
                for entry in it:
                    try:
                        if entry.is_file(follow_symlinks=False):
                            total_size += entry.stat().st_size
                        elif entry.is_dir(follow_symlinks=False) and max_depth > 0:
                            # Recursively calculate subdirectory size
                            total_size += self._get_dir_size_fast(Path(entry.path), max_depth - 1)
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

        # Filter out empty paths, resolve to absolute paths, and deduplicate
        seen = set()
        unique_dirs = []
        for d in temp_dirs:
            if d and os.path.exists(d):
                # Resolve to real path to handle symlinks and relative paths
                real_path = os.path.realpath(d)
                if real_path not in seen:
                    seen.add(real_path)
                    unique_dirs.append(real_path)

        return unique_dirs

    def analyze_temp_files(self) -> Dict:
        """Analyze temporary file usage with progress bar"""
        temp_dirs = self.get_temp_directories()
        results = []

        if self.show_progress and len(temp_dirs) > 0:
            progress = ProgressBar(len(temp_dirs), prefix="Analyzing temp")
        else:
            progress = None

        for i, temp_dir in enumerate(temp_dirs):
            size = self._get_dir_size_fast(Path(temp_dir), max_depth=2)
            results.append(
                {
                    "path": temp_dir,
                    "size_gb": round(size / (1024**3), 2),
                    "size_mb": round(size / (1024**2), 2),
                }
            )

            if progress:
                progress.update(1, Path(temp_dir).name)

        if progress:
            progress.close()

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
    print(f"\n[i] Disk Usage ({usage['path']}):")
    print(f"  Total: {usage['total_gb']} GB")
    print(f"  Used:  {usage['used_gb']} GB ({usage['usage_percent']}%)")
    print(f"  Free:  {usage['free_gb']} GB")

    # Alert if low on space
    if usage["usage_percent"] > 90:
        print("  [!] WARNING: Disk critically full!")
    elif usage["usage_percent"] > 80:
        print("  [!] WARNING: Disk running low on space")

    # Temp directories
    print("\n[x] Temporary Directories:")
    for temp in report["temp_analysis"]["temp_directories"]:
        size_str = f"{temp['size_gb']} GB" if temp["size_gb"] > 0 else f"{temp['size_mb']} MB"
        print(f"  {temp['path']}: {size_str}")

    # Large directories
    if "scan_results" in report:
        print("\n[DIR] Largest Directories:")
        for i, d in enumerate(report["scan_results"]["directories"][:10], 1):
            size_str = f"{d['size_gb']} GB" if d["size_gb"] > 0 else f"{d['size_mb']} MB"
            print(f"  {i}. {d['name']}: {size_str}")

        print("\n[FILE] Largest Files:")
        for i, f in enumerate(report["scan_results"]["files"][:10], 1):
            size_str = f"{f['size_gb']} GB" if f["size_gb"] > 0 else f"{f['size_mb']} MB"
            print(f"  {i}. {f['name']}: {size_str}")

    print("\n" + "=" * 60)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Analyze disk space usage",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze current drive (C:\\ on Windows, / on Unix)
  python scripts/analyze_disk.py

  # Analyze specific path with default limits
  python scripts/analyze_disk.py --path "D:/Projects"

  # Analyze with custom limits for large drives
  python scripts/analyze_disk.py --path "D:/" --file-limit 2000000 --time-limit 600

  # Get top 50 largest items
  python scripts/analyze_disk.py --top 50

  # Output as JSON for automation
  python scripts/analyze_disk.py --json --output report.json
        """,
    )
    parser.add_argument("--path", "-p", help="Path to analyze", default=None)
    parser.add_argument("--top", "-n", type=int, default=20, help="Number of top items to show")
    parser.add_argument(
        "--file-limit",
        type=int,
        default=None,
        help="Maximum number of files to scan (default: 50000 for large disks)",
    )
    parser.add_argument(
        "--time-limit",
        type=int,
        default=None,
        help="Maximum scan time in seconds (default: 30 for large disks)",
    )
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Quick sample mode (1 second) to estimate scan time and directory characteristics",
    )
    parser.add_argument(
        "--progressive",
        action="store_true",
        help="Use progressive scanning with real-time feedback (recommended for large disks)",
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--output", "-o", help="Save report to file")
    parser.add_argument(
        "--no-progress", action="store_true", help="Disable progress bars (useful for scripting)"
    )

    args = parser.parse_args()

    show_progress = not args.no_progress and not args.json
    analyzer = DiskAnalyzer(
        path=args.path,
        top_n=args.top,
        show_progress=show_progress,
        max_files=args.file_limit,
        max_seconds=args.time_limit,
    )

    # 快速采样模式
    if args.sample:
        sample_result = analyzer.quick_sample(sample_time=1.0)
        if args.json:
            print(json.dumps(sample_result, indent=2))
        sys.exit(0)

    # 对于可能的大磁盘，先进行采样并询问
    if not args.json and not args.sample and not args.progressive:
        # 自动进行1秒采样
        sample_result = analyzer.quick_sample(sample_time=1.0)
        estimated_time = sample_result.get("estimated_time_seconds", 0)

        # 如果预计超过2分钟，建议使用限制
        if estimated_time > 120:
            print(f"\n[!] 预计完整扫描需要 {estimated_time/60:.1f} 分钟")
            print("\n[i] 建议使用以下选项之一:")
            print("   --sample         快速采样模式（1秒）")
            print("   --file-limit 10000  限制文件数")
            print("   --time-limit 30   限制时间（秒）")
            print("   --progressive    渐进式扫描")
            print("\n如需继续完整扫描，请按 Ctrl+C 并重新运行时添加相应参数")

    report = analyzer.generate_report()

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_report(report)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\n[OK] Report saved to {args.output}")


if __name__ == "__main__":
    main()
