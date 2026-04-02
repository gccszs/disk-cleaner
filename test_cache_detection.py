#!/usr/bin/env python3
"""
Test script to verify cache detection improvements.
Tests WindowsPlatform cache detection with comprehensive coverage.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from diskcleaner.platforms.windows import WindowsPlatform


def test_cache_detection():
    """Test comprehensive cache detection."""
    print("=" * 60)
    print("Testing Windows Cache Detection")
    print("=" * 60)

    # Test cache locations
    print("\n[1] Testing Cache Locations:")
    print("-" * 60)
    cache_locations = WindowsPlatform.get_cache_locations()

    if not cache_locations:
        print("  No cache locations found!")
    else:
        print(f"  Found {len(cache_locations)} cache locations:")
        for i, loc in enumerate(cache_locations, 1):
            # Encode to ASCII-safe representation
            try:
                ascii_path = loc.encode('ascii', errors='replace').decode('ascii')
            except:
                ascii_path = "<path encoding error>"
            print(f"    {i}. {ascii_path}")

    # Test temp locations
    print("\n[2] Testing Temp Locations:")
    print("-" * 60)
    temp_locations = WindowsPlatform.get_temp_locations()

    if not temp_locations:
        print("  No temp locations found!")
    else:
        print(f"  Found {len(temp_locations)} temp locations:")
        for i, loc in enumerate(temp_locations, 1):
            try:
                ascii_path = loc.encode('ascii', errors='replace').decode('ascii')
            except:
                ascii_path = "<path encoding error>"
            print(f"    {i}. {ascii_path}")

    # Test log locations
    print("\n[3] Testing Log Locations:")
    print("-" * 60)
    log_locations = WindowsPlatform.get_log_locations()

    if not log_locations:
        print("  No log locations found!")
    else:
        print(f"  Found {len(log_locations)} log locations:")
        for i, loc in enumerate(log_locations, 1):
            try:
                ascii_path = loc.encode('ascii', errors='replace').decode('ascii')
            except:
                ascii_path = "<path encoding error>"
            print(f"    {i}. {ascii_path}")

    # Test Docker locations
    print("\n[4] Testing Docker Locations:")
    print("-" * 60)
    docker_locations = WindowsPlatform.get_docker_locations()

    if not docker_locations:
        print("  No Docker locations found!")
    else:
        print(f"  Found {len(docker_locations)} Docker locations:")
        for i, loc in enumerate(docker_locations, 1):
            try:
                ascii_path = loc.encode('ascii', errors='replace').decode('ascii')
            except:
                ascii_path = "<path encoding error>"
            print(f"    {i}. {ascii_path}")

    # Summary
    print("\n" + "=" * 60)
    print("Summary:")
    print("-" * 60)
    print(f"  Cache locations: {len(cache_locations)}")
    print(f"  Temp locations:  {len(temp_locations)}")
    print(f"  Log locations:   {len(log_locations)}")
    print(f"  Docker locations: {len(docker_locations)}")
    print(f"  Total:           {len(cache_locations) + len(temp_locations) + len(log_locations) + len(docker_locations)}")
    print("=" * 60)

    # Check for expected cache types
    print("\n[5] Checking for Expected Cache Types:")
    print("-" * 60)

    cache_types = {
        "Chrome": any("Chrome" in loc for loc in cache_locations),
        "Edge": any("Edge" in loc for loc in cache_locations),
        "Firefox": any("Firefox" in loc for loc in cache_locations),
        "JetBrains": any("JetBrains" in loc for loc in cache_locations),
        "npm": any("npm" in loc.lower() for loc in cache_locations),
        "yarn": any("yarn" in loc.lower() for loc in cache_locations),
        "pnpm": any("pnpm" in loc.lower() for loc in cache_locations),
        "pip": any("pip" in loc.lower() for loc in cache_locations),
        "poetry": any("poetry" in loc.lower() for loc in cache_locations),
        "gradle": any("gradle" in loc.lower() for loc in cache_locations),
        "maven": any("maven" in loc.lower() for loc in cache_locations),
    }

    for cache_type, found in cache_types.items():
        status = "FOUND" if found else "NOT FOUND"
        print(f"  {cache_type:15} {status}")

    print("\n" + "=" * 60)
    print("Test completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    test_cache_detection()
