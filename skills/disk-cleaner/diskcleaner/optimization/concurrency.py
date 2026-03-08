"""
Concurrency management for optimized execution.

Manages thread pools and process pools for concurrent operations.
Provides optimal worker count calculation and resource cleanup.
"""

import os
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from typing import Dict, Optional


class ConcurrencyManager:
    """
    Unified manager for concurrent resources.

    Manages:
    - Thread pools (for I/O-bound tasks)
    - Process pools (for CPU-bound tasks)
    - Optimal worker count calculation
    - Graceful shutdown
    """

    def __init__(self):
        self.thread_pools: Dict[str, ThreadPoolExecutor] = {}
        self.process_pools: Dict[str, ProcessPoolExecutor] = {}
        self._initialized = False

    def get_thread_pool(
        self, purpose: str, max_workers: Optional[int] = None
    ) -> ThreadPoolExecutor:
        """
        Get or create a thread pool.

        Args:
            purpose: Pool identifier ('io_scan', 'io_delete', 'ui_update')
            max_workers: Maximum worker threads (None for auto)

        Returns:
            ThreadPoolExecutor instance
        """
        if purpose in self.thread_pools:
            return self.thread_pools[purpose]

        workers = max_workers or self._optimal_threads(purpose)
        pool = ThreadPoolExecutor(max_workers=workers, thread_name_prefix=f"{purpose}-")
        self.thread_pools[purpose] = pool
        self._initialized = True
        return pool

    def get_process_pool(
        self, purpose: str, max_workers: Optional[int] = None
    ) -> ProcessPoolExecutor:
        """
        Get or create a process pool.

        Args:
            purpose: Pool identifier ('hash_compute', 'cpu_intensive')
            max_workers: Maximum worker processes (None for auto)

        Returns:
            ProcessPoolExecutor instance
        """
        if purpose in self.process_pools:
            return self.process_pools[purpose]

        workers = max_workers or self._optimal_processes(purpose)
        pool = ProcessPoolExecutor(max_workers=workers)
        self.process_pools[purpose] = pool
        self._initialized = True
        return pool

    def _optimal_threads(self, purpose: str) -> int:
        """
        Calculate optimal thread count for a purpose.

        I/O-bound tasks can use more threads than CPU count.
        """
        cpu_count = os.cpu_count() or 1

        if purpose.startswith("io_"):
            # I/O密集型：可以用更多线程
            # 限制在32以内，避免过多上下文切换
            return min(32, cpu_count * 4)
        elif purpose == "ui_update":
            # UI更新只需要少量线程
            return 2
        else:
            # 默认：CPU核心数
            return cpu_count

    def _optimal_processes(self, purpose: str) -> int:
        """
        Calculate optimal process count for a purpose.

        CPU-bound tasks should not exceed CPU count.
        """
        cpu_count = os.cpu_count() or 1

        if purpose == "hash_compute":
            # 哈希计算是CPU密集型
            return cpu_count
        else:
            # 默认
            return cpu_count

    def shutdown_pool(self, purpose: str, wait: bool = True):
        """
        Shutdown a specific pool.

        Args:
            purpose: Pool identifier
            wait: Whether to wait for pending work to complete
        """
        if purpose in self.thread_pools:
            self.thread_pools[purpose].shutdown(wait=wait)
            del self.thread_pools[purpose]

        if purpose in self.process_pools:
            self.process_pools[purpose].shutdown(wait=wait)
            del self.process_pools[purpose]

    def shutdown_all(self, wait: bool = True):
        """
        Shutdown all pools gracefully.

        Args:
            wait: Whether to wait for pending work to complete
        """
        for pool in self.thread_pools.values():
            pool.shutdown(wait=wait)
        self.thread_pools.clear()

        for pool in self.process_pools.values():
            pool.shutdown(wait=wait)
        self.process_pools.clear()

        self._initialized = False

    def get_pool_count(self) -> int:
        """Get total number of active pools."""
        return len(self.thread_pools) + len(self.process_pools)

    def is_initialized(self) -> bool:
        """Check if any pools have been created."""
        return self._initialized

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.shutdown_all(wait=True)
        return False
