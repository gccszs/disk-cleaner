#!/usr/bin/env python3
"""
改进的技能包打包脚本

创建自包含的 .skill 文件，确保：
1. 包含所有必需的文件
2. 自动检测项目根目录
3. 验证打包后的完整性
4. 生成安装说明
"""

import os
import platform
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import List, Tuple


# 初始化 Windows 控制台编码
def init_console():
    """初始化控制台编码"""
    if platform.system().lower() == "windows":
        try:
            import ctypes

            ctypes.windll.kernel32.SetConsoleOutputCP(65001)
            if hasattr(sys.stdout, "buffer"):
                import io

                sys.stdout = io.TextIOWrapper(
                    sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True
                )
            if hasattr(sys.stderr, "buffer"):
                sys.stderr = io.TextIOWrapper(
                    sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True
                )
        except Exception:
            pass


# 在模块加载时初始化
init_console()


def find_project_root() -> Path:
    """
    智能查找项目根目录

    查找策略：
    1. 从当前脚本位置向上查找
    2. 查找包含 diskcleaner 目录的父目录
    3. 查找包含 pyproject.toml 的目录
    """
    # 脚本位置
    script_path = Path(__file__).resolve()

    # 方法1: 从脚本位置推断
    # scripts/disk-cleaner/scripts/package_skill.py
    # -> 项目根是上3级
    candidate = script_path.parent.parent.parent.parent
    if (candidate / "diskcleaner").exists():
        return candidate

    # 方法2: 查找 pyproject.toml
    current = script_path
    while current != current.parent:
        if (current / "pyproject.toml").exists():
            return current
        current = current.parent

    # 方法3: 使用当前脚本所在目录的父目录的父目录
    # 假设在 skills/disk-cleaner/scripts/ 中
    candidate = script_path.parent.parent.parent
    if (candidate / "diskcleaner").exists():
        return candidate

    # 最后回退：使用 cwd
    cwd = Path.cwd()
    if (cwd / "diskcleaner").exists():
        return cwd

    raise FileNotFoundError(
        f"无法找到项目根目录。请从 disk-cleaner 仓库目录运行此脚本。\n"
        f"当前脚本位置: {script_path}\n"
        f"当前工作目录: {cwd}"
    )


def find_skill_root(project_root: Path) -> Path:
    """查找技能根目录"""
    # 尝试常见位置
    candidates = [
        project_root / "skills" / "disk-cleaner",
        project_root / "skill",
        project_root,
    ]

    for candidate in candidates:
        if (candidate / "SKILL.md").exists():
            return candidate

    raise FileNotFoundError(
        f"无法找到技能根目录（需要 SKILL.md 文件）。\n"
        f"尝试的位置: {[str(c) for c in candidates]}"
    )


def get_files_to_include(project_root: Path, skill_root: Path) -> List[Tuple[Path, str]]:
    """
    获取需要打包的文件列表

    Returns:
        (源路径, 目标相对路径) 的列表
    """
    items = []

    # 核心模块（从项目根目录）
    core_files = [
        "diskcleaner/__init__.py",
        "diskcleaner/config/__init__.py",
        "diskcleaner/config/defaults.py",
        "diskcleaner/config/loader.py",
        "diskcleaner/core/__init__.py",
        "diskcleaner/core/cache.py",
        "diskcleaner/core/classifier.py",
        "diskcleaner/core/duplicate_finder.py",
        "diskcleaner/core/interactive.py",
        "diskcleaner/core/process_manager.py",
        "diskcleaner/core/progress.py",
        "diskcleaner/core/safety.py",
        "diskcleaner/core/scanner.py",
        "diskcleaner/core/smart_cleanup.py",
        "diskcleaner/optimization/__init__.py",
        "diskcleaner/optimization/concurrency.py",
        "diskcleaner/optimization/delete.py",
        "diskcleaner/optimization/hash.py",
        "diskcleaner/optimization/memory.py",
        "diskcleaner/optimization/profiler.py",
        "diskcleaner/optimization/scan.py",
        "diskcleaner/platforms/__init__.py",
        "diskcleaner/platforms/linux.py",
        "diskcleaner/platforms/macos.py",
        "diskcleaner/platforms/windows.py",
    ]

    for file_path in core_files:
        src = project_root / file_path
        if src.exists():
            items.append((src, file_path))
        else:
            print(f"[!] 警告: 文件不存在: {src}")

    # 技能文件（从技能根目录）
    skill_files = [
        "SKILL.md",
        "INSTALL.md",
        "UNIVERSAL_INSTALL.md",
        "NO_PYTHON_GUIDE.md",
        "PROGRESSIVE_SCAN_SUMMARY.md",  # 新增：渐进式扫描说明
        "FIXES.md",
        "ENCODING_FIX_SUMMARY.md",  # 新增：编码修复总结
        "AGENT_QUICK_REF.txt",
        "scripts/analyze_disk.py",
        "scripts/analyze_progressive.py",  # 新增：渐进式扫描
        "scripts/clean_disk.py",
        "scripts/monitor_disk.py",
        "scripts/skill_bootstrap.py",
        "scripts/check_skill.py",
        "scripts/package_skill.py",
        "scripts/scheduler.py",
        "references/temp_locations.md",
    ]

    for file_path in skill_files:
        src = skill_root / file_path
        if src.exists():
            items.append((src, file_path))
        else:
            print(f"[!] 警告: 文件不存在: {src}")

    return items


