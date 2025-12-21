from enum import Enum
from typing import Dict


class VCComparison(Enum):
    DOMINATES = 1
    IS_DOMINATED = 2
    CONCURRENT = 3
    EQUAL = 4


def increment(vc: Dict[str, int], node_id: str) -> Dict[str, int]:
    """
    Increment the vector clock for the given node
    """
    new_vc = vc.copy()
    new_vc[node_id] = new_vc.get(node_id, 0) + 1
    return new_vc


def merge(vc1: Dict[str, int], vc2: Dict[str, int]) -> Dict[str, int]:
    """
    Merge two vector clocks by taking max for each node
    """
    merged = {}
    all_nodes = set(vc1.keys()) | set(vc2.keys())

    for node in all_nodes:
        merged[node] = max(vc1.get(node, 0), vc2.get(node, 0))

    return merged


def compare(vc1: Dict[str, int], vc2: Dict[str, int]) -> VCComparison:
    """
    Compare two vector clocks.
    Returns:
      - DOMINATES        : vc1 happened-after vc2
      - IS_DOMINATED     : vc1 happened-before vc2
      - CONCURRENT       : concurrent updates
      - EQUAL            : same version
    """
    vc1_bigger = False
    vc2_bigger = False

    all_nodes = set(vc1.keys()) | set(vc2.keys())

    for node in all_nodes:
        c1 = vc1.get(node, 0)
        c2 = vc2.get(node, 0)

        if c1 > c2:
            vc1_bigger = True
        elif c2 > c1:
            vc2_bigger = True

    if vc1_bigger and not vc2_bigger:
        return VCComparison.DOMINATES
    if vc2_bigger and not vc1_bigger:
        return VCComparison.IS_DOMINATED
    if not vc1_bigger and not vc2_bigger:
        return VCComparison.EQUAL

    return VCComparison.CONCURRENT
