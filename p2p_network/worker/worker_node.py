"""
Worker node implementation for P2P network with concurrent task processing
"""
import threading
import time
import logging
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid
from concurrent.futures import ThreadPoolExecutor

from ..common.message_formats import (
    NodeRegistration, TaskAssignment, 
    ResultSubmission, Heartbeat
)
from ..common.network_utils import NetworkClient


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WorkerNode:
    def __init__(self, node_id: Optional[str] = None, 
                 ip_address: str = "localhost", 
                 port: int = 8080,
                 capabilities: Optional[List[str]] = None,
                 max_concurrent_tasks: int = 3):
        """Initialize a worker node"""
        self.node_id = node_id or str(uuid.uuid4())
        self.ip_address = ip_address
        self.port = port
        self.capabilities = capabilities or ["python", "javascript"]
        self.supernode_url = None
        self.is_running = False
        self.current_tasks = {}  # Dictionary of task_id -> task
        self.max_concurrent_tasks = max_concurrent_tasks
        self.heartbeat_interval = 30  # seconds
        self.task_poll_interval = 10  # seconds
        self.network_client = NetworkClient()
        self.heartbeat_thread = None
        self.task_poll_thread = None
        self.task_lock = threading.Lock()
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent_tasks)
        
    def register_with_supernode(self, supernode_url: str) -> bool:
        """Register this node with the supernode"""
        self.supernode_url = supernode_url
        
        registration = NodeRegistration(
            node_id=self.node_id,
            ip_address=self.ip_address,
            port=self.port,
            capabilities=self.capabilities,
            timestamp=datetime.now().isoformat()
        )
        
        try:
            response = self.network_client.post(
                f"{supernode_url}/register",
                registration.to_dict()
            )
            
            if response and response.status_code == 200:
                data = response.json()
                logger.info(f"Successfully registered with supernode: {data}")
                return True
            else:
                logger.error(f"Failed to register with supernode")
                return False
                
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return False
    
    def start(self):
        """Start the worker node operations"""
        if not self.supernode_url:
            logger.error("Cannot start: not registered with supernode")
            return
            
        self.is_running = True
        
        # Start heartbeat thread
        self.heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            daemon=True
        )
        self.heartbeat_thread.start()
        
        # Start task polling thread
        self.task_poll_thread = threading.Thread(
            target=self._task_poll_loop,
            daemon=True
        )
        self.task_poll_thread.start()
        
        logger.info(f"Worker node {self.node_id} started")
    
    def stop(self):
        """Stop the worker node operations"""
        self.is_running = False
        
        # Wait for threads to finish
        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=2)
        if self.task_poll_thread:
            self.task_poll_thread.join(timeout=2)
            
        # Shut down executor
        self.executor.shutdown(wait=False)
            
        logger.info(f"Worker node {self.node_id} stopped")
    
    def _heartbeat_loop(self):
        """Send periodic heartbeats to the supernode"""
        while self.is_running:
            try:
                heartbeat = Heartbeat(
                    node_id=self.node_id,
                    timestamp=datetime.now().isoformat(),
                    status="active",
                    current_load=self._calculate_load()
                )
                
                response = self.network_client.post(
                    f"{self.supernode_url}/heartbeat",
                    heartbeat.to_dict()
                )
                
                if response and response.status_code == 200:
                    logger.debug(f"Heartbeat sent successfully")
                else:
                    logger.warning(f"Heartbeat failed")
                    
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
            
            time.sleep(self.heartbeat_interval)
    
    def _task_poll_loop(self):
        """Poll for available tasks from the supernode"""
        while self.is_running:
            try:
                # Check if we can take more tasks
                with self.task_lock:
                    can_take_more = len(self.current_tasks) < self.max_concurrent_tasks
                
                if can_take_more:
                    self._poll_for_tasks()
                else:
                    logger.debug(f"Worker {self.node_id} at max tasks ({len(self.current_tasks)})")
                    
            except Exception as e:
                logger.error(f"Task polling error: {e}")
            
            time.sleep(self.task_poll_interval)
    
    def _poll_for_tasks(self):
        """Check for available tasks"""
        try:
            response = self.network_client.get(
                f"{self.supernode_url}/tasks",
                params={
                    "node_id": self.node_id,
                    "max_tasks": self.max_concurrent_tasks - len(self.current_tasks)
                }
            )
            
            if response and response.status_code == 200:
                data = response.json()
                tasks = data.get("tasks", [])
                
                if tasks:
                    for task_data in tasks:
                        task = TaskAssignment.from_dict(task_data)
                        
                        # Store task and submit to executor
                        with self.task_lock:
                            self.current_tasks[task.task_id] = task
                        
                        logger.info(f"Worker {self.node_id} received task: {task.task_id}")
                        self.executor.submit(self._execute_task, task)
                else:
                    logger.debug(f"No tasks available for worker {self.node_id}")
                    
        except Exception as e:
            logger.error(f"Error polling for tasks: {e}")
    
    def _execute_task(self, task: TaskAssignment):
        """Execute an analysis task"""
        logger.info(f"Worker {self.node_id} executing task {task.task_id}")
        
        try:
            # Simulate task execution (will be replaced with real analysis)
            time.sleep(5)  # Simulate work
            
            # Create mock results
            results = {
                "task_id": task.task_id,
                "analysis_type": task.analysis_type,
                "code_url": task.code_url,
                "findings": {
                    "issues_found": 3,
                    "severity": "medium",
                    "details": [
                        {
                            "type": "security",
                            "line": 42,
                            "description": "Potential SQL injection"
                        },
                        {
                            "type": "style",
                            "line": 15,
                            "description": "Line too long"
                        },
                        {
                            "type": "performance",
                            "line": 78,
                            "description": "Inefficient loop"
                        }
                    ]
                },
                "execution_time": 5.0,
                "timestamp": datetime.now().isoformat()
            }
            
            # Submit results
            submission = ResultSubmission(
                task_id=task.task_id,
                results=results,
                node_id=self.node_id,
                timestamp=datetime.now().isoformat()
            )
            
            response = self.network_client.post(
                f"{self.supernode_url}/results",
                submission.to_dict()
            )
            
            if response and response.status_code == 200:
                logger.info(f"Worker {self.node_id} submitted results for task {task.task_id}")
            else:
                logger.error(f"Worker {self.node_id} failed to submit results for task {task.task_id}")
                
        except Exception as e:
            logger.error(f"Worker {self.node_id} error executing task {task.task_id}: {e}")
        finally:
            # Remove task from current tasks
            with self.task_lock:
                if task.task_id in self.current_tasks:
                    del self.current_tasks[task.task_id]
            
            logger.info(f"Worker {self.node_id} completed task {task.task_id}")
    
    def _calculate_load(self) -> float:
        """Calculate current node load"""
        with self.task_lock:
            task_count = len(self.current_tasks)
        
        # Load is ratio of current tasks to max tasks
        return min(1.0, task_count / self.max_concurrent_tasks)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current node status"""
        with self.task_lock:
            current_task_ids = list(self.current_tasks.keys())
            
        return {
            "node_id": self.node_id,
            "ip_address": self.ip_address,
            "port": self.port,
            "capabilities": self.capabilities,
            "is_running": self.is_running,
            "current_tasks": current_task_ids,
            "load": self._calculate_load()
        }