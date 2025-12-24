"""
Timeout handling and failure detection
"""

import time
from typing import Callable, Optional, Any, Dict, List
from enum import Enum
from config import DEFAULT_REQUEST_TIMEOUT


class FailureType(Enum):
    """Types of failures that can occur"""
    TIMEOUT = "timeout"
    NETWORK_ERROR = "network_error"
    NODE_UNREACHABLE = "node_unreachable"
    QUORUM_FAILURE = "quorum_failure"


class FailureDetector:
    """
    Detects and tracks node failures.
    """

    def __init__(self, timeout: float = DEFAULT_REQUEST_TIMEOUT):
        self.timeout = timeout
        self.failure_history: Dict[str, List[float]] = {}  # node -> list of failure timestamps
        self.failure_threshold = 3  # Number of consecutive failures before marking as failed
        self.failed_nodes: set = set()

    def record_failure(self, node: str, failure_type: FailureType):
        """
        Record a failure for a node.
        """
        if node not in self.failure_history:
            self.failure_history[node] = []

        self.failure_history[node].append(time.time())

        # Check if node should be marked as failed
        recent_failures = [
            ts for ts in self.failure_history[node]
            if time.time() - ts < 60  # Last minute
        ]

        if len(recent_failures) >= self.failure_threshold:
            self.failed_nodes.add(node)

    def record_success(self, node: str):
        """
        Record a successful operation for a node.
        Clears failure history if node was previously failed.
        """
        if node in self.failed_nodes:
            self.failed_nodes.remove(node)
        if node in self.failure_history:
            self.failure_history[node] = []

    def is_node_failed(self, node: str) -> bool:
        """
        Check if a node is currently marked as failed.
        """
        return node in self.failed_nodes

    def get_failed_nodes(self) -> set:
        """
        Get set of currently failed nodes.
        """
        return self.failed_nodes.copy()


def with_timeout(
    func: Callable,
    timeout: float = DEFAULT_REQUEST_TIMEOUT,
    default_return: Any = None
) -> Any:
    """
    Execute a function with a timeout.
    Returns default_return if timeout occurs.
    """
    start_time = time.time()

    try:
        result = func()
        elapsed = time.time() - start_time

        if elapsed > timeout:
            return default_return

        return result
    except Exception:
        return default_return


def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    initial_delay: float = 0.1,
    timeout: float = DEFAULT_REQUEST_TIMEOUT
) -> Optional[Any]:
    """
    Retry a function with exponential backoff.
    """
    delay = initial_delay

    for attempt in range(max_retries):
        try:
            result = with_timeout(func, timeout)
            if result is not None:
                return result
        except Exception:
            pass

        if attempt < max_retries - 1:
            time.sleep(delay)
            delay *= 2  # Exponential backoff

    return None


def check_quorum_availability(
    total_nodes: int,
    failed_nodes: int,
    required_quorum: int
) -> bool:
    """
    Check if quorum is still achievable given failed nodes.
    """
    available_nodes = total_nodes - failed_nodes
    return available_nodes >= required_quorum

