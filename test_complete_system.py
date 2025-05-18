import time
import logging
import requests
import threading
import sys
import os
import json
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from p2p_network.supernode.api import app
from p2p_network.worker.worker_node import WorkerNode

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def start_supernode():
    app.run(host='0.0.0.0', port=5000, debug=False)

def main():
    # Start supernode in a separate thread
    supernode_thread = threading.Thread(target=start_supernode)
    supernode_thread.daemon = True
    supernode_thread.start()
    
    logger.info("Starting supernode... waiting for it to initialize")
    time.sleep(3) 
    
    worker = WorkerNode(
        node_id="test-integration-worker",
        port=8082,
        capabilities=["python", "javascript"],
        max_concurrent_tasks=3
    )
    
    worker.task_poll_interval = 2
    worker.heartbeat_interval = 5
    
    if worker.register_with_supernode("http://localhost:5000"):
        logger.info(f"Worker registered with ID: {worker.node_id}")
        worker.start()
    else:
        logger.error("Failed to register worker. Is the supernode running?")
        return
    
    logger.info("Creating test tasks...")
    
    task_ids = []
    for i in range(3):
        response = requests.post(
            "http://localhost:5000/create_task",
            json={
                "code_url": f"https://github.com/example/test-repo-{i}.git",
                "analysis_type": "security_scan",
                "deadline": "2025-05-20T12:00:00Z",
                "commit_id": f"commit-{i}"
            }
        )
        
        if response.status_code == 201:
            task_data = response.json()
            task_id = task_data["task_id"]
            task_ids.append(task_id)
            logger.info(f"Created task {i+1}: {task_id}")
        else:
            logger.error(f"Failed to create task {i+1}: {response.text}")
    
    logger.info("Waiting for tasks to be processed...")
    time.sleep(15) 
    
    logger.info("Checking blockchain records...")
    
    blockchain_response = requests.get("http://localhost:5000/blockchain/blocks")
    if blockchain_response.status_code == 200:
        blockchain_data = blockchain_response.json()
        logger.info(f"Blockchain has {blockchain_data['block_count']} blocks")
        
        if blockchain_data['block_count'] >= 4:
            logger.info("✅ Blockchain has correct number of blocks")
        else:
            logger.warning("❌ Blockchain is missing expected blocks")
            
        # Print a summary of blocks
        for block in blockchain_data['blocks']:
            if block['index'] == 0:
                logger.info(f"Block #{block['index']}: Genesis Block")
            else:
                status = block['data'].get('status', 'unknown')
                review_id = block['data'].get('review_id', 'unknown')
                timestamp = datetime.fromtimestamp(block['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
                logger.info(f"Block #{block['index']}: Review {review_id} - Status: {status} at {timestamp}")
    else:
        logger.error(f"Failed to get blockchain blocks: {blockchain_response.text}")
    
    validation_response = requests.get("http://localhost:5000/blockchain/validate")
    if validation_response.status_code == 200:
        validation_data = validation_response.json()
        if validation_data['is_valid']:
            logger.info("✅ Blockchain integrity valid")
        else:
            logger.error("❌ Blockchain integrity check failed")
    else:
        logger.error(f"Failed to validate blockchain: {validation_response.text}")
    
    status_response = requests.get("http://localhost:5000/status")
    if status_response.status_code == 200:
        status_data = status_response.json()
        logger.info(f"Supernode status: {json.dumps(status_data, indent=2)}")
    else:
        logger.error(f"Failed to get status: {status_response.text}")
    
    logger.info("Stopping worker...")
    worker.stop()
    
    logger.info("Test complete!")

if __name__ == "__main__":
    main()
