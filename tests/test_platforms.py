"""
Cross-platform tests for platform-specific functionality.
"""

import os
import platform

import pytest

from diskcleaner.platforms import LinuxPlatform, MacOSPlatform, WindowsPlatform


class TestWindowsPlatform:
    """Test Windows platform functionality."""

    @pytest.mark.skipif(platform.system() != "Windows", reason="Windows only")
    def test_get_temp_locations(self):
        """Test Windows temp location detection."""
        locations = WindowsPlatform.get_temp_locations()
        assert isinstance(locations, list)
        assert len(locations) > 0

        # Check that TEMP directory is included
        temp_env = os.environ.get("TEMP", "")
        if temp_env:
            assert any(temp_env in loc for loc in locations)

    @pytest.mark.skipif(platform.system() != "Windows", reason="Windows only")
    def test_get_cache_locations(self):
        """Test Windows cache location detection."""
        locations = WindowsPlatform.get_cache_locations()
        assert isinstance(locations, list)

    @pytest.mark.skipif(platform.system() != "Windows", reason="Windows only")
    def test_check_disk_space(self):
        """Test Windows disk space checking."""
        space_info = WindowsPlatform.check_disk_space()
        assert isinstance(space_info, dict)
        assert "total_gb" in space_info
        assert "used_gb" in space_info
        assert "free_gb" in space_info
        assert "usage_percent" in space_info
        assert space_info["total_gb"] > 0

    def test_get_system_maintenance_items(self):
        """Test Windows system maintenance items."""
        items = WindowsPlatform.get_system_maintenance_items()
        assert isinstance(items, dict)
        assert "windows_update" in items
        assert "recycle_bin" in items
        assert "prefetch" in items

        # Check item structure
        for key, item in items.items():
            assert "name" in item
            assert "path" in item
            assert "description" in item
            assert "risk" in item


class TestLinuxPlatform:
    """Test Linux platform functionality."""

    @pytest.mark.skipif(platform.system() != "Linux", reason="Linux only")
    def test_get_temp_locations(self):
        """Test Linux temp location detection."""
        locations = LinuxPlatform.get_temp_locations()
        assert isinstance(locations, list)
        assert len(locations) > 0
        # /tmp should always exist on Linux
        assert any("/tmp" in loc for loc in locations)

    @pytest.mark.skipif(platform.system() != "Linux", reason="Linux only")
    def test_get_cache_locations(self):
        """Test Linux cache location detection."""
        locations = LinuxPlatform.get_cache_locations()
        assert isinstance(locations, list)

    @pytest.mark.skipif(platform.system() != "Linux", reason="Linux only")
    def test_check_disk_space(self):
        """Test Linux disk space checking."""
        space_info = LinuxPlatform.check_disk_space("/")
        assert isinstance(space_info, dict)
        assert "total_gb" in space_info
        assert "used_gb" in space_info
        assert "free_gb" in space_info
        assert "usage_percent" in space_info
        assert space_info["total_gb"] > 0

    def test_get_system_maintenance_items(self):
        """Test Linux system maintenance items."""
        items = LinuxPlatform.get_system_maintenance_items()
        assert isinstance(items, dict)
        assert "apt_cache" in items
        assert "journal_logs" in items

        # Check item structure
        for key, item in items.items():
            assert "name" in item
            assert "path" in item
            assert "description" in item
            assert "risk" in item

    def test_get_package_manager_cache(self):
        """Test Linux package manager cache info."""
        pm_cache = LinuxPlatform.get_package_manager_cache()
        assert isinstance(pm_cache, dict)

        # Should have common package managers
        assert "apt" in pm_cache
        assert "yum" in pm_cache or "dnf" in pm_cache


class TestMacOSPlatform:
    """Test macOS platform functionality."""

    @pytest.mark.skipif(platform.system() != "Darwin", reason="macOS only")
    def test_get_temp_locations(self):
        """Test macOS temp location detection."""
        locations = MacOSPlatform.get_temp_locations()
        assert isinstance(locations, list)
        assert len(locations) > 0

    @pytest.mark.skipif(platform.system() != "Darwin", reason="macOS only")
    def test_get_cache_locations(self):
        """Test macOS cache location detection."""
        locations = MacOSPlatform.get_cache_locations()
        assert isinstance(locations, list)

    @pytest.mark.skipif(platform.system() != "Darwin", reason="macOS only")
    def test_check_disk_space(self):
        """Test macOS disk space checking."""
        space_info = MacOSPlatform.check_disk_space("/")
        assert isinstance(space_info, dict)
        assert "total_gb" in space_info
        assert "used_gb" in space_info
        assert "free_gb" in space_info
        assert "usage_percent" in space_info
        assert space_info["total_gb"] > 0

    def test_get_system_maintenance_items(self):
        """Test macOS system maintenance items."""
        items = MacOSPlatform.get_system_maintenance_items()
        assert isinstance(items, dict)
        assert "user_cache" in items
        assert "ios_backups" in items
        assert "homebrew_cache" in items

        # Check item structure
        for key, item in items.items():
            assert "name" in item
            assert "path" in item
            assert "description" in item
            assert "risk" in item


class TestCrossPlatform:
    """Cross-platform tests that run on all platforms."""

    def test_all_platforms_have_temp_locations(self):
        """Test all platforms can identify temp locations."""
        current_system = platform.system()

        if current_system == "Windows":
            locations = WindowsPlatform.get_temp_locations()
        elif current_system == "Linux":
            locations = LinuxPlatform.get_temp_locations()
        elif current_system == "Darwin":
            locations = MacOSPlatform.get_temp_locations()
        else:
            pytest.skip(f"Unsupported platform: {current_system}")

        assert isinstance(locations, list)
        # Should have at least one temp location
        assert len(locations) > 0

    def test_all_platforms_have_cache_locations(self):
        """Test all platforms can identify cache locations."""
        current_system = platform.system()

        if current_system == "Windows":
            locations = WindowsPlatform.get_cache_locations()
        elif current_system == "Linux":
            locations = LinuxPlatform.get_cache_locations()
        elif current_system == "Darwin":
            locations = MacOSPlatform.get_cache_locations()
        else:
            pytest.skip(f"Unsupported platform: {current_system}")

        assert isinstance(locations, list)

    def test_all_platforms_can_check_disk_space(self):
        """Test all platforms can check disk space."""
        current_system = platform.system()

        if current_system == "Windows":
            space_info = WindowsPlatform.check_disk_space()
        elif current_system == "Linux":
            space_info = LinuxPlatform.check_disk_space("/")
        elif current_system == "Darwin":
            space_info = MacOSPlatform.check_disk_space("/")
        else:
            pytest.skip(f"Unsupported platform: {current_system}")

        assert isinstance(space_info, dict)
        assert "total_gb" in space_info
        assert "free_gb" in space_info
        assert space_info["total_gb"] > 0

    def test_all_platforms_have_maintenance_items(self):
        """Test all platforms have system maintenance suggestions."""
        current_system = platform.system()

        if current_system == "Windows":
            items = WindowsPlatform.get_system_maintenance_items()
        elif current_system == "Linux":
            items = LinuxPlatform.get_system_maintenance_items()
        elif current_system == "Darwin":
            items = MacOSPlatform.get_system_maintenance_items()
        else:
            pytest.skip(f"Unsupported platform: {current_system}")

        assert isinstance(items, dict)
        assert len(items) > 0

        # All items should have required fields
        for key, item in items.items():
            assert "name" in item
            assert "path" in item
            assert "description" in item
            assert "risk" in item
            assert item["risk"] in ["safe", "confirm", "protected"]
