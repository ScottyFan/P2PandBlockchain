import unittest
import threading
import time
import requests
import logging

from p2p_network.supernode.api import app
from p2p_network.worker.worker_node import WorkerNode

# Set up logging to see what's happening
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestP2PIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Start supernode server"""
        cls.server_thread = threading.Thread(
            target=lambda: app.run(port=5555, debug=False),
            daemon=True
        )
        cls.server_thread.start()
        time.sleep(2)  # Wait for server to start
        
        cls.supernode_url = "http://localhost:5555"
    
    def test_multiple_workers(self):
        """Test multiple workers handling tasks"""
        # Create 3 worker nodes with faster polling
        workers = []
        for i in range(3):
            worker = WorkerNode(
                node_id=f"worker-{i}",
                port=8080 + i,
                capabilities=["python"]
            )
            # Make polling faster for tests
            worker.task_poll_interval = 2  # Poll every 2 seconds instead of 10
            worker.heartbeat_interval = 5  # Heartbeat every 5 seconds instead of 30
            
            worker.register_with_supernode(self.supernode_url)
            worker.start()
            workers.append(worker)
            logger.info(f"Started worker {i}")
        
        # Give workers time to start up
        time.sleep(3)
        
        # Create 5 tasks
        task_ids = []
        for i in range(5):
            response = requests.post(
                f"{self.supernode_url}/create_task",
                json={
                    "code_url": f"https://github.com/example/repo{i}.git",
                    "analysis_type": "pylint",
                    "deadline": "2025-12-31T23:59:59Z"
                }
            )
            task_data = response.json()
            task_ids.append(task_data["task_id"])
            logger.info(f"Created task {i}: {task_data['task_id']}")
        
        # Wait for tasks to be processed with periodic status checks
        max_wait_time = 30  # Maximum 30 seconds
        start_time = time.time()
        completed = 0
        
        while completed < 5 and (time.time() - start_time) < max_wait_time:
            response = requests.get(f"{self.supernode_url}/status")
            status = response.json()
            completed = status["tasks"]["completed"]
            pending = status["tasks"]["pending"]
            
            logger.info(f"Status: {completed} completed, {pending} pending")
            
            if completed < 5:
                time.sleep(2)
        
        # Final check
        response = requests.get(f"{self.supernode_url}/status")
        final_status = response.json()
        
        # Debug output
        logger.info(f"Final status: {final_status}")
        
        # Clean up - stop all workers
        for worker in workers:
            worker.stop()
        
        # Now assert
        self.assertEqual(final_status["tasks"]["completed"], 5)
        self.assertEqual(final_status["tasks"]["pending"], 0)
    
    def test_single_worker_sequential(self):
        """Test single worker handling multiple tasks sequentially"""
        worker = WorkerNode(
            node_id="test-worker",
            port=8090,
            capabilities=["python"]
        )
        worker.task_poll_interval = 1  # Fast polling for test
        
        worker.register_with_supernode(self.supernode_url)
        worker.start()
        
        # Create 3 tasks
        task_ids = []
        for i in range(3):
            response = requests.post(
                f"{self.supernode_url}/create_task",
                json={
                    "code_url": f"https://github.com/example/seq{i}.git",
                    "analysis_type": "pylint",
                    "deadline": "2025-12-31T23:59:59Z"
                }
            )
            task_ids.append(response.json()["task_id"])
        
        # Wait for completion
        time.sleep(20)
        
        # Check status
        response = requests.get(f"{self.supernode_url}/status")
        status = response.json()
        
        worker.stop()
        
        self.assertGreaterEqual(status["tasks"]["completed"], 2)


if __name__ == '__main__':
    unittest.main()