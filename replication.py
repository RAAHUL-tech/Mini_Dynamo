from typing import List
from hash_ring import HashRing


class ReplicationManager:
    """
    Responsible for selecting replica nodes for a given key.
    """

    def __init__(self, hash_ring: HashRing):
        self.hash_ring = hash_ring

    def get_replicas(self, key: str, n: int) -> List[str]:
        """
        Return N unique physical nodes responsible for the key.
        """
        return self.hash_ring.get_nodes_for_key(key, n)
