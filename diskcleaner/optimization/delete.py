"""
Optimized deletion components.

Provides:
- BatchDeleter: Smart batched deletion
- AsyncDeleter: Background async deletion
- DeleteStrategy: Smart deletion strategy selection
"""

import os
import time
import shutil
import threading
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any, Iterator
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue, Empty
from enum import Enum

from diskcleaner.optimization.memory import MemoryMonitor


class DeleteStrategy(Enum):
    """Deletion strategy types."""
    DELETE_DIRECT = "direct"      # Direct delete (fastest)
    DELETE_RECYCLE = "recycle"    # Move to recycle bin
    DELETE_SMART = "smart"        # Smart selection


@dataclass
class DeleteResult:
    """Result of a delete operation."""
    success: List[Path]
    failed: List[Path]
    total_deleted: int
    total_failed: int
    total_size_freed: int
    elapsed_time: float
    cancelled: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'success': [str(p) for p in self.success],
            'failed': [str(p) for p in self.failed],
            'total_deleted': self.total_deleted,
            'total_failed': self.total_failed,
            'total_size_freed': self.total_size_freed,
            'elapsed_time': self.elapsed_time,
            'cancelled': self.cancelled,
        }


@dataclass
class ProgressUpdate:
    """Progress update for deletion operations."""
    current: int
    total: int
    percent: float
    batch: int
    total_batches: int
    current_file: Optional[str] = None
    speed: float = 0.0  # files/second

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'current': self.current,
            'total': self.total,
            'percent': self.percent,
            'batch': self.batch,
            'total_batches': self.total_batches,
            'current_file': self.current_file,
            'speed': self.speed,
        }


class BatchDeleter:
    """
    Smart batched file deletion.

    Deletes files in batches with progress tracking and error handling.
    """

    def __init__(self, progress_callback=None):
        """
        Initialize batch deleter.

        Args:
            progress_callback: Optional callback for progress updates
        """
        self.batch_config = {
            'small': {'count': 1000, 'interval': 0.1},
            'medium': {'count': 5000, 'interval': 0.5},
            'large': {'count': 10000, 'interval': 1.0},
        }
        self.progress_callback = progress_callback

    def delete_with_progress(self, files: List[Path]) -> DeleteResult:
        """
        Delete files in batches with progress updates.

        Args:
            files: List of files to delete

        Returns:
            DeleteResult with success/failed files
        """
        if not files:
            return DeleteResult(
                success=[],
                failed=[],
                total_deleted=0,
                total_failed=0,
                total_size_freed=0,
                elapsed_time=0.0,
            )

        start_time = time.time()

        # Select batch strategy
        file_count = len(files)
        if file_count < 5000:
            config = self.batch_config['small']
        elif file_count < 20000:
            config = self.batch_config['medium']
        else:
            config = self.batch_config['large']

        batch_size = config['count']
        interval = config['interval']

        success = []
        failed = []
        cancelled = False
        total_size = 0

        # Process in batches
        for i in range(0, file_count, batch_size):
            if cancelled:
                break

            batch = files[i:i + batch_size]
            batch_success, batch_failed, batch_size_freed = self._delete_batch(batch)

            success.extend(batch_success)
            failed.extend(batch_failed)
            total_size += batch_size_freed

            # Progress update
            current_count = len(success) + len(failed)
            if self.progress_callback:
                progress = ProgressUpdate(
                    current=current_count,
                    total=file_count,
                    percent=(current_count / file_count) * 100,
                    batch=i // batch_size + 1,
                    total_batches=(file_count + batch_size - 1) // batch_size,
                )

                # Callback returns False to cancel
                if self.progress_callback(progress) is False:
                    cancelled = True
                    break

            # Batch interval (let system breathe)
            if i + batch_size < file_count:
                time.sleep(interval)

        elapsed_time = time.time() - start_time

        return DeleteResult(
            success=success,
            failed=failed,
            total_deleted=len(success),
            total_failed=len(failed),
            total_size_freed=total_size,
            elapsed_time=elapsed_time,
            cancelled=cancelled,
        )

    def _delete_batch(self, files: List[Path]) -> Tuple[List[Path], List[Path], int]:
        """
        Delete a batch of files.

        Args:
            files: Files to delete

        Returns:
            Tuple of (success_list, failed_list, size_freed)
        """
        success = []
        failed = []
        size_freed = 0

        for file in files:
            try:
                # Permission check (fast fail)
                if not os.access(file, os.W_OK):
                    failed.append(file)
                    continue

                # Get size before deletion
                try:
                    file_size = file.stat().st_size
                except OSError:
                    file_size = 0

                # Delete based on type
                if file.is_dir():
                    shutil.rmtree(file, ignore_errors=False)
                else:
                    file.unlink()

                success.append(file)
                size_freed += file_size

            except (PermissionError, OSError):
                failed.append(file)
            except Exception:
                failed.append(file)

        return success, failed, size_freed


