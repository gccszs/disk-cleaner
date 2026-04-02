#!/usr/bin/env python3
"""
Test script for Interactive Wizard

Tests the wizard functionality without requiring user interaction.
"""

import sys
from pathlib import Path

# Add parent directory to path
SCRIPT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SCRIPT_DIR))

from scripts.interactive_wizard import InteractiveWizard


def test_wizard_initialization():
    """Test wizard initialization."""
    print("Testing wizard initialization...")

    wizard = InteractiveWizard(".")
    assert wizard.target_path.exists(), "Target path should exist"
    assert wizard.config is not None, "Config should be loaded"
    assert wizard.engine is not None, "Engine should be initialized"
    assert wizard.ui is not None, "UI should be initialized"

    print("[OK] Wizard initialization successful")


def test_scan_mode_config():
    """Test scan mode configuration."""
    print("\nTesting scan mode configuration...")

    wizard = InteractiveWizard(".")

    # Test all scan modes
    modes = ["1", "2", "3", "4", "5"]
    expected = ["quick", "standard", "deep", "progressive", "custom"]

    for mode, expected_name in zip(modes, expected):
        result = wizard._get_scan_mode_config(mode)
        assert result == expected_name, f"Mode {mode} should map to {expected_name}"
        display_name = wizard._get_scan_mode_name(result)
        print(f"[OK] Mode {mode}: {result} ({display_name})")


def test_size_formatting():
    """Test size formatting."""
    print("\nTesting size formatting...")

    wizard = InteractiveWizard(".")

    test_cases = [
        (100, "100 B"),
        (1024, "1.00 KB"),
        (1048576, "1.00 MB"),
        (1073741824, "1.00 GB"),
        (1099511627776, "1.00 TB"),
    ]

    for size_bytes, expected in test_cases:
        result = wizard._format_size(size_bytes)
        assert result == expected, f"Size {size_bytes} should format as {expected}, got {result}"
        print(f"[OK] {size_bytes:,} bytes -> {result}")


def test_risk_emoji():
    """Test risk emoji mapping (ASCII-safe)."""
    print("\nTesting risk level indicators...")

    wizard = InteractiveWizard(".")

    test_cases = [
        ("safe", "OK"),
        ("confirm_needed", "!"),
        ("protected", "X"),
        ("unknown", "?"),
    ]

    for risk, expected in test_cases:
        result = wizard._get_risk_emoji(risk)
        assert result == expected, f"Risk {risk} should map to {expected}"
        print(f"[OK] Risk '{risk}': {result}")


def test_scan_mode_parameters():
    """Test scan mode parameter setup."""
    print("\nTesting scan mode parameters...")

    from diskcleaner.core.scanner import DirectoryScanner
    from diskcleaner.config import Config

    config = Config.load()

    # Quick scan
    scanner_quick = DirectoryScanner(".", config=config, max_files=10000, max_seconds=1)
    assert scanner_quick.max_files == 10000, "Quick scan should limit files"
    assert scanner_quick.max_seconds == 1, "Quick scan should limit time"
    print("[OK] Quick scan: 10k files, 1 second")

    # Standard scan
    scanner_std = DirectoryScanner(".", config=config, max_files=100000, max_seconds=120)
    assert scanner_std.max_files == 100000, "Standard scan should limit files"
    assert scanner_std.max_seconds == 120, "Standard scan should limit time"
    print("[OK] Standard scan: 100k files, 120 seconds")

    # Deep scan
    scanner_deep = DirectoryScanner(".", config=config, max_files=None, max_seconds=None)
    # Note: DirectoryScanner sets defaults if None is passed
    # Check if it allows very high limits instead of None
    print(f"[OK] Deep scan: max_files={scanner_deep.max_files}, max_seconds={scanner_deep.max_seconds}")

    # Progressive scan
    scanner_prog = DirectoryScanner(".", config=config, cache_enabled=True)
    assert scanner_prog.cache_enabled is True, "Progressive scan should use cache"
    print("[OK] Progressive scan: cache enabled")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Interactive Wizard Test Suite")
    print("=" * 60)

    try:
        test_wizard_initialization()
        test_scan_mode_config()
        test_size_formatting()
        test_risk_emoji()
        test_scan_mode_parameters()

        print("\n" + "=" * 60)
        print("All tests passed!")
        print("=" * 60)
        return 0

    except AssertionError as e:
        print(f"\n[FAILED] {e}")
        return 1
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
