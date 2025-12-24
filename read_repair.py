from vector_clock import compare, VCComparison
from client_rpc import send_put

def perform_read_repair(key, latest_versions, replica_responses):
    """
    replica_responses: node -> versions (list of version dicts including tombstones)
    latest_versions: list of latest version dicts after conflict resolution
    
    Repairs all replica nodes by ensuring they have the latest versions.
    - If a node has no data (empty list), send all latest versions
    - If a node has outdated versions, send the latest versions
    - Handles tombstones properly (propagates deletions)
    
    Returns True if any repair was performed, False otherwise.
    """
    if not latest_versions:
        return False
    
    # Check if latest_versions contains only tombstones
    # If so, we need to propagate tombstones to all nodes
    all_tombstones = all(v.get("deleted", False) for v in latest_versions)
    
    repair_performed = False
    
    for node, versions in replica_responses.items():
        # Filter tombstones from node's versions for comparison
        node_non_tombstones = [v for v in versions if not v.get("deleted", False)]
        node_tombstones = [v for v in versions if v.get("deleted", False)]
        
        # Case 1: Node has no data - send all latest versions (including tombstones)
        if not versions or len(versions) == 0:
            for latest in latest_versions:
                send_put(node, key, latest)
            repair_performed = True
            continue
        
        # Case 2: If latest_versions are tombstones, ensure node has them
        if all_tombstones:
            # Check if node has the latest tombstone
            needs_repair = False
            for latest in latest_versions:
                found = False
                for v in node_tombstones:
                    if compare(v["vector_clock"], latest["vector_clock"]) == VCComparison.EQUAL:
                        found = True
                        break
                    elif compare(v["vector_clock"], latest["vector_clock"]) == VCComparison.IS_DOMINATED:
                        needs_repair = True
                        break
                if not found:
                    needs_repair = True
                    break
            
            if needs_repair:
                for latest in latest_versions:
                    send_put(node, key, latest)
                repair_performed = True
            continue
        
        # Case 3: Node has tombstones but latest_versions are not tombstones
        # This means key was recreated after deletion - remove old tombstones
        if node_tombstones and not all_tombstones:
            # Node has outdated tombstones, needs repair
            for latest in latest_versions:
                send_put(node, key, latest)
            repair_performed = True
            continue
        
        # Case 4: Node has data - check if any version is outdated
        needs_repair = False
        for v in node_non_tombstones:
            for latest in latest_versions:
                comparison = compare(v["vector_clock"], latest["vector_clock"])
                if comparison == VCComparison.IS_DOMINATED:
                    needs_repair = True
                    break
            if needs_repair:
                break
        
        # Case 5: Node is missing latest versions (check if latest versions exist in node)
        if not needs_repair:
            for latest in latest_versions:
                found = False
                for v in node_non_tombstones:
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
            repair_performed = True
    
    return repair_performed
