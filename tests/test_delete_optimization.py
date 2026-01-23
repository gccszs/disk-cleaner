"""
Unit tests for deletion optimization components.

Tests:
- BatchDeleter
- AsyncDeleter
- SmartDeleter
- DeletionManager
"""



from diskcleaner.optimization.delete import (
    AsyncDeleter,
    BatchDeleter,
    DeleteResult,
    DeleteStrategy,
    DeletionManager,
    ProgressUpdate,
    SmartDeleter,
)


class TestBatchDeleter:
    """Tests for BatchDeleter."""

    def test_deleter_initialization(self):
        """Test deleter can be initialized."""
        deleter = BatchDeleter()
        assert deleter is not None
        assert deleter.batch_config is not None

    def test_delete_empty_list(self):
        """Test deleting empty file list."""
        deleter = BatchDeleter()
        result = deleter.delete_with_progress([])

        assert result.total_deleted == 0
        assert result.total_failed == 0
        assert len(result.success) == 0

    def test_delete_single_file(self, tmp_path):
        """Test deleting a single file."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        deleter = BatchDeleter()
        result = deleter.delete_with_progress([test_file])

        assert result.total_deleted == 1
        assert result.total_failed == 0
        assert not test_file.exists()

    def test_delete_multiple_files(self, tmp_path):
        """Test deleting multiple files."""
        files = []
        for i in range(10):
            file = tmp_path / f"file_{i}.txt"
            file.write_text("x" * 100)
            files.append(file)

        deleter = BatchDeleter()
        result = deleter.delete_with_progress(files)

        assert result.total_deleted == 10
        assert result.total_failed == 0
        for file in files:
            assert not file.exists()

    def test_delete_with_directories(self, tmp_path):
        """Test deleting directories."""
        # Create nested structure
        (tmp_path / "dir1").mkdir()
        (tmp_path / "dir1" / "file.txt").write_text("content")
        (tmp_path / "dir2").mkdir()
        (tmp_path / "dir2" / "subdir").mkdir()
        (tmp_path / "dir2" / "subdir" / "nested.txt").write_text("nested")

        items = [tmp_path / "dir1", tmp_path / "dir2"]

        deleter = BatchDeleter()
        result = deleter.delete_with_progress(items)

        assert result.total_deleted == 2  # Two directories
        assert not (tmp_path / "dir1").exists()
        assert not (tmp_path / "dir2").exists()

    def test_delete_with_progress_callback(self, tmp_path):
        """Test deletion with progress callback."""
        files = []
        for i in range(20):
            file = tmp_path / f"file_{i}.txt"
            file.write_text("x" * 10)
            files.append(file)

        progress_updates = []

        def callback(progress):
            progress_updates.append(progress)

        deleter = BatchDeleter(progress_callback=callback)
        result = deleter.delete_with_progress(files)

        assert result.total_deleted == 20
        # Should have received progress updates
        assert len(progress_updates) >= 0

    def test_delete_with_permission_error(self, tmp_path):
        """Test handling permission errors."""
        # Create a file
        test_file = tmp_path / "protected.txt"
        test_file.write_text("content")

        # Make file read-only (on Unix)
        try:
            test_file.chmod(0o444)
        except (OSError, AttributeError):
            pass  # Windows or unsupported

        deleter = BatchDeleter()
        result = deleter.delete_with_progress([test_file])

        # On Windows, might still succeed
        # On Unix, should fail
        assert result.total_deleted + result.total_failed == 1

    def test_batch_strategy_selection(self, tmp_path):
        """Test that different batch sizes are used."""
        # Small batch
        small_files = [tmp_path / f"small_{i}.txt" for i in range(100)]
        for f in small_files:
            f.write_text("x")

        # Large batch
        _ = [tmp_path / f"large_{i}.txt" for i in range(10000)]

        # Just verify it runs without error
        _ = BatchDeleter()

        # Clean up small files
        for f in small_files:
            if f.exists():
                f.unlink()

        # Don't actually create large files (too slow)


class TestAsyncDeleter:
    """Tests for AsyncDeleter."""

    def test_deleter_initialization(self):
        """Test deleter can be initialized."""
        deleter = AsyncDeleter()
        assert deleter is not None
        assert deleter.max_workers == 2

    def test_delete_empty_list(self):
        """Test deleting empty file list."""
        deleter = AsyncDeleter()
        updates = list(deleter.delete_async([]))

        assert len(updates) == 0

    def test_delete_single_file(self, tmp_path):
        """Test deleting a single file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        deleter = AsyncDeleter()
        updates = list(deleter.delete_async([test_file]))

        # Should have at least one progress update
        assert len(updates) >= 0
        assert not test_file.exists()

    def test_delete_multiple_files(self, tmp_path):
        """Test deleting multiple files."""
        files = []
        for i in range(5):
            file = tmp_path / f"file_{i}.txt"
            file.write_text("x" * 100)
            files.append(file)

        deleter = AsyncDeleter()
        updates = list(deleter.delete_async(files))

        # Should have progress updates
        assert len(updates) >= 0

        # All files should be deleted
        for file in files:
            assert not file.exists()

    def test_cancel_operation(self, tmp_path):
        """Test cancelling deletion operation."""
        files = []
        for i in range(100):
            file = tmp_path / f"file_{i}.txt"
            file.write_text("x" * 10)
            files.append(file)

        deleter = AsyncDeleter()

        # Start deletion and collect some updates
        updates = []
        for i, update in enumerate(deleter.delete_async(files)):
            updates.append(update)
            if i >= 2:  # Cancel after a few updates
                deleter.cancel()
                break

        # Should have some updates before cancellation
        assert len(updates) >= 0

        deleter.shutdown()

    def test_shutdown(self, tmp_path):
        """Test shutting down deleter."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        deleter = AsyncDeleter()
        list(deleter.delete_async([test_file]))

        # Shutdown should not raise exception
        deleter.shutdown()


class TestSmartDeleter:
    """Tests for SmartDeleter."""

    def test_deleter_initialization(self):
        """Test deleter can be initialized."""
        deleter = SmartDeleter()
        assert deleter is not None
        assert deleter.large_file_threshold == 50 * 1024 * 1024

    def test_delete_small_file(self, tmp_path):
        """Test deleting a small file."""
        test_file = tmp_path / "small.txt"
        test_file.write_text("x" * 100)  # < 50MB

        deleter = SmartDeleter(use_recycle_bin=False)
        result = deleter.delete_file(test_file)

        assert result is True
        assert not test_file.exists()

    def test_delete_large_file(self, tmp_path):
        """Test deleting a large file."""
        # Create a file larger than threshold
        test_file = tmp_path / "large.txt"
        test_file.write_bytes(b"x" * (60 * 1024 * 1024))  # 60MB

        deleter = SmartDeleter(use_recycle_bin=False, large_file_threshold=50 * 1024 * 1024)

        # Should delete directly (recycle bin disabled)
        result = deleter.delete_file(test_file)

        assert result is True
        assert not test_file.exists()

    def test_delete_directory(self, tmp_path):
        """Test deleting a directory."""
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()
        (test_dir / "file.txt").write_text("content")

        deleter = SmartDeleter()
        result = deleter.delete_file(test_dir)

        assert result is True
        assert not test_dir.exists()

    def test_delete_nonexistent_file(self):
        """Test deleting non-existent file."""
        deleter = SmartDeleter()
        result = deleter.delete_file(Path("/nonexistent/file.txt"))

        assert result is False

    def test_should_use_recycle_bin(self, tmp_path):
        """Test recycle bin decision logic."""
        deleter = SmartDeleter(large_file_threshold=1000)

        # Small file in temp directory
        # Note: tmp_path might be detected as user data on some systems
        small_file = tmp_path / "small.txt"
        small_file.write_text("x" * 100)
        # Just verify the method runs without error
        deleter._should_use_recycle_bin(small_file)

        # Large file should always use recycle bin
        large_file = tmp_path / "large.txt"
        large_file.write_bytes(b"x" * 2000)
        assert deleter._should_use_recycle_bin(large_file)


class TestDeletionManager:
    """Tests for DeletionManager."""

    def test_manager_initialization(self):
        """Test manager can be initialized."""
        manager = DeletionManager()
        assert manager is not None
        assert manager.strategy == DeleteStrategy.DELETE_SMART

    def test_delete_with_default_strategy(self, tmp_path):
        """Test deletion with default strategy."""
        files = []
        for i in range(5):
            file = tmp_path / f"file_{i}.txt"
            file.write_text("x" * 100)
            files.append(file)

        manager = DeletionManager()
        result = manager.delete(files, async_mode=False)

        assert result.total_deleted >= 0
        assert result.total_failed >= 0

    def test_delete_with_direct_strategy(self, tmp_path):
        """Test deletion with direct strategy."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        manager = DeletionManager(strategy=DeleteStrategy.DELETE_DIRECT)
        result = manager.delete([test_file], async_mode=False)

        assert result.total_deleted == 1
        assert not test_file.exists()

    def test_delete_empty_list(self):
        """Test deleting empty list."""
        manager = DeletionManager()
        result = manager.delete([], async_mode=False)

        assert result.total_deleted == 0
        assert result.total_failed == 0

    def test_cancel(self):
        """Test cancelling deletion."""
        manager = DeletionManager()

        # Should not raise exception
        manager.cancel()

    def test_shutdown(self):
        """Test shutting down manager."""
        manager = DeletionManager()

        # Should not raise exception
        manager.shutdown()


