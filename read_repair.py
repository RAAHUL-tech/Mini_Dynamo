from vector_clock import compare, VCComparison
from client_rpc import send_put

def perform_read_repair(key, latest_versions, replica_responses):
    """
    replica_responses: node -> versions
    """
    for node, versions in replica_responses.items():
        for v in versions:
            for latest in latest_versions:
                if compare(v["vector_clock"], latest["vector_clock"]) == VCComparison.IS_DOMINATED:
                    send_put(node, key, latest)
