#!/usr/bin/env python3
"""
Disk Cleaner 技能包诊断工具

用于快速检测技能包是否正常工作，并提供详细的诊断信息。
"""

import os
import sys
import platform
from pathlib import Path


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


def print_section(title: str):
    """打印分节标题"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print("=" * 60)


def print_check(name: str, status: bool, details: str = ""):
    """打印检查结果"""
    icon = "[OK]" if status else "[X]"
    print(f"{icon} {name}")
    if details:
        print(f"   {details}")


def check_python_version():
    """检查 Python 版本"""
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"

    # Python 3.7+ 是推荐的
    is_good = version >= (3, 7)
    is_excellent = version >= (3, 8)

    if is_excellent:
        print_check("Python 版本", True, f"v{version_str} (推荐)")
    elif is_good:
        print_check("Python 版本", True, f"v{version_str} (可用，建议升级到3.8+)")
    else:
        print_check("Python 版本", False, f"v{version_str} (需要3.7+)")

    return is_good


def check_platform():
    """检查操作系统"""
    system = platform.system()
    version = platform.version()
    print_check("操作系统", True, f"{system} {platform.release()}")
    return True


def check_skill_structure():
    """检查技能包文件结构"""
    print("\n[DIR] 检查技能包文件结构:")

    # 检测技能根目录
    script_dir = Path(__file__).parent.resolve()
    skill_root = script_dir.parent

    if not skill_root.exists():
        print_check("技能根目录", False, f"未找到: {skill_root}")
        return False

    print_check("技能根目录", True, str(skill_root))

    # 检查关键文件
    key_files = [
        ("SKILL.md", "技能说明文档"),
        ("scripts/analyze_disk.py", "磁盘分析脚本"),
        ("scripts/clean_disk.py", "清理脚本"),
        ("scripts/monitor_disk.py", "监控脚本"),
        ("scripts/skill_bootstrap.py", "引导模块"),
        ("diskcleaner/__init__.py", "核心模块"),
        ("diskcleaner/core/progress.py", "进度条模块"),
        ("diskcleaner/core/scanner.py", "扫描器模块"),
    ]

    all_ok = True
    for file_path, description in key_files:
        full_path = skill_root / file_path
        exists = full_path.exists()
        print_check(f"  {description}", exists, file_path if exists else "缺失")
        if not exists:
            all_ok = False

    return all_ok


def check_imports():
    """检查模块导入"""
    print("\n[PKG] 检查模块导入:")

    # 首先检查引导模块
    try:
        script_dir = Path(__file__).parent.resolve()
        if str(script_dir) not in sys.path:
            sys.path.insert(0, str(script_dir))

        from skill_bootstrap import get_bootstrap

        bootstrap = get_bootstrap()
        print_check("  引导模块", True, "skill_bootstrap.py")
    except ImportError as e:
        print_check("  引导模块", False, f"导入失败: {e}")
        return False

    # 设置环境
    success = bootstrap.setup_import_path()
    print_check("  环境设置", success, "模块路径配置" if success else "路径配置失败")

    if not success:
        return False

    # 尝试导入核心模块
    modules = [
        ("diskcleaner", "主模块"),
        ("diskcleaner.config", "配置模块"),
        ("diskcleaner.core.progress", "进度条"),
        ("diskcleaner.core.scanner", "扫描器"),
    ]

    all_ok = True
    for module_name, description in modules:
        try:
            __import__(module_name)
            print_check(f"  {description}", True, module_name)
        except ImportError as e:
            print_check(f"  {description}", False, f"{module_name}: {e}")
            all_ok = False

    return all_ok


def check_permissions():
    """检查文件权限"""
    print("\n[KEY] 检查文件权限:")

    # 检查是否有创建临时文件的权限
    try:
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", delete=True) as f:
            f.write("test")
        print_check("临时文件创建", True)
    except Exception as e:
        print_check("临时文件创建", False, str(e))
        return False

    # 检查目录读取权限
    script_dir = Path(__file__).parent.resolve()
    try:
        list(script_dir.iterdir())
        print_check("目录读取权限", True)
    except Exception as e:
        print_check("目录读取权限", False, str(e))
        return False

    return True


def check_scripts():
    """测试脚本是否能运行"""
    print("\n[TEST] 测试脚本运行:")

    script_dir = Path(__file__).parent.resolve()
    scripts = [
        "analyze_disk.py",
        "clean_disk.py",
        "monitor_disk.py",
    ]

    all_ok = True
    for script_name in scripts:
        script_path = script_dir / script_name
        if not script_path.exists():
            print_check(f"  {script_name}", False, "文件不存在")
            all_ok = False
            continue

        # 尝试编译脚本（检查语法）
        try:
            with open(script_path, "r", encoding="utf-8") as f:
                compile(f.read(), str(script_path), "exec")
            print_check(f"  {script_name}", True, "语法检查通过")
        except SyntaxError as e:
            print_check(f"  {script_name}", False, f"语法错误: {e}")
            all_ok = False
        except Exception as e:
            print_check(f"  {script_name}", False, f"检查失败: {e}")
            all_ok = False

    return all_ok


def main():
    """主诊断流程"""
    print_section("DISK CLEANER 技能包诊断工具")
    print(f"时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = []

    # 执行各项检查
    print_section("环境检查")
    results.append(("Python 版本", check_python_version()))
    results.append(("操作系统", check_platform()))

    results.append(("文件结构", check_skill_structure()))
    results.append(("模块导入", check_imports()))
    results.append(("文件权限", check_permissions()))
    results.append(("脚本测试", check_scripts()))

    # 总结
    print_section("诊断总结")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    print(f"\n通过: {passed}/{total}")

    for name, result in results:
        icon = "✅" if result else "❌"
        print(f"{icon} {name}")

    if passed == total:
        print(f"\n[*] 所有检查通过！技能包可以正常使用。")
        return 0
    else:
        print(f"\n[!] 发现 {total - passed} 个问题需要解决。")

        # 提供修复建议
        print_section("修复建议")

        if not results[2][1]:  # 文件结构失败
            print("\n[X] 文件结构问题:")
            print("   确保技能包已正确解压，包含以下结构:")
            print("   disk-cleaner/")
            print("   ├── SKILL.md")
            print("   ├── scripts/")
            print("   │   ├── analyze_disk.py")
            print("   │   ├── clean_disk.py")
            print("   │   ├── monitor_disk.py")
            print("   │   └── skill_bootstrap.py")
            print("   └── diskcleaner/")

        if not results[3][1]:  # 模块导入失败
            print("\n[X] 模块导入问题:")
            print("   尝试以下方法:")
            print("   1. 运行: python scripts/skill_bootstrap.py --test-import")
            print("   2. 设置 PYTHONPATH 环境变量")
            print("   3. 从技能包根目录运行脚本")

        if not results[5][1]:  # 脚本测试失败
            print("\n[X] 脚本问题:")
            print("   检查 Python 语法是否正确")
            print("   确保文件编码为 UTF-8")

        return 1


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="诊断 Disk Cleaner 技能包")
    parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")
    parser.add_argument("--fix", action="store_true", help="尝试自动修复问题")

    args = parser.parse_args()

    # 设置调试模式
    if args.verbose:
        os.environ["DISK_CLEANER_DEBUG"] = "true"

    sys.exit(main())