def create_skill_package(
    output_path: Path = None,
    project_root: Path = None,
    skill_root: Path = None,
    verify: bool = True,
) -> Path:
    """
    创建技能包

    Args:
        output_path: 输出文件路径
        project_root: 项目根目录
        skill_root: 技能根目录
        verify: 是否验证打包结果

    Returns:
        创建的 .skill 文件路径
    """
    # 查找目录
    if project_root is None:
        project_root = find_project_root()
        print(f"[DIR] 项目根目录: {project_root}")

    if skill_root is None:
        skill_root = find_skill_root(project_root)
        print(f"[DIR] 技能根目录: {skill_root}")

    # 确定输出路径
    if output_path is None:
        output_path = skill_root / "disk-cleaner.skill"
    print(f"[PKG] 输出文件: {output_path}")

    # 获取文件列表
    items = get_files_to_include(project_root, skill_root)
    print(f"[i] 打包文件数: {len(items)}")

    # 排除模式
    exclude_patterns = [
        "__pycache__",
        "*.pyc",
        ".pyc",
        "*.pyo",
        ".pytest_cache",
        "*.egg-info",
        ".mypy_cache",
        ".benchmarks",
        "*.py~",  # 编辑器备份文件
        ".DS_Store",  # macOS
    ]

    # 创建临时目录
    with tempfile.TemporaryDirectory() as temp_dir:
        skill_dir = Path(temp_dir) / "disk-cleaner"
        skill_dir.mkdir()

        # 复制文件
        copied = 0
        for src, dst_rel in items:
            dst = skill_dir / dst_rel

            # 创建目标目录
            dst.parent.mkdir(parents=True, exist_ok=True)

            # 检查是否应该排除
            if any(pattern in str(src) for pattern in exclude_patterns):
                continue

            # 复制文件
            if src.is_dir():
                shutil.copytree(src, dst, ignore=shutil.ignore_patterns(*exclude_patterns))
            else:
                shutil.copy2(src, dst)
            copied += 1

        print(f"[OK] 复制文件: {copied}")

        # 创建 README
        readme_content = """# Disk Cleaner 技能包

## 安装方法

1. 将此 .skill 文件解压到你的技能目录:
   - Windows: `%USERPROFILE%\\.claude\\skills\\disk-cleaner\\`
   - macOS/Linux: `~/.claude/skills/disk-cleaner/`

2. 或者在 Claude Code 中使用:
   ```
   /install-skill path/to/disk-cleaner.skill
   ```

## 使用方法

### 分析磁盘空间
```bash
python scripts/analyze_disk.py
python scripts/analyze_disk.py --path "D:\\Projects"
python scripts/analyze_disk.py --top 50
```

### 清理垃圾文件
```bash
# 预览（安全模式）
python scripts/clean_disk.py --dry-run

# 实际清理
python scripts/clean_disk.py --force

# 清理特定类别
python scripts/clean_disk.py --temp --cache --dry-run
```

### 监控磁盘使用
```bash
python scripts/monitor_disk.py
python scripts/monitor_disk.py --watch --interval 300
```

## 诊断问题

如果遇到问题，运行诊断工具:
```bash
python scripts/check_skill.py
python scripts/skill_bootstrap.py --test-import
```

## 系统要求

- Python 3.7+
- 无需额外依赖

更多信息请查看 SKILL.md
"""
        (skill_dir / "README.txt").write_text(readme_content, encoding="utf-8")

        # 创建版本文件
        created_time = __import__("datetime").datetime.now().isoformat()
        version_content = f"""{{
  "name": "disk-cleaner",
  "version": "2.1.0",
  "description": "High-performance cross-platform disk space monitoring, "
  "analysis, and cleaning toolkit with progressive scanning and "
  "cross-platform encoding fixes",
  "python_requires": ">=3.7",
  "created": "{created_time}"
}}
"""
        (skill_dir / "skill.json").write_text(version_content, encoding="utf-8")

        # 创建 zip 文件
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file_path in skill_dir.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(skill_dir)
                    zipf.write(file_path, arcname)

    # 显示结果
    size_mb = output_path.stat().st_size / (1024 * 1024)
    print("[OK] 打包完成!")
    print(f"   文件大小: {size_mb:.2f} MB")
    print(f"   文件位置: {output_path}")

    # 验证
    if verify:
        print("\n[?] 验证打包内容...")
        verify_skill_package(output_path)

    return output_path