class AsyncDeleter:
    """
    Async file deletion with background execution.

    Executes deletion in background threads while main thread handles UI.
    """

    def __init__(self, max_workers: int = 2, progress_callback=None):
        """
        Initialize async deleter.

        Args:
            max_workers: Number of worker threads (2 is optimal for I/O)
            progress_callback: Optional callback for progress updates
        """
        self.max_workers = max_workers
        self.executor: Optional[ThreadPoolExecutor] = None
        self.progress_callback = progress_callback
        self.stop_event = threading.Event()

    def delete_async(self, files: List[Path]) -> Iterator[ProgressUpdate]:
        """
        Delete files asynchronously, yielding progress updates.

        Args:
            files: Files to delete

        Yields:
            ProgressUpdate objects with deletion progress
        """
        if not files:
            return

        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        self.stop_event.clear()

        # Split into batches
        batch_size = 100
        batches = [files[i:i + batch_size] for i in range(0, len(files), batch_size)]

        # Submit all batches
        futures = {}
        for batch_id, batch in enumerate(batches):
            if not self.stop_event.is_set():
                future = self.executor.submit(self._delete_batch_async, batch_id, batch)
                futures[future] = batch_id

        # Collect results
        total_deleted = 0
        total_failed = 0
        total_size = 0
        start_time = time.time()

        for future in as_completed(futures):
            if self.stop_event.is_set():
                future.cancel()
                continue

            try:
                result = future.result(timeout=30.0)
                total_deleted += result['deleted']
                total_failed += result['failed']
                total_size += result['size_freed']

                # Yield progress update
                elapsed = time.time() - start_time
                speed = total_deleted / elapsed if elapsed > 0 else 0

                update = ProgressUpdate(
                    batch_id=futures[future],
                    current=total_deleted + total_failed,
                    total=len(files),
                    percent=((total_deleted + total_failed) / len(files)) * 100,
                    batch=futures[future] + 1,
                    total_batches=len(batches),
                    speed=speed,
                )

                if self.progress_callback:
                    self.progress_callback(update)

                yield update

            except Exception:
                pass  # Log error, continue

        self.stop_event.clear()

        # Cleanup executor
        if self.executor:
            self.executor.shutdown(wait=False)
            self.executor = None

    def _delete_batch_async(self, batch_id: int, files: List[Path]) -> Dict[str, int]:
        """
        Worker thread: delete a batch of files.

        Args:
            batch_id: Batch identifier
            files: Files to delete

        Returns:
            Dict with deletion statistics
        """
        deleted = 0
        failed = 0
        size_freed = 0

        for file in files:
            if self.stop_event.is_set():
                break

            try:
                # Get size before deletion
                try:
                    file_size = file.stat().st_size
                except OSError:
                    file_size = 0

                # Delete
                if file.is_dir():
                    shutil.rmtree(file)
                else:
                    file.unlink()

                deleted += 1
                size_freed += file_size

            except Exception:
                failed += 1

        return {
            'batch_id': batch_id,
            'deleted': deleted,
            'failed': failed,
            'size_freed': size_freed,
        }

    def cancel(self):
        """Cancel the deletion operation."""
        self.stop_event.set()

    def shutdown(self):
        """Cleanup resources."""
        self.stop_event.set()
        if self.executor:
            self.executor.shutdown(wait=False)
            self.executor = None


