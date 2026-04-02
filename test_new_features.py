#!/usr/bin/env python3
"""
Test script for new features: Duplicate Finder and Growth Analyzer

This script tests the newly implemented features to ensure they work correctly.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_duplicate_finder():
    """Test duplicate file finder"""
    print("\n" + "=" * 60)
    print("Testing Duplicate File Finder")
    print("=" * 60)

    try:
        from diskcleaner.core.scanner import FileInfo
        from diskcleaner.core.duplicate_finder import DuplicateFinder

        # Create test files in temp directory
        temp_dir = tempfile.mkdtemp(prefix="diskcleaner_test_")
        print(f"\n[*] Created test directory: {temp_dir}")

        try:
            # Create test files
            test_file1 = Path(temp_dir) / "test1.txt"
            test_file2 = Path(temp_dir) / "test2.txt"
            test_file3 = Path(temp_dir) / "test3.txt"

            # Write same content to test1 and test2 (duplicates)
            content = b"This is test content for duplicate detection" * 100
            test_file1.write_bytes(content)
            test_file2.write_bytes(content)

            # Write different content to test3
            test_file3.write_bytes(b"Different content" * 100)

            print("[*] Created 3 test files (2 duplicates, 1 unique)")

            # Create FileInfo objects
            files = [
                FileInfo(
                    path=str(test_file1),
                    name="test1.txt",
                    size=test_file1.stat().st_size,
                    is_dir=False,
                    is_link=False,
                    mtime=test_file1.stat().st_mtime,
                ),
                FileInfo(
                    path=str(test_file2),
                    name="test2.txt",
                    size=test_file2.stat().st_size,
                    is_dir=False,
                    is_link=False,
                    mtime=test_file2.stat().st_mtime,
                ),
                FileInfo(
                    path=str(test_file3),
                    name="test3.txt",
                    size=test_file3.stat().st_size,
                    is_dir=False,
                    is_link=False,
                    mtime=test_file3.stat().st_mtime,
                ),
            ]

            # Test duplicate finder
            finder = DuplicateFinder(strategy="accurate")
            duplicates = finder.find_duplicates(files)

            print(f"\n[OK] Found {len(duplicates)} duplicate group(s)")

            if len(duplicates) == 1:
                group = duplicates[0]
                print(f"  Files in group: {group.count}")
                print(f"  File size: {group.size} bytes")
                print(f"  Reclaimable space: {group.reclaimable_space} bytes")
                print("[OK] Duplicate finder working correctly!")
                return True
            else:
                print("[!] Expected 1 duplicate group, found", len(duplicates))
                return False

        finally:
            # Cleanup
            shutil.rmtree(temp_dir)
            print(f"\n[*] Cleaned up test directory")

    except Exception as e:
        print(f"[!] Error testing duplicate finder: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_growth_analyzer():
    """Test growth analyzer"""
    print("\n" + "=" * 60)
    print("Testing Growth Analyzer")
    print("=" * 60)

    try:
        from diskcleaner.core.growth_analyzer import GrowthAnalyzer

        # Create temp data file
        temp_file = tempfile.mktemp(suffix="_growth_test.json")

        try:
            # Initialize analyzer
            analyzer = GrowthAnalyzer(data_file=temp_file)
            print(f"\n[*] Created analyzer with data file: {temp_file}")

            # Add test snapshots
            import time
            from datetime import datetime, timedelta

            base_time = datetime.now() - timedelta(days=10)

            for i in range(10):
                # Simulate growing disk usage
                used_bytes = 100 * (1024**3) + (i * 1024**3 * 1024)  # 100GB + growth
                total_bytes = 500 * (1024**3)  # 500GB
                free_bytes = total_bytes - used_bytes

                # Add snapshot with custom timestamp
                snapshot = {
                    "timestamp": (base_time + timedelta(days=i)).isoformat(),
                    "path": "/test",
                    "used_bytes": used_bytes,
                    "total_bytes": total_bytes,
                    "free_bytes": free_bytes,
                    "used_percent": round((used_bytes / total_bytes * 100), 2),
                    "platform": "Linux",
                }

                analyzer.history["snapshots"].append(snapshot)

            # Save history
            analyzer._save_history()
            print("[*] Added 10 test snapshots")

            # Test growth rate calculation
            daily_rate = analyzer.calculate_growth_rate(path="/test", period="daily")

            if "error" not in daily_rate:
                print(f"\n[OK] Daily growth rate calculated:")
                print(f"  Average growth: {daily_rate['avg_growth_mb_per_period']:.2f} MB/day")
                print(f"  Trend: {daily_rate.get('trend', 'unknown')}")
            else:
                print(f"[!] Error calculating growth rate: {daily_rate['error']}")
                return False

            # Test prediction
            prediction = analyzer.predict_full_date(path="/test")

            if "error" not in prediction:
                print(f"\n[OK] Prediction calculated:")
                print(f"  Days until full: {prediction['days_until_full']:.0f}")
                print(f"  Predicted full date: {prediction['predicted_full_date_human']}")
            else:
                print(f"[!] Error making prediction: {prediction['error']}")
                return False

            # Test report generation
            report = analyzer.generate_report(path="/test")

            if "error" not in report:
                print(f"\n[OK] Report generated successfully")
                print(f"  Snapshots analyzed: {report['snapshots_count']}")
                print("[OK] Growth analyzer working correctly!")
                return True
            else:
                print(f"[!] Error generating report: {report['error']}")
                return False

        finally:
            # Cleanup
            if os.path.exists(temp_file):
                os.remove(temp_file)
                print(f"\n[*] Cleaned up test data file")

    except Exception as e:
        print(f"[!] Error testing growth analyzer: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_scripts():
    """Test that scripts can be imported"""
    print("\n" + "=" * 60)
    print("Testing Script Imports")
    print("=" * 60)

    try:
        # Test find_duplicates script
        scripts_dir = project_root / "skills" / "disk-cleaner" / "scripts"

        find_dupes_script = scripts_dir / "find_duplicates.py"
        analyze_growth_script = scripts_dir / "analyze_growth.py"

        if find_dupes_script.exists():
            print(f"\n[OK] find_duplicates.py exists at {find_dupes_script}")
        else:
            print(f"[!] find_duplicates.py not found")
            return False

        if analyze_growth_script.exists():
            print(f"[OK] analyze_growth.py exists at {analyze_growth_script}")
        else:
            print(f"[!] analyze_growth.py not found")
            return False

        # Test that scripts are syntactically correct
        import py_compile

        try:
            py_compile.compile(str(find_dupes_script), doraise=True)
            print(f"[OK] find_duplicates.py compiles successfully")
        except py_compile.PyCompileError as e:
            print(f"[!] find_duplicates.py has syntax errors: {e}")
            return False

        try:
            py_compile.compile(str(analyze_growth_script), doraise=True)
            print(f"[OK] analyze_growth.py compiles successfully")
        except py_compile.PyCompileError as e:
            print(f"[!] analyze_growth.py has syntax errors: {e}")
            return False

        print("\n[OK] All scripts present and syntactically correct!")
        return True

    except Exception as e:
        print(f"[!] Error testing scripts: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("DISK CLEANER NEW FEATURES TEST SUITE")
    print("=" * 60)

    results = []

    # Test 1: Duplicate Finder
    results.append(("Duplicate Finder", test_duplicate_finder()))

    # Test 2: Growth Analyzer
    results.append(("Growth Analyzer", test_growth_analyzer()))

    # Test 3: Scripts
    results.append(("Scripts", test_scripts()))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "[OK]" if result else "[X]"
        print(f"{status} {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n[OK] All tests passed!")
        return 0
    else:
        print(f"\n[!] {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
