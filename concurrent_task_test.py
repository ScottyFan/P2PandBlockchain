# Simple Concurrent Task Test
"""
Simple test for concurrent task processing
"""
import time
import logging
import requests
import threading
from p2p_network.worker.worker_node import WorkerNode

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    # Ensure supernode is running on default port
    try:
        response = requests.get("http://localhost:5000/status")
        if response.status_code != 200:
            logger.error("Supernode not running or not responding")
            return
    except Exception as e:
        logger.error(f"Supernode connection error: {e}")
        logger.error("Make sure to run the supernode first: python3 run_supernode.py")
        return
    
    logger.info("Creating concurrent worker...")
    
    # Create worker with multiple concurrent tasks capability
    worker = WorkerNode(
        node_id="concurrent-worker",
        port=8888,
        max_concurrent_tasks=5,  # Handle up to 5 concurrent tasks
        capabilities=["python", "javascript"]
    )
    
    # Configure faster polling for test
    worker.task_poll_interval = 2
    worker.heartbeat_interval = 5
    
    # Register with supernode
    if not worker.register_with_supernode("http://localhost:5000"):
        logger.error("Failed to register worker")
        return
    
    # Start worker
    worker.start()
    logger.info(f"Worker started with ID: {worker.node_id}")
    
    # Create 5 tasks
    logger.info("Creating 5 test tasks...")
    task_ids = []
    for i in range(5):
        response = requests.post(
            "http://localhost:5000/create_task",
            json={
                "code_url": f"https://github.com/example/test{i}.git",
                "analysis_type": "security_scan",
                "deadline": "2025-05-16T12:00:00Z"
            }
        )
        
        if response.status_code == 201:
            task_data = response.json()
            task_ids.append(task_data["task_id"])
            logger.info(f"Created task {i+1}: {task_data['task_id']}")
        else:
            logger.error(f"Failed to create task {i+1}")
    
    # Monitor task processing
    logger.info("Monitoring task processing...")
    done = False
    start_time = time.time()
    
    while not done and (time.time() - start_time) < 60:  # Max 60 seconds
        # Check status
        response = requests.get("http://localhost:5000/status")
        if response.status_code == 200:
            status = response.json()
            completed = status["tasks"]["completed"]
            pending = status["tasks"]["pending"]
            
            logger.info(f"Status: {completed} completed, {pending} pending")
            
            # Check worker current tasks
            worker_status = worker.get_status()
            logger.info(f"Worker load: {worker_status['load']:.2f}, Active tasks: {len(worker_status['current_tasks'])}")
            
            if completed >= 5:
                logger.info("All tasks completed!")
                done = True
                break
        
        time.sleep(3)
    
    # Final status
    response = requests.get("http://localhost:5000/status")
    final_status = response.json()
    logger.info(f"Final status: {final_status}")
    
    # Stop worker
    logger.info("Stopping worker...")
    worker.stop()
    
    logger.info("Test complete!")

if __name__ == "__main__":
    main()