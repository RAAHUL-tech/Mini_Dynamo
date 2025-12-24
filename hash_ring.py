import hashlib
import bisect
from typing import List, Dict
from config import DEFAULT_VNODES


class HashRing:
    """
    Consistent Hash Ring with Virtual Nodes
    """

    def __init__(self, nodes: List[str], vnodes: int = DEFAULT_VNODES):
        """
        nodes  : list of physical node identifiers (e.g. "127.0.0.1:5001")
        vnodes : number of virtual nodes per physical node
        """
        self.vnodes = vnodes
        self.ring: Dict[int, str] = {}      # hash -> physical node
        self.sorted_keys: List[int] = []    # sorted hashes

        for node in nodes:
            self.add_node(node)

    def _hash(self, key: str) -> int:
        """
        Returns a 32-bit hash of the given key
        """
        return int(hashlib.md5(key.encode()).hexdigest(), 16) % (2 ** 32)

    def add_node(self, node: str):
        """
        Add a physical node with multiple virtual nodes
        """
        for i in range(self.vnodes):
            vnode_key = f"{node}#{i}"
            h = self._hash(vnode_key)
            self.ring[h] = node
            bisect.insort(self.sorted_keys, h)

    def remove_node(self, node: str):
        """
        Remove a physical node and all its virtual nodes
        """
        for i in range(self.vnodes):
            vnode_key = f"{node}#{i}"
            h = self._hash(vnode_key)
            if h in self.ring:
                self.ring.pop(h)
                self.sorted_keys.remove(h)

    def get_nodes_for_key(self, key: str, n: int) -> List[str]:
        """
        Return N unique physical nodes responsible for the key
        """
        if not self.ring:
            return []

        h = self._hash(key)
        idx = bisect.bisect(self.sorted_keys, h)

        result = []
        visited = set()

        while len(result) < n:
            if idx == len(self.sorted_keys):
                idx = 0

            node = self.ring[self.sorted_keys[idx]]
            if node not in visited:
                visited.add(node)
                result.append(node)

            idx += 1

        return result
