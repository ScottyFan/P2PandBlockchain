import unittest
import threading
import time
import requests
import logging

from p2p_network.supernode.api import app
from p2p_network.worker.worker_node import WorkerNode

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestP2PIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server_thread = threading.Thread(
            target=lambda: app.run(port=5555, debug=False),
            daemon=True
        )
        cls.server_thread.start()
        time.sleep(2)  
        
        cls.supernode_url = "http://localhost:5555"
    
    def test_multiple_workers(self):
        workers = []
        for i in range(3):
            worker = WorkerNode(
                node_id=f"worker-{i}",
                port=8080 + i,
                capabilities=["python"]
            )
            worker.task_poll_interval = 2  # Poll every 2 seconds 
            worker.heartbeat_interval = 5  # Heartbeat every 5 seconds 
            
            worker.register_with_supernode(self.supernode_url)
            worker.start()
            workers.append(worker)
            logger.info(f"Started worker {i}")
        
        time.sleep(3)
        
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
        max_wait_time = 30  
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
        
        # Clean u
        for worker in workers:
            worker.stop()
        
        # Now assert
        self.assertEqual(final_status["tasks"]["completed"], 5)
        self.assertEqual(final_status["tasks"]["pending"], 0)
    
    def test_single_worker_sequential(self):
        worker = WorkerNode(
            node_id="test-worker",
            port=8090,
            capabilities=["python"]
        )
        worker.task_poll_interval = 1  # Fast polling for test
        
        worker.register_with_supernode(self.supernode_url)
        worker.start()
        
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
        
        time.sleep(20)
        
        response = requests.get(f"{self.supernode_url}/status")
        status = response.json()
        
        worker.stop()
        
        self.assertGreaterEqual(status["tasks"]["completed"], 2)


if __name__ == '__main__':
    unittest.main()
