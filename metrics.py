"""
Performance and availability metrics
"""

import time
from typing import Dict, List, Optional
from threading import RLock
from collections import defaultdict, deque


class Metrics:
    """
    Tracks performance and availability metrics for the node.
    """

    def __init__(self):
        # RLock avoids deadlocks when aggregated getters call other getters
        self.lock = RLock()

        # Operation counters
        self.read_count = 0
        self.write_count = 0
        self.read_repair_count = 0
        self.conflict_count = 0
        self.failure_count = 0

        # Latency tracking (using deque for rolling window)
        self.read_latencies: deque = deque(maxlen=1000)
        self.write_latencies: deque = deque(maxlen=1000)

        # Quorum success/failure tracking
        self.read_quorum_success = 0
        self.read_quorum_failure = 0
        self.write_quorum_success = 0
        self.write_quorum_failure = 0

        # Node-specific metrics
        self.node_responses: Dict[str, Dict[str, int]] = defaultdict(
            lambda: {"success": 0, "failure": 0, "timeout": 0}
        )

    def record_read(self, latency_ms: float, quorum_success: bool):
        """Record a read operation"""
        with self.lock:
            self.read_count += 1
            self.read_latencies.append(latency_ms)
            if quorum_success:
                self.read_quorum_success += 1
            else:
                self.read_quorum_failure += 1

    def record_write(self, latency_ms: float, quorum_success: bool):
        """Record a write operation"""
        with self.lock:
            self.write_count += 1
            self.write_latencies.append(latency_ms)
            if quorum_success:
                self.write_quorum_success += 1
            else:
                self.write_quorum_failure += 1

    def record_read_repair(self):
        """Record a read repair operation"""
        with self.lock:
            self.read_repair_count += 1

    def record_conflict(self):
        """Record a conflict detection"""
        with self.lock:
            self.conflict_count += 1

    def record_failure(self):
        """Record a general failure"""
        with self.lock:
            self.failure_count += 1

    def record_node_response(self, node: str, success: bool, timeout: bool = False):
        """Record a response from a specific node"""
        with self.lock:
            if timeout:
                self.node_responses[node]["timeout"] += 1
            elif success:
                self.node_responses[node]["success"] += 1
            else:
                self.node_responses[node]["failure"] += 1

    def get_read_latency_stats(self) -> Dict[str, float]:
        """Get read latency statistics"""
        with self.lock:
            if not self.read_latencies:
                return {"avg": 0.0, "min": 0.0, "max": 0.0, "p95": 0.0}

            latencies = list(self.read_latencies)
            latencies.sort()

            return {
                "avg": sum(latencies) / len(latencies),
                "min": latencies[0],
                "max": latencies[-1],
                "p95": latencies[int(len(latencies) * 0.95)] if latencies else 0.0
            }

    def get_write_latency_stats(self) -> Dict[str, float]:
        """Get write latency statistics"""
        with self.lock:
            if not self.write_latencies:
                return {"avg": 0.0, "min": 0.0, "max": 0.0, "p95": 0.0}

            latencies = list(self.write_latencies)
            latencies.sort()

            return {
                "avg": sum(latencies) / len(latencies),
                "min": latencies[0],
                "max": latencies[-1],
                "p95": latencies[int(len(latencies) * 0.95)] if latencies else 0.0
            }

    def get_read_success_rate(self) -> float:
        """Get read quorum success rate"""
        with self.lock:
            total = self.read_quorum_success + self.read_quorum_failure
            if total == 0:
                return 0.0
            return self.read_quorum_success / total

    def get_write_success_rate(self) -> float:
        """Get write quorum success rate"""
        with self.lock:
            total = self.write_quorum_success + self.write_quorum_failure
            if total == 0:
                return 0.0
            return self.write_quorum_success / total

    def get_node_health(self, node: str) -> Dict[str, float]:
        """Get health metrics for a specific node"""
        with self.lock:
            stats = self.node_responses[node]
            total = stats["success"] + stats["failure"] + stats["timeout"]
            if total == 0:
                return {"success_rate": 0.0, "timeout_rate": 0.0}

            return {
                "success_rate": stats["success"] / total,
                "timeout_rate": stats["timeout"] / total,
                "total_requests": total
            }

    def get_summary(self) -> Dict:
        """Get a summary of all metrics"""
        with self.lock:
            return {
                "operations": {
                    "reads": self.read_count,
                    "writes": self.write_count,
                    "read_repairs": self.read_repair_count,
                    "conflicts": self.conflict_count,
                    "failures": self.failure_count
                },
                "quorum_rates": {
                    "read_success_rate": self.get_read_success_rate(),
                    "write_success_rate": self.get_write_success_rate()
                },
                "latency": {
                    "read": self.get_read_latency_stats(),
                    "write": self.get_write_latency_stats()
                },
                "node_health": {
                    node: self.get_node_health(node)
                    for node in self.node_responses.keys()
                }
            }

    def reset(self):
        """Reset all metrics"""
        with self.lock:
            self.read_count = 0
            self.write_count = 0
            self.read_repair_count = 0
            self.conflict_count = 0
            self.failure_count = 0
            self.read_latencies.clear()
            self.write_latencies.clear()
            self.read_quorum_success = 0
            self.read_quorum_failure = 0
            self.write_quorum_success = 0
            self.write_quorum_failure = 0
            self.node_responses.clear()


# Global metrics instance (can be shared across modules)
_global_metrics: Optional[Metrics] = None


def get_metrics() -> Metrics:
    """Get the global metrics instance"""
    global _global_metrics
    if _global_metrics is None:
        _global_metrics = Metrics()
    return _global_metrics


def reset_metrics():
    """Reset the global metrics instance"""
    global _global_metrics
    if _global_metrics is not None:
        _global_metrics.reset()

