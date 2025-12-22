import requests
from typing import Any, Dict, List

# Default timeout in seconds (keep small for availability)
REQUEST_TIMEOUT = 0.3


def send_put(node: str, key: str, payload: Dict[str, Any]) -> bool:
    """
    Send PUT request to another node.
    Returns True if successful, False otherwise.
    """
    url = f"http://{node}/internal/kv/{key}"

    try:
        resp = requests.put(url, json=payload, timeout=REQUEST_TIMEOUT)
        return resp.status_code == 200
    except requests.RequestException:
        # Node unreachable / timeout
        return False


def send_get(node: str, key: str) -> List[Dict[str, Any]]:
    """
    Send GET request to another node.
    Returns list of versions or empty list on failure.
    """
    url = f"http://{node}/internal/kv/{key}"

    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        if resp.status_code == 200:
            return resp.json().get("versions", [])
        return []
    except requests.RequestException:
        return []