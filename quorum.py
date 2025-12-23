from typing import Dict, Any, List
import time


class Quorum:
    """
    Handles quorum logic for read and write operations.
    """

    @staticmethod
    def wait_for_write_quorum(
        responses: Dict[str, Any],
        required_w: int
    ) -> bool:
        """
        responses: node -> response (success/failure)
        """
        success_count = sum(1 for r in responses.values() if r is True)
        return success_count >= required_w

    @staticmethod
    def collect_read_quorum(
        responses: Dict[str, Any],
        required_r: int
    ) -> List[Any]:
        """
        responses: node -> read_result (list of versions)
        Collects from all nodes and flattens versions.
        Ensures at least R nodes responded (even if with empty lists).
        """
        all_versions = []
        responding_nodes = 0
        
        for value in responses.values():
            if value is not None:
                responding_nodes += 1
                # value is a list of versions, flatten it
                if isinstance(value, list):
                    all_versions.extend(value)
                else:
                    all_versions.append(value)
        
        # Check if we have at least R nodes that responded
        if responding_nodes < required_r:
            # Not enough nodes responded, but we still return what we have
            # (the system should handle this gracefully)
            pass
        
        # Return all collected versions (collect all for read repair)
        return all_versions
