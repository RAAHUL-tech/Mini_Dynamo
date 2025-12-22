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
        responses: node -> read_result
        """
        results = []
        for value in responses.values():
            if value is not None:
                results.append(value)
            if len(results) >= required_r:
                break
        return results
