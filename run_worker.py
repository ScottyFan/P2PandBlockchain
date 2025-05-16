import sys
import os
import argparse
import time
import signal

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from p2p_network.worker.worker_node import WorkerNode


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\nShutting down worker node...")
    if worker_node:
        worker_node.stop()
    sys.exit(0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run a P2P worker node')
    parser.add_argument('--node-id', type=str, help='Node ID (generated if not provided)')
    parser.add_argument('--supernode-url', type=str, default='http://localhost:5000',
                       help='Supernode URL (default: http://localhost:5000)')
    parser.add_argument('--port', type=int, default=8080,
                       help='Worker node port (default: 8080)')
    parser.add_argument('--capabilities', type=str, nargs='+',
                       default=['python', 'javascript'],
                       help='Node capabilities (default: python javascript)')
    
    args = parser.parse_args()
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and start worker node
    worker_node = WorkerNode(
        node_id=args.node_id,
        port=args.port,
        capabilities=args.capabilities
    )
    
    print(f"Starting worker node {worker_node.node_id}...")
    
    # Register with supernode
    if worker_node.register_with_supernode(args.supernode_url):
        print(f"Successfully registered with supernode at {args.supernode_url}")
        
        # Start worker operations
        worker_node.start()
        
        print(f"Worker node {worker_node.node_id} is running. Press Ctrl+C to stop.")
        
        # Keep the main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
    else:
        print("Failed to register with supernode. Exiting.")
        sys.exit(1)