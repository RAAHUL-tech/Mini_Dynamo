import requests
from typing import Any, Dict, List
from config import DEFAULT_REQUEST_TIMEOUT
from failure import FailureDetector, FailureType
from metrics import get_metrics


# Global failure detector instance
_failure_detector = FailureDetector(timeout=DEFAULT_REQUEST_TIMEOUT)


def send_put(node: str, key: str, payload: Dict[str, Any], timeout: float = DEFAULT_REQUEST_TIMEOUT) -> bool:
    """
    Send PUT request to another node.
    Returns True if successful, False otherwise.
    """
    url = f"http://{node}/internal/kv/{key}"

    try:
        resp = requests.put(url, json=payload, timeout=timeout)
        success = resp.status_code == 200
        
        if success:
            _failure_detector.record_success(node)
            get_metrics().record_node_response(node, success=True)
        else:
            _failure_detector.record_failure(node, FailureType.NETWORK_ERROR)
            get_metrics().record_node_response(node, success=False)
        
        return success
    except requests.Timeout:
        _failure_detector.record_failure(node, FailureType.TIMEOUT)
        get_metrics().record_node_response(node, success=False, timeout=True)
        return False
    except requests.RequestException:
        _failure_detector.record_failure(node, FailureType.NETWORK_ERROR)
        get_metrics().record_node_response(node, success=False)
        return False


def send_get(node: str, key: str, timeout: float = DEFAULT_REQUEST_TIMEOUT) -> List[Dict[str, Any]]:
    """
    Send GET request to another node.
    Returns list of versions or empty list on failure.
    """
    url = f"http://{node}/internal/kv/{key}"

    try:
        resp = requests.get(url, timeout=timeout)
        if resp.status_code == 200:
            _failure_detector.record_success(node)
            get_metrics().record_node_response(node, success=True)
            return resp.json().get("versions", [])
        else:
            _failure_detector.record_failure(node, FailureType.NETWORK_ERROR)
            get_metrics().record_node_response(node, success=False)
            return []
    except requests.Timeout:
        _failure_detector.record_failure(node, FailureType.TIMEOUT)
        get_metrics().record_node_response(node, success=False, timeout=True)
        return []
    except requests.RequestException:
        _failure_detector.record_failure(node, FailureType.NETWORK_ERROR)
        get_metrics().record_node_response(node, success=False)
        return []


def get_failure_detector() -> FailureDetector:
    """
    Get the global failure detector instance.
    """
    return _failure_detector