#!/usr/bin/env python3
"""
Disk Cleaner Skill Package Diagnostic Tool

Quickly detect if skill package is working correctly and provide detailed diagnostic information.
"""

import os
import platform
import sys
from pathlib import Path


# Initialize Windows console encoding
def init_console():
    """Initialize console encoding"""
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


# Initialize at module load time
init_console()


def print_section(title: str):
    """Print section title"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print("=" * 60)


def print_check(name: str, status: bool, details: str = ""):
    """Print check result"""
    icon = "[OK]" if status else "[X]"
    print(f"{icon} {name}")
    if details:
        print(f"   {details}")


def check_python_version():
    """Check Python version"""
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"

    # Python 3.7+ is recommended
    is_good = version >= (3, 7)
    is_excellent = version >= (3, 8)

    if is_excellent:
        print_check("Python Version", True, f"v{version_str} (recommended)")
    elif is_good:
        print_check("Python Version", True, f"v{version_str} (usable, recommend upgrading to 3.8+)")
    else:
        print_check("Python Version", False, f"v{version_str} (requires 3.7+)")

    return is_good


def check_platform():
    """Check operating system"""
    system = platform.system()
    version = platform.version()
    print_check("Operating System", True, f"{system} {platform.release()}")
    return True


def check_skill_structure():
    """Check skill package file structure"""
    print("\n[DIR] Checking skill package file structure:")

    # Detect skill root
    script_dir = Path(__file__).parent.resolve()
    skill_root = script_dir.parent

    if not skill_root.exists():
        print_check("Skill Root", False, f"Not found: {skill_root}")
        return False

    print_check("Skill Root", True, str(skill_root))

    # Check key files
    key_files = [
        ("SKILL.md", "Skill documentation"),
        ("scripts/analyze_disk.py", "Disk analysis script"),
        ("scripts/clean_disk.py", "Cleaning script"),
        ("scripts/monitor_disk.py", "Monitoring script"),
        ("scripts/skill_bootstrap.py", "Bootstrap module"),
        ("diskcleaner/__init__.py", "Core module"),
        ("diskcleaner/core/progress.py", "Progress bar module"),
        ("diskcleaner/core/scanner.py", "Scanner module"),
    ]

    all_ok = True
    for file_path, description in key_files:
        full_path = skill_root / file_path
        exists = full_path.exists()
        print_check(f"  {description}", exists, file_path if exists else "missing")
        if not exists:
            all_ok = False

    return all_ok


def check_imports():
    """Check module imports"""
    print("\n[PKG] Checking module imports:")

    # First check bootstrap module
    try:
        script_dir = Path(__file__).parent.resolve()
        if str(script_dir) not in sys.path:
            sys.path.insert(0, str(script_dir))

        from skill_bootstrap import get_bootstrap

        bootstrap = get_bootstrap()
        print_check("  Bootstrap Module", True, "skill_bootstrap.py")
    except ImportError as e:
        print_check("  Bootstrap Module", False, f"Import failed: {e}")
        return False

    # Setup environment
    success = bootstrap.setup_import_path()
    print_check("  Environment Setup", success, "Module path configured" if success else "Path configuration failed")

    if not success:
        return False

    # Try importing core modules
    modules = [
        ("diskcleaner", "Main module"),
        ("diskcleaner.config", "Config module"),
        ("diskcleaner.core.progress", "Progress bar"),
        ("diskcleaner.core.scanner", "Scanner"),
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
    """Check file permissions"""
    print("\n[KEY] Checking file permissions:")

    # Check if have permission to create temp files
    try:
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", delete=True) as f:
            f.write("test")
        print_check("Temp File Creation", True)
    except Exception as e:
        print_check("Temp File Creation", False, str(e))
        return False

    # Check directory read permission
    script_dir = Path(__file__).parent.resolve()
    try:
        list(script_dir.iterdir())
        print_check("Directory Read Permission", True)
    except Exception as e:
        print_check("Directory Read Permission", False, str(e))
        return False

    return True


def check_scripts():
    """Test if scripts can run"""
    print("\n[TEST] Testing script execution:")

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
            print_check(f"  {script_name}", False, "File does not exist")
            all_ok = False
            continue

        # Try compiling script (check syntax)
        try:
            with open(script_path, "r", encoding="utf-8") as f:
                compile(f.read(), str(script_path), "exec")
            print_check(f"  {script_name}", True, "Syntax check passed")
        except SyntaxError as e:
            print_check(f"  {script_name}", False, f"Syntax error: {e}")
            all_ok = False
        except Exception as e:
            print_check(f"  {script_name}", False, f"Check failed: {e}")
            all_ok = False

    return all_ok


def main():
    """Main diagnostic flow"""
    print_section("DISK CLEANER SKILL PACKAGE DIAGNOSTIC TOOL")
    print(f"Time: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = []

    # Execute various checks
    print_section("Environment Check")
    results.append(("Python Version", check_python_version()))
    results.append(("Operating System", check_platform()))

    results.append(("File Structure", check_skill_structure()))
    results.append(("Module Import", check_imports()))
    results.append(("File Permissions", check_permissions()))
    results.append(("Script Test", check_scripts()))

    # Summary
    print_section("Diagnostic Summary")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    print(f"\nPassed: {passed}/{total}")

    for name, result in results:
        icon = "[OK]" if result else "[X]"
        print(f"{icon} {name}")

    if passed == total:
        print("\n[*] All checks passed! Skill package can be used normally.")
        return 0
    else:
        print(f"\n[!] Found {total - passed} issue(s) that need to be resolved.")

        # Provide fix suggestions
        print_section("Fix Suggestions")

        if not results[2][1]:  # File structure failed
            print("\n[X] File structure issues:")
            print("   Ensure skill package is correctly extracted with the following structure:")
            print("   disk-cleaner/")
            print("   ├── SKILL.md")
            print("   ├── scripts/")
            print("   │   ├── analyze_disk.py")
            print("   │   ├── clean_disk.py")
            print("   │   ├── monitor_disk.py")
            print("   │   └── skill_bootstrap.py")
            print("   └── diskcleaner/")

        if not results[3][1]:  # Module import failed
            print("\n[X] Module import issues:")
            print("   Try the following methods:")
            print("   1. Run: python scripts/skill_bootstrap.py --test-import")
            print("   2. Set PYTHONPATH environment variable")
            print("   3. Run scripts from skill package root directory")

        if not results[5][1]:  # Script test failed
            print("\n[X] Script issues:")
            print("   Check if Python syntax is correct")
            print("   Ensure file encoding is UTF-8")

        return 1


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Diagnose Disk Cleaner skill package")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed information")
    parser.add_argument("--fix", action="store_true", help="Try to automatically fix issues")

    args = parser.parse_args()

    # Set debug mode
    if args.verbose:
        os.environ["DISK_CLEANER_DEBUG"] = "true"

    sys.exit(main())