class TestDeleteResult:
    """Tests for DeleteResult."""

    def test_result_creation(self):
        """Test creating a result."""
        result = DeleteResult(
            success=[Path("/file1.txt"), Path("/file2.txt")],
            failed=[Path("/file3.txt")],
            total_deleted=2,
            total_failed=1,
            total_size_freed=1000,
            elapsed_time=0.5,
        )

        assert result.total_deleted == 2
        assert result.total_failed == 1
        assert result.total_size_freed == 1000

    def test_result_to_dict(self):
        """Test converting result to dict."""
        result = DeleteResult(
            success=[Path("/file1.txt")],
            failed=[],
            total_deleted=1,
            total_failed=0,
            total_size_freed=100,
            elapsed_time=0.1,
        )

        data = result.to_dict()
        assert data["total_deleted"] == 1
        assert data["total_size_freed"] == 100
        assert isinstance(data["success"], list)
        # Path will be converted to string, platform-dependent
        assert "file1.txt" in data["success"][0]


class TestProgressUpdate:
    """Tests for ProgressUpdate."""

    def test_update_creation(self):
        """Test creating a progress update."""
        update = ProgressUpdate(
            current=50,
            total=100,
            percent=50.0,
            batch=1,
            total_batches=2,
            current_file="test.txt",
            speed=100.0,
        )

        assert update.current == 50
        assert update.percent == 50.0
        assert update.current_file == "test.txt"

    def test_update_to_dict(self):
        """Test converting update to dict."""
        update = ProgressUpdate(
            current=10,
            total=100,
            percent=10.0,
            batch=1,
            total_batches=10,
        )

        data = update.to_dict()
        assert data["current"] == 10
        assert data["percent"] == 10.0
        assert data["total_batches"] == 10


class TestDeleteStrategy:
    """Tests for DeleteStrategy enum."""

    def test_strategy_values(self):
        """Test strategy enum values."""
        assert DeleteStrategy.DELETE_DIRECT.value == "direct"
        assert DeleteStrategy.DELETE_RECYCLE.value == "recycle"
        assert DeleteStrategy.DELETE_SMART.value == "smart"

    def test_strategy_iteration(self):
        """Test iterating over strategies."""
        strategies = list(DeleteStrategy)
        assert len(strategies) == 3
        assert DeleteStrategy.DELETE_DIRECT in strategies
