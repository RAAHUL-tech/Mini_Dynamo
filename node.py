import sys
import argparse
from hash_ring import HashRing
from storage import Storage
from replication import ReplicationManager
from coordinator import Coordinator
from api import create_app


def main():
    """
    Usage:
      python node.py --port <port> [--nodes <node1,node2,node3>]
    Example:
      python node.py --port 5001
      python node.py --port 5001 --nodes 127.0.0.1:5001,127.0.0.1:5002,127.0.0.1:5003
      
    Legacy format (still supported):
      python node.py <node_id> <port> <node_list>
    """
    parser = argparse.ArgumentParser(description='Start a Mini Dynamo node')
    parser.add_argument('--port', type=int, help='Port to listen on')
    parser.add_argument('--nodes', type=str, 
                       default='127.0.0.1:5001,127.0.0.1:5002,127.0.0.1:5003',
                       help='Comma-separated list of all nodes in cluster')
    
    # Support legacy positional arguments
    if len(sys.argv) > 1 and not sys.argv[1].startswith('--'):
        # Legacy format: python node.py <node_id> <port> <node_list>
        if len(sys.argv) == 4:
            node_id = sys.argv[1]
            port = int(sys.argv[2])
            nodes = sys.argv[3].split(",")
        else:
            print("Usage: python node.py <node_id> <port> <node_list>")
            print("   or: python node.py --port <port> [--nodes <node_list>]")
            sys.exit(1)
    else:
        # New format with argparse
        args = parser.parse_args()
        if args.port is None:
            parser.print_help()
            sys.exit(1)
        
        port = args.port
        node_id = f"127.0.0.1:{port}"
        nodes = args.nodes.split(",")

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
