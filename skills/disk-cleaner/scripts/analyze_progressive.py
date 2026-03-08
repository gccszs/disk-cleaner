#!/usr/bin/env python3
"""
渐进式磁盘分析工具 - Progressive Disk Analyzer

针对大磁盘优化的分析工具：
1. 快速采样估算（0.5-1秒）
2. 显示预计扫描时间
3. 渐进式显示结果
4. 可随时中断查看部分结果
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# 使用智能引导模块导入
try:
    script_dir = Path(__file__).parent.resolve()
    if str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))

    from skill_bootstrap import init_console, safe_print, setup_skill_environment

    # 初始化控制台编码
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
    """渐进式磁盘分析器 - 提供实时反馈和早期结果"""

    def __init__(self, target_path: str = None):
        self.target_path = Path(target_path or self._get_default_path()).resolve()
        self.platform = sys.platform
        self.results_shown = 0
        self.start_time = None
        self.last_update_time = 0

    def _get_default_path(self) -> str:
        """获取默认扫描路径"""
        if sys.platform == "Windows":
            return "C:\\"
        else:
            return "/"

    def quick_sample(self, sample_time: float = 1.0) -> Dict:
        """
        快速采样分析 - 1秒内估算目录特征

        Returns:
            包含估算信息的字典
        """
        safe_print(f"\n[*] 快速采样分析中... ({sample_time}秒)")

        file_count = 0
        total_size = 0
        sample_dirs = 0
        start = time.time()

        try:
            # 使用 os.scandir 进行快速采样
            for root, dirs, files in os.walk(str(self.target_path)):
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
            safe_print(f"采样出错: {e}")

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
        safe_print("\n[i] 采样结果:")
        safe_print(f"   发现文件: {file_count:,} 个")
        safe_print(f"   目录数: {sample_dirs:,} 个")
        safe_print(f"   扫描速度: {result['files_per_second']:,} 文件/秒")

        if estimated_seconds > 0:
            if estimated_seconds < 60:
                safe_print(f"   预计完整扫描: {estimated_seconds:.0f} 秒")
            else:
                safe_print(f"   预计完整扫描: {estimated_seconds/60:.1f} 分钟")

        return result

    def progressive_scan(
        self, max_files: int = None, max_seconds: int = None, show_progress: bool = True
    ) -> Dict:
        """
        渐进式扫描 - 实时显示结果

        Args:
            max_files: 最大文件数限制
            max_seconds: 最大时间限制（秒）
            show_progress: 是否显示进度

        Returns:
            扫描结果字典
        """
        if DirectoryScanner is None:
            safe_print("[X] 高级扫描功能不可用，使用基础方法")
            return self._basic_scan()

        # 设置限制
        if max_files is None:
            max_files = 50000  # 默认5万文件
        if max_seconds is None:
            max_seconds = 30  # 默认30秒

        safe_print("\n[*] 渐进式扫描启动")
        safe_print(f"   限制: {max_files:,} 文件或 {max_seconds} 秒")
        safe_print("   按 Ctrl+C 随时中断查看部分结果\n")

        self.start_time = time.time()
        results = {"directories": [], "files": [], "scanned": 0}

        try:
            scanner = DirectoryScanner(
                str(self.target_path),
                max_files=max_files,
                max_seconds=max_seconds,
                cache_enabled=False,
            )

            # 使用生成器进行渐进式处理
            file_count = 0
            last_display_time = 0
            display_interval = 2.0  # 每2秒显示一次进度

            for file_info in scanner.scan_generator():
                file_count += 1
                elapsed = time.time() - self.start_time

                # 渐进式显示进度
                if show_progress and elapsed - last_display_time > display_interval:
                    self._show_progress(file_count, elapsed, scanner.stopped_early)
                    last_display_time = elapsed

                # 收集大文件（>10MB）
                if not file_info.is_dir and file_info.size > 10 * 1024 * 1024:
                    results["files"].append(
                        {
                            "path": file_info.path,
                            "name": file_info.name,
                            "size_gb": round(file_info.size / (1024**3), 2),
                            "size_mb": round(file_info.size / (1024**2), 2),
                        }
                    )

                # 收集目录（仅顶层）
                if file_info.is_dir and Path(file_info.path).parent == self.target_path:
                    results["directories"].append(
                        {
                            "path": file_info.path,
                            "name": file_info.name,
                        }
                    )

            # 扫描完成
            elapsed = time.time() - self.start_time
            self._show_progress(file_count, elapsed, True)

            # 计算目录大小
            results["directories"] = self._calculate_dir_sizes(results["directories"][:20])

            # 排序并限制结果数量
            results["files"].sort(key=lambda x: x["size_gb"], reverse=True)
            results["directories"].sort(key=lambda x: x["size_gb"], reverse=True)

            results["files"] = results["files"][:50]
            results["directories"] = results["directories"][:50]

            # 添加扫描信息
            results["scan_info"] = {
                "files_scanned": file_count,
                "scan_time_seconds": round(elapsed, 1),
                "stopped_early": scanner.stopped_early,
                "stop_reason": scanner.stop_reason if scanner.stopped_early else "",
            }

        except KeyboardInterrupt:
            safe_print("\n\n[!] 扫描被用户中断")
            elapsed = time.time() - self.start_time
            safe_print(f"   已扫描: {results.get('scanned', 0):,} 文件")
            safe_print(f"   用时: {elapsed:.1f} 秒")

        except Exception as e:
            safe_print(f"\n[X] 扫描出错: {e}")
            return self._basic_scan()

        return results

    def _show_progress(self, file_count: int, elapsed: float, complete: bool = False):
        """显示扫描进度"""
        if complete:
            safe_print(f"\n[OK] 扫描完成: {file_count:,} 文件, {elapsed:.1f} 秒")
        else:
            safe_print(f"   正在扫描: {file_count:,} 文件, {elapsed:.1f} 秒... (继续)")

    def _calculate_dir_sizes(self, dirs: List[Dict], max_depth: int = 1) -> List[Dict]:
        """计算目录大小"""
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
        """快速计算目录大小"""
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
        """基础扫描方法（当高级功能不可用时）"""
        safe_print("\n使用基础扫描方法...")

        results = {"directories": [], "files": []}
        file_count = 0

        try:
            # 只扫描顶层
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
            safe_print(f"基础扫描也失败了: {e}")

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
        """格式化报告"""
        lines = []
        lines.append("\n" + "=" * 60)
        lines.append(f"DISK ANALYSIS REPORT - {self.target_path}")
        lines.append("=" * 60)

        # 扫描信息
        if "scan_info" in results:
            info = results["scan_info"]
            lines.append("\n[i] Scan Info:")
            lines.append(f"   Files scanned: {info.get('files_scanned', 0):,}")
            lines.append(f"   Time: {info.get('scan_time_seconds', 0):.1f} seconds")
            if info.get("stopped_early"):
                lines.append(f"   Stopped early: {info.get('stop_reason', 'Unknown')}")

        # 大目录
        if results.get("directories"):
            lines.append("\n[DIR] Largest Directories:")
            for i, d in enumerate(results["directories"][:20], 1):
                size_str = f"{d['size_gb']} GB" if d["size_gb"] > 0 else f"{d['size_mb']} MB"
                lines.append(f"   {i}. {d['name']}: {size_str}")

        # 大文件
        if results.get("files"):
            lines.append("\n[FILE] Largest Files:")
            for i, f in enumerate(results["files"][:20], 1):
                size_str = f"{f['size_gb']} GB" if f["size_gb"] > 0 else f"{f['size_mb']} MB"
                # 缩短路径
                path_str = f"...{f['path'][-50:]}" if len(f["path"]) > 50 else f["path"]
                lines.append(f"   {i}. {f['name']}: {size_str}")
                lines.append(f"      {path_str}")

        lines.append("\n" + "=" * 60)
        return "\n".join(lines)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="渐进式磁盘分析工具 - 适合大磁盘",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 快速采样（1秒）
  python scripts/analyze_progressive.py --sample

  # 渐进式扫描（30秒限制）
  python scripts/analyze_progressive.py --max-seconds 30

  # 限制文件数（快速）
  python scripts/analyze_progressive.py --max-files 10000

  # 完整扫描（长时间）
  python scripts/analyze_progressive.py --max-seconds 300

  # 自定义路径
  python scripts/analyze_progressive.py --path "D:\\Projects" --sample
        """,
    )

    parser.add_argument("--path", "-p", help="扫描路径")
    parser.add_argument("--sample", action="store_true", help="仅快速采样（1秒）")
    parser.add_argument("--max-files", type=int, default=50000, help="最大文件数限制（默认: 50000）")
    parser.add_argument("--max-seconds", type=int, default=30, help="最大时间限制-秒（默认: 30）")
    parser.add_argument("--json", action="store_true", help="JSON输出")
    parser.add_argument("--no-progress", action="store_true", help="不显示进度")

    args = parser.parse_args()

    analyzer = ProgressiveDiskAnalyzer(args.path)

    # 快速采样模式
    if args.sample:
        sample_result = analyzer.quick_sample(sample_time=1.0)

        if args.json:
            print(json.dumps(sample_result, indent=2))
        return 0

    # 先进行快速采样
    sample_result = analyzer.quick_sample(sample_time=1.0)

    # 询问是否继续
    estimated_time = sample_result.get("estimated_time_seconds", 0)
    if estimated_time > 60:  # 超过1分钟
        safe_print(f"\n[!] 预计扫描需要 {estimated_time/60:.1f} 分钟")
        safe_print("建议:")
        safe_print("   1. 使用 --sample 快速采样模式")
        safe_print("   2. 使用 --max-seconds 降低时间限制")
        safe_print("   3. 使用 --max-files 限制文件数量")

        # 非交互模式，直接返回
        if args.json:
            print(json.dumps({"sample": sample_result}, indent=2))
        return 0

    # 渐进式扫描
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
        safe_print("\n\n[*] 用户中断")
        sys.exit(0)