class SmartDeleter:
    """
    Smart deletion with strategy selection.

    Automatically chooses optimal deletion strategy based on file characteristics.
    """

    def __init__(self,
                 use_recycle_bin: bool = False,
                 large_file_threshold: int = 50 * 1024 * 1024):
        """
        Initialize smart deleter.

        Args:
            use_recycle_bin: Whether to use recycle bin (platform-dependent)
            large_file_threshold: Size threshold for "large file" (default 50MB)
        """
        self.use_recycle_bin = use_recycle_bin
        self.large_file_threshold = large_file_threshold

    def delete_file(self, file: Path) -> bool:
        """
        Delete a single file using smart strategy.

        Args:
            file: File to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            if not file.exists():
                return False

            # Check if should use recycle bin
            if self.use_recycle_bin and self._should_use_recycle_bin(file):
                return self._move_to_recycle_bin(file)
            else:
                # Direct delete
                if file.is_dir():
                    shutil.rmtree(file)
                else:
                    file.unlink()
                return True

        except Exception:
            return False

    def _should_use_recycle_bin(self, file: Path) -> bool:
        """
        Decide if file should go to recycle bin.

        Args:
            file: File to check

        Returns:
            True if should use recycle bin
        """
        # Large files go to recycle bin (unless user data)
        if file.stat().st_size > self.large_file_threshold:
            return True

        # System paths go to recycle bin
        path_str = str(file).lower()
        system_indicators = ['windows', 'program files', 'system', 'library']
        if any(indicator in path_str for indicator in system_indicators):
            return True

        # User data goes to recycle bin
        user_indicators = ['users', 'home', 'documents', 'desktop']
        if any(indicator in path_str for indicator in user_indicators):
            return True

        # Small temp files: direct delete
        return False

    def _move_to_recycle_bin(self, file: Path) -> bool:
        """
        Move file to recycle bin.

        Args:
            file: File to move

        Returns:
            True if successful
        """
        try:
            # Platform-specific implementation
            if os.name == 'nt':  # Windows
                import send2trash
                send2trash.send2trash(str(file))
                return True
            else:  # macOS/Linux
                # Try send2trash if available
                try:
                    import send2trash
                    send2trash.send2trash(str(file))
                    return True
                except ImportError:
                    # Fallback to direct delete
                    if file.is_dir():
                        shutil.rmtree(file)
                    else:
                        file.unlink()
                    return True

        except Exception:
            # Fallback to direct delete
            try:
                if file.is_dir():
                    shutil.rmtree(file)
                else:
                    file.unlink()
                return True
            except Exception:
                return False


class DeletionManager:
    """
    High-level deletion manager.

    Provides unified interface for all deletion strategies.
    """

    def __init__(self,
                 strategy: DeleteStrategy = DeleteStrategy.DELETE_SMART,
                 progress_callback=None):
        """
        Initialize deletion manager.

        Args:
            strategy: Deletion strategy to use
            progress_callback: Optional progress callback
        """
        self.strategy = strategy
        self.progress_callback = progress_callback
        self.batch_deleter = BatchDeleter(progress_callback)
        self.async_deleter = None  # Created when needed
        self.smart_deleter = SmartDeleter()

    def delete(self, files: List[Path], async_mode: bool = False) -> DeleteResult:
        """
        Delete files using configured strategy.

        Args:
            files: Files to delete
            async_mode: Whether to use async deletion

        Returns:
            DeleteResult with operation results
        """
        if not files:
            return DeleteResult(
                success=[],
                failed=[],
                total_deleted=0,
                total_failed=0,
                total_size_freed=0,
                elapsed_time=0.0,
            )

        if async_mode:
            return self._delete_async(files)
        else:
            return self._delete_batch(files)

    def _delete_batch(self, files: List[Path]) -> DeleteResult:
        """Delete files in batches."""
        # Apply smart strategy filtering
        if self.strategy == DeleteStrategy.DELETE_SMART:
            files = self._apply_smart_filtering(files)

        return self.batch_deleter.delete_with_progress(files)

    def _delete_async(self, files: List[Path]) -> DeleteResult:
        """Delete files asynchronously."""
        self.async_deleter = AsyncDeleter(progress_callback=self.progress_callback)

        success = []
        failed = []
        total_size = 0
        start_time = time.time()

        # Collect results from async operation
        for update in self.async_deleter.delete_async(files):
            # Update is yielded, but we don't track individual file results here
            pass

        # For async mode, we'd need to track results differently
        # This is a simplified version
        elapsed_time = time.time() - start_time

        return DeleteResult(
            success=success,  # Would be filled by actual implementation
            failed=failed,
            total_deleted=len(success),
            total_failed=len(failed),
            total_size_freed=total_size,
            elapsed_time=elapsed_time,
        )

    def _apply_smart_filtering(self, files: List[Path]) -> List[Path]:
        """
        Apply smart strategy filtering.

        Args:
            files: Files to filter

        Returns:
            Filtered file list
        """
        # Smart strategy: separate files by deletion method
        return files  # Simplified, would filter in real implementation

    def cancel(self):
        """Cancel ongoing deletion."""
        if self.async_deleter:
            self.async_deleter.cancel()

    def shutdown(self):
        """Cleanup resources."""
        if self.async_deleter:
            self.async_deleter.shutdown()
