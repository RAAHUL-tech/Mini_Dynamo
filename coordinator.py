import time
from typing import Dict, List
from read_repair import perform_read_repair
from replication import ReplicationManager
from quorum import Quorum
from vector_clock import increment, compare, VCComparison, merge
from storage import Storage
from client_rpc import send_put, send_get
from conflict_resolution import resolve_versions
from metrics import get_metrics
from utils import format_latency_ms


class Coordinator:
    """
    Acts as coordinator for read/write requests.
    """

    def __init__(
        self,
        node_id: str,
        storage: Storage,
        replication_manager: ReplicationManager
    ):
        self.node_id = node_id
        self.storage = storage
        self.replication = replication_manager

    # ---------------- WRITE PATH ---------------- #

    def handle_put(self, key: str, value, n: int, w: int) -> bool:
        start_time = time.time()
        metrics = get_metrics()

        replicas = self.replication.get_replicas(key, n)

        # Fetch existing versions (including tombstones) from all replicas to merge vector clocks properly
        existing_versions = []
        
        # Get all local versions including tombstones
        local_versions = self.storage.get_all(key)
        existing_versions.extend(local_versions)
        
        # Fetch all versions from other replicas (including tombstones for vector clock merging)
        for node in replicas:
            if node != self.node_id:
                # send_get now returns all versions including tombstones (via internal_get)
                remote_versions = send_get(node, key)
                existing_versions.extend(remote_versions)
        
        # Merge all existing vector clocks
        merged_vc = {}
        for v in existing_versions:
            merged_vc = merge(merged_vc, v["vector_clock"])

        new_vc = increment(merged_vc, self.node_id)

        payload = {
            "value": value,
            "vector_clock": new_vc
        }

        responses: Dict[str, bool] = {}

        for node in replicas:
            if node == self.node_id:
                self.storage.put(key, payload)
                responses[node] = True
            else:
                responses[node] = send_put(node, key, payload)

        success = Quorum.wait_for_write_quorum(responses, w)
        
        # Record metrics
        latency_ms = format_latency_ms(time.time() - start_time)
        metrics.record_write(latency_ms, success)
        
        return success

    # ---------------- READ PATH ---------------- #

    def handle_get(self, key: str, r: int, n: int = 3) -> List[dict]:
        start_time = time.time()
        metrics = get_metrics()

        replicas = self.replication.get_replicas(key, n)
        responses: Dict[str, List[dict]] = {}

        # Get all versions including tombstones from all replicas
        for node in replicas:
            if node == self.node_id:
                # Get all versions including tombstones for internal processing
                all_versions = self.storage.get_all(key)
                responses[node] = all_versions
            else:
                # send_get calls internal_get which now returns all versions including tombstones
                responses[node] = send_get(node, key)

        read_versions, quorum_met = Quorum.collect_read_quorum(responses, r)
        
        # If quorum not met, return empty (or could raise exception)
        if not quorum_met:
            metrics.record_read(format_latency_ms(time.time() - start_time), False)
            return []
        
        # Resolve all versions (including tombstones) to get the latest
        all_resolved = resolve_versions(read_versions)
        
        # Separate tombstones from non-tombstones
        resolved_tombstones = [v for v in all_resolved if v.get("deleted", False)]
        resolved_non_tombstones = [v for v in all_resolved if not v.get("deleted", False)]
        
        # If we have both tombstones and non-tombstones, compare their vector clocks
        # The latest version (by vector clock) wins
        if resolved_tombstones and resolved_non_tombstones:
            # Compare the latest tombstone with latest non-tombstone
            latest_tombstone = max(resolved_tombstones, 
                                 key=lambda v: sum(v["vector_clock"].values()))
            latest_non_tombstone = max(resolved_non_tombstones,
                                     key=lambda v: sum(v["vector_clock"].values()))
            
            comparison = compare(latest_tombstone["vector_clock"], 
                                latest_non_tombstone["vector_clock"])
            
            if comparison == VCComparison.DOMINATES or comparison == VCComparison.EQUAL:
                # Tombstone is latest or equal - key is deleted
                resolved_versions = resolved_tombstones
            else:
                # Non-tombstone is latest - key exists
                resolved_versions = resolved_non_tombstones
        elif resolved_tombstones:
            # Only tombstones - key is deleted
            resolved_versions = resolved_tombstones
        else:
            # Only non-tombstones - key exists
            resolved_versions = resolved_non_tombstones
        
        # If latest version is a tombstone, return empty to client
        if resolved_versions and all(v.get("deleted", False) for v in resolved_versions):
            # Perform read repair with tombstones to propagate deletion
            perform_read_repair(
                key=key,
                latest_versions=resolved_versions,
                replica_responses=responses
            )
            metrics.record_read(format_latency_ms(time.time() - start_time), quorum_met)
            return []
        
        # If we get here, we have non-tombstone versions
        if not resolved_versions:
            metrics.record_read(format_latency_ms(time.time() - start_time), quorum_met)
            return []
        
        # Check for conflicts (multiple versions means conflict)
        if len(resolved_versions) > 1:
            metrics.record_conflict()
        
        # Check if read repair was needed
        repair_needed = perform_read_repair(
            key=key,
            latest_versions=resolved_versions,
            replica_responses=responses
        )
        
        if repair_needed:
            metrics.record_read_repair()

        # Record metrics
        latency_ms = format_latency_ms(time.time() - start_time)
        metrics.record_read(latency_ms, quorum_met)

        return resolved_versions

    # ---------------- DELETE PATH ---------------- #

    def handle_delete(self, key: str, n: int, w: int) -> bool:
        """
        Delete a key using tombstone approach for eventual consistency.
        Creates a tombstone marker instead of immediate deletion.
        """
        start_time = time.time()
        metrics = get_metrics()

        replicas = self.replication.get_replicas(key, n)

        # Fetch existing versions (including tombstones) to merge vector clocks
        existing_versions = []
        # Get all versions including tombstones for proper vector clock merging
        local_versions = self.storage.get_all(key)
        existing_versions.extend(local_versions)
        
        for node in replicas:
            if node != self.node_id:
                # send_get now returns all versions including tombstones (via internal_get)
                remote_versions = send_get(node, key)
                existing_versions.extend(remote_versions)
        
        # Merge vector clocks
        merged_vc = {}
        for v in existing_versions:
            merged_vc = merge(merged_vc, v["vector_clock"])

        new_vc = increment(merged_vc, self.node_id)

        # Create tombstone (marker for deletion)
        tombstone = {
            "value": None,  # None indicates tombstone
            "vector_clock": new_vc,
            "deleted": True
        }

        responses: Dict[str, bool] = {}

        for node in replicas:
            if node == self.node_id:
                # Store tombstone locally
                self.storage.put(key, tombstone)
                responses[node] = True
            else:
                responses[node] = send_put(node, key, tombstone)

        success = Quorum.wait_for_write_quorum(responses, w)
        
        # Record metrics (treat as write operation)
        latency_ms = format_latency_ms(time.time() - start_time)
        metrics.record_write(latency_ms, success)
        
        return success