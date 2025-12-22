import sys
from hash_ring import HashRing
from storage import Storage
from replication import ReplicationManager
from coordinator import Coordinator
from api import create_app


def main():
    """
    Usage:
      python node.py <node_id> <port> <node1,node2,node3>
    Example:
      python node.py 127.0.0.1:5001 5001 127.0.0.1:5001,127.0.0.1:5002,127.0.0.1:5003
    """
    if len(sys.argv) != 4:
        print("Usage: python node.py <node_id> <port> <node_list>")
        sys.exit(1)

    node_id = sys.argv[1]
    port = int(sys.argv[2])
    nodes = sys.argv[3].split(",")

    # ---------- Initialize Core Components ----------

    hash_ring = HashRing(nodes)
    storage = Storage()
    replication_manager = ReplicationManager(hash_ring)

    coordinator = Coordinator(
        node_id=node_id,
        storage=storage,
        replication_manager=replication_manager
    )

    app = create_app(coordinator)

    print(f"[INFO] Node {node_id} starting on port {port}")
    app.run(host="0.0.0.0", port=port, threaded=True)


if __name__ == "__main__":
    main()
