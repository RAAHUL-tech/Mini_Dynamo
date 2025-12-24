"""
Shared utility functions
"""

import hashlib
import json
from typing import Any, Dict, List, Optional, Tuple


def hash_key(key: str) -> int:
    """
    Hash a key to a 32-bit integer.
    Uses MD5 for consistent hashing.
    """
    return int(hashlib.md5(key.encode()).hexdigest(), 16) % (2 ** 32)


def parse_node_id(node_str: str) -> Tuple[str, int]:
    """
    Parse a node identifier string into (host, port) tuple.
    Expected format: "host:port" or "127.0.0.1:5001"
    """
    if ":" not in node_str:
        raise ValueError(f"Invalid node format: {node_str}. Expected 'host:port'")

    host, port_str = node_str.rsplit(":", 1)
    try:
        port = int(port_str)
    except ValueError:
        raise ValueError(f"Invalid port in node: {node_str}")

    return (host, port)


def format_node_id(host: str, port: int) -> str:
    """
    Format (host, port) tuple into node identifier string.
    """
    return f"{host}:{port}"


def validate_quorum_params(n: int, r: int, w: int) -> bool:
    """
    Validate quorum parameters.
    Returns True if valid, False otherwise.
    """
    if n <= 0 or r <= 0 or w <= 0:
        return False
    if r > n or w > n:
        return False
    return True


def ensure_quorum_consistency(n: int, r: int, w: int) -> bool:
    """
    Check if R + W > N for strong consistency.
    """
    return (r + w) > n


def serialize_value(value: Any) -> str:
    """
    Serialize a value to JSON string.
    """
    return json.dumps(value)


def deserialize_value(value_str: str) -> Any:
    """
    Deserialize a JSON string to Python value.
    """
    return json.loads(value_str)


def merge_dicts(dict1: Dict, dict2: Dict) -> Dict:
    """
    Merge two dictionaries, with dict2 values taking precedence.
    """
    result = dict1.copy()
    result.update(dict2)
    return result


def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """
    Split a list into chunks of specified size.
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def get_first_n_unique(items: List, n: int) -> List:
    """
    Get first N unique items from a list.
    Preserves order.
    """
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
            if len(result) >= n:
                break
    return result


def safe_get(dictionary: Dict, key: str, default: Any = None) -> Any:
    """
    Safely get a value from a dictionary with a default.
    """
    return dictionary.get(key, default)


def format_latency_ms(seconds: float) -> float:
    """
    Convert seconds to milliseconds.
    """
    return seconds * 1000.0


def format_bytes(bytes_count: int) -> str:
    """
    Format byte count to human-readable string.
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_count < 1024.0:
            return f"{bytes_count:.2f} {unit}"
        bytes_count /= 1024.0
    return f"{bytes_count:.2f} PB"


def is_valid_key(key: str) -> bool:
    """
    Validate that a key is non-empty and doesn't contain invalid characters.
    """
    if not key or not isinstance(key, str):
        return False
    # Basic validation - can be extended
    if len(key) > 1024:  # Reasonable key length limit
        return False
    return True


def normalize_node_list(nodes: List[str]) -> List[str]:
    """
    Normalize a list of node identifiers.
    Removes duplicates and validates format.
    """
    normalized = []
    seen = set()

    for node in nodes:
        node = node.strip()
        if not node:
            continue

        # Validate format
        try:
            parse_node_id(node)
        except ValueError:
            continue

        if node not in seen:
            seen.add(node)
            normalized.append(node)

    return normalized

