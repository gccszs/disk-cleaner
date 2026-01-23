"""
Pytest configuration for cross-platform testing.
"""

import pytest


def pytest_collection_modifyitems(config, items):
    """
    Modify collected test items.
    
    This ensures that benchmark scripts that don't contain actual tests
    don't cause issues on non-Windows platforms.
    """
    # You can add custom collection logic here if needed
    pass


@pytest.fixture(scope="session")
def platform_info():
    """Fixture providing platform information."""
    import platform
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
    }
