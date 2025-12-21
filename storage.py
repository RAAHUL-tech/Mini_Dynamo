from typing import Dict, List
from threading import Lock


class Storage:
    """
    In-memory key-value store.
    Each key can have multiple versions (siblings).
    """

    def __init__(self):
        self.store: Dict[str, List[dict]] = {}
        self.lock = Lock()

    def put(self, key: str, versioned_value: dict):
        """
        Store a versioned value.
        versioned_value must include:
        {
            "value": any,
            "vector_clock": dict
        }
        """
        with self.lock:
            if key not in self.store:
                self.store[key] = []

            self.store[key].append(versioned_value)

    def get(self, key: str) -> List[dict]:
        """
        Return all versions for a key
        """
        with self.lock:
            return list(self.store.get(key, []))

    def overwrite(self, key: str, versions: List[dict]):
        """
        Replace all versions for a key (used after conflict resolution)
        """
        with self.lock:
            self.store[key] = versions

    def delete(self, key: str):
        with self.lock:
            if key in self.store:
                del self.store[key]
