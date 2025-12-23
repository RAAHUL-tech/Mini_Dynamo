from typing import Dict, List
from read_repair import perform_read_repair
from replication import ReplicationManager
from quorum import Quorum
from vector_clock import increment, compare, VCComparison, merge
from storage import Storage
from client_rpc import send_put, send_get
from conflict_resolution import resolve_versions


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
        replicas = self.replication.get_replicas(key, n)

        # Merge existing vector clocks
        existing_versions = self.storage.get(key)
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

        return Quorum.wait_for_write_quorum(responses, w)

    # ---------------- READ PATH ---------------- #

    def handle_get(self, key: str, r: int, n: int = 3) -> List[dict]:
        replicas = self.replication.get_replicas(key, n)
        responses: Dict[str, List[dict]] = {}

        for node in replicas:
            if node == self.node_id:
                responses[node] = self.storage.get(key)
            else:
                responses[node] = send_get(node, key)

        read_versions = Quorum.collect_read_quorum(responses, r)
        resolved_versions = resolve_versions(read_versions)
        perform_read_repair(
            key=key,
            latest_versions=resolved_versions,
            replica_responses=responses
            )


        return resolved_versions