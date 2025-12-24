"""
Cluster configuration (ports, N/R/W defaults)
"""

# Default replication and quorum parameters
DEFAULT_N = 3  # Replication factor (total replicas)
DEFAULT_R = 2  # Read quorum (replicas that must respond)
DEFAULT_W = 2  # Write quorum (replicas that must acknowledge)

# Network configuration
DEFAULT_PORT = 5001
DEFAULT_HOST = "0.0.0.0"

# Request timeout configuration (in seconds)
DEFAULT_REQUEST_TIMEOUT = 0.3

# Consistent hashing configuration
DEFAULT_VNODES = 100  # Number of virtual nodes per physical node

# Cluster membership (can be overridden at runtime)
# Format: ["127.0.0.1:5001", "127.0.0.1:5002", "127.0.0.1:5003"]
DEFAULT_CLUSTER_NODES = []


class ClusterConfig:
    """
    Cluster configuration manager.
    Allows runtime configuration of cluster parameters.
    """

    def __init__(
        self,
        n: int = DEFAULT_N,
        r: int = DEFAULT_R,
        w: int = DEFAULT_W,
        request_timeout: float = DEFAULT_REQUEST_TIMEOUT,
        vnodes: int = DEFAULT_VNODES
    ):
        self.n = n
        self.r = r
        self.w = w
        self.request_timeout = request_timeout
        self.vnodes = vnodes

    def validate_quorum(self) -> bool:
        """
        Validates that R + W > N for strong consistency.
        Returns True if valid, False otherwise.
        """
        return (self.r + self.w) > self.n

    def get_consistency_level(self) -> str:
        """
        Returns the consistency level based on R, W, N values.
        """
        if self.validate_quorum():
            return "strong"
        return "eventual"

