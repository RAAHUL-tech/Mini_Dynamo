from vector_clock import compare, VCComparison
from client_rpc import send_put

def perform_read_repair(key, latest_versions, replica_responses):
    """
    replica_responses: node -> versions (list of version dicts)
    latest_versions: list of latest version dicts after conflict resolution
    
    Repairs all replica nodes by ensuring they have the latest versions.
    - If a node has no data (empty list), send all latest versions
    - If a node has outdated versions, send the latest versions
    """
    if not latest_versions:
        return
    
    for node, versions in replica_responses.items():
        # Case 1: Node has no data - send all latest versions
        if not versions or len(versions) == 0:
            for latest in latest_versions:
                send_put(node, key, latest)
            continue
        
        # Case 2: Node has data - check if any version is outdated
        needs_repair = False
        for v in versions:
            for latest in latest_versions:
                comparison = compare(v["vector_clock"], latest["vector_clock"])
                if comparison == VCComparison.IS_DOMINATED:
                    needs_repair = True
                    break
            if needs_repair:
                break
        
        # Case 3: Node is missing latest versions (check if latest versions exist in node)
        if not needs_repair:
            for latest in latest_versions:
                found = False
                for v in versions:
                    if compare(v["vector_clock"], latest["vector_clock"]) == VCComparison.EQUAL:
                        found = True
                        break
                if not found:
                    needs_repair = True
                    break
        
        # Send all latest versions if repair is needed
        if needs_repair:
            for latest in latest_versions:
                send_put(node, key, latest)