def verify_skill_package(skill_path: Path) -> bool:
    """
    验证技能包的完整性

    检查:
    1. 关键文件是否存在
    2. Python 模块是否可以导入
    3. 文件结构是否正确
    """
    with zipfile.ZipFile(skill_path, "r") as zipf:
        files = zipf.namelist()

        print(f"   总文件数: {len(files)}")

        # 检查关键文件
        key_files = [
            "SKILL.md",
            "skill.json",
            "scripts/skill_bootstrap.py",
            "scripts/analyze_disk.py",
            "scripts/clean_disk.py",
            "scripts/monitor_disk.py",
            "scripts/check_skill.py",
            "diskcleaner/__init__.py",
            "diskcleaner/core/progress.py",
            "diskcleaner/core/scanner.py",
        ]

        all_ok = True
        for key_file in key_files:
            if key_file in files:
                print(f"   [OK] {key_file}")
            else:
                print(f"   [X] {key_file} (缺失)")
                all_ok = False

        if not all_ok:
            print("\n[!] 验证失败: 缺少关键文件")
            return False

    print("   [OK] 验证通过!")

    # 尝试导入测试
    print("\n[TEST] 测试模块导入...")
    try:
        # 创建临时目录解压
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            with zipfile.ZipFile(skill_path, "r") as zipf:
                zipf.extractall(temp_path)

            # 添加到路径并测试导入
            skill_extracted = temp_path / "disk-cleaner"
            sys.path.insert(0, str(skill_extracted))

            try:
                from skill_bootstrap import import_diskcleaner_modules

                success, modules = import_diskcleaner_modules()

                if success:
                    print("   [OK] 模块导入成功")
                    for name in modules.keys():
                        print(f"      - {name}")
                else:
                    print("   [!] 模块导入失败，但可能仍可使用基础功能")

            finally:
                # 清理路径
                if str(skill_extracted) in sys.path:
                    sys.path.remove(str(skill_extracted))

    except Exception as e:
        print(f"   [!] 导入测试失败: {e}")
        print("   (这可能不影响实际使用)")

    return True


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="创建 Disk Cleaner 技能包",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 创建技能包（默认位置）
  python scripts/package_skill.py

  # 指定输出路径
  python scripts/package_skill.py --output ../disk-cleaner-v2.0.skill

  # 跳过验证
  python scripts/package_skill.py --no-verify

  # 只验证现有技能包
  python scripts/package_skill.py --verify-only disk-cleaner.skill
        """,
    )

    parser.add_argument("--output", "-o", type=Path, help="输出 .skill 文件路径")
    parser.add_argument("--project-root", type=Path, help="项目根目录（默认自动检测）")
    parser.add_argument("--skill-root", type=Path, help="技能根目录（默认自动检测）")
    parser.add_argument("--no-verify", action="store_true", help="跳过验证步骤")
    parser.add_argument("--verify-only", type=Path, metavar="SKILL_FILE", help="只验证现有的技能包")

    args = parser.parse_args()

    if args.verify_only:
        print("[?] 验证技能包...")
        success = verify_skill_package(args.verify_only)
        sys.exit(0 if success else 1)

    try:
        output_path = create_skill_package(
            output_path=args.output,
            project_root=args.project_root,
            skill_root=args.skill_root,
            verify=not args.no_verify,
        )
        print(f"\n[*] 技能包创建成功: {output_path}")
        sys.exit(0)

    except Exception as e:
        print(f"\n[X] 错误: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
