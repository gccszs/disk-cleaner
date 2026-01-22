"""
pytest configuration and fixtures
"""

import shutil
import tempfile
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing."""
    temp = Path(tempfile.mkdtemp())
    yield temp
    shutil.rmtree(temp)


@pytest.fixture
def sample_files(temp_dir: Path) -> Path:
    """Create sample files for testing."""
    # Create various types of files
    (temp_dir / "test.log").write_text("x" * 1000)
    (temp_dir / "test.txt").write_text("hello world")
    (temp_dir / "app.py").write_text("print('hello')")

    # Create subdirectory with files
    subdir = temp_dir / "subdir"
    subdir.mkdir()
    (subdir / "nested.txt").write_text("nested content")

    # Create duplicate files
    (temp_dir / "dup1.txt").write_text("duplicate content")
    (temp_dir / "dup2.txt").write_text("duplicate content")

    # Create temporary files
    (temp_dir / "temp.tmp").write_text("temporary")

    return temp_dir


@pytest.fixture
def sample_project(temp_dir: Path) -> Path:
    """Create a sample project structure."""
    # Node.js project
    node_modules = temp_dir / "node_modules"
    node_modules.mkdir()
    (node_modules / "package.json").write_text('{"name": "test"}')

    # Python cache
    pycache = temp_dir / "__pycache__"
    pycache.mkdir()
    (pycache / "app.cpython-38.pyc").write_bytes(b"\x00" * 100)

    # Logs
    (temp_dir / "app.log").write_text("x" * 5000)
    (temp_dir / "old.log").write_text("x" * 3000)

    # Build artifacts
    build = temp_dir / "build"
    build.mkdir()
    (build / "output.exe").write_bytes(b"\x00" * 1000)

    return temp_dir


@pytest.fixture
def sample_config(temp_dir: Path) -> Path:
    """Create a sample configuration file."""
    config_content = """
protected:
  paths:
    - "important-project/"
    - "database/"
  patterns:
    - "*.database"
    - "*.db"
    - "config.*"

rules:
  - name: "Old logs"
    pattern: "*.log"
    category: "Logs"
    risk: "safe"
    age_threshold: 60

  - name: "Build artifacts"
    pattern: "build/"
    category: "Build"
    risk: "safe"
    age_threshold: 0

ignore:
  - "node_modules/@types"
  - ".git/*"

safety:
  check_file_locks: true
  verify_permissions: true
  backup_before_delete: false

scan:
  use_incremental: true
  cache_dir: "~/.disk-cleaner/cache"
  cache_ttl: 7
  parallel_jobs: 4
"""
    config_path = temp_dir / ".disk-cleaner.yaml"
    config_path.write_text(config_content)
    return config_path
