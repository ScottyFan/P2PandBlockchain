"""
Supernode implementation for P2P network
"""
import logging
from queue import Queue, PriorityQueue
from threading import Lock
from typing import Dict, List, Optional
import time
import uuid

from ..common.message_formats import (
    NodeRegistration, TaskAssignment, 
    ResultSubmission, Heartbeat
)
from .models import NodeInfo, Task


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SuperNode:
    def __init__(self):
        self.registered_nodes: Dict[str, NodeInfo] = {}
        self.task_queue: PriorityQueue = PriorityQueue()
        self.pending_tasks: Dict[str, Task] = {}
        self.completed_tasks: Dict[str, Task] = {}
        self.node_lock = Lock()
        self.task_lock = Lock()
        
    def register_node(self, registration: NodeRegistration) -> str:
        with self.node_lock:
            node_info = NodeInfo(
                node_id=registration.node_id,
                ip_address=registration.ip_address,
                port=registration.port,
                capabilities=registration.capabilities
            )
            self.registered_nodes[registration.node_id] = node_info
            logger.info(f"Registered node: {registration.node_id}")
            return registration.node_id
    
    def handle_heartbeat(self, heartbeat: Heartbeat) -> bool:
        with self.node_lock:
            if heartbeat.node_id in self.registered_nodes:
                node = self.registered_nodes[heartbeat.node_id]
                node.update_heartbeat(
                    timestamp=time.time(),
                    load=heartbeat.current_load
                )
                logger.debug(f"Heartbeat from {heartbeat.node_id}")
                return True
            else:
                logger.warning(f"Heartbeat from unknown node: {heartbeat.node_id}")
                return False
    
    def create_task(self, code_url: str, analysis_type: str, 
                   deadline: str) -> Task:
        """Create a new analysis task"""
        task_id = str(uuid.uuid4())
        task = Task(
            task_id=task_id,
            code_url=code_url,
            analysis_type=analysis_type,
            deadline=deadline
        )
        
        with self.task_lock:
            self.pending_tasks[task_id] = task
            # Add to priority queue (using deadline as priority)
            self.task_queue.put((deadline, task_id))
            
        logger.info(f"Created task: {task_id}")
        return task
    
    def get_available_tasks(self, node_id: str, max_tasks: int = 3) -> List[TaskAssignment]:
        """Get available tasks for a specific node"""
        with self.node_lock:
            if node_id not in self.registered_nodes:
                logger.warning(f"Unknown node requesting tasks: {node_id}")
                return []
            
            node = self.registered_nodes[node_id]
            if not node.is_healthy():
                logger.warning(f"Unhealthy node requesting tasks: {node_id}")
                return []
        
        available_tasks = []
        with self.task_lock:
            # Check for unassigned tasks that match node capabilities
            temp_queue = []
            
            # Only take tasks if node isn't already busy
            if node.current_load >= 1.0:
                logger.debug(f"Node {node_id} is busy (load: {node.current_load})")
                return []
            
            # Updated: use max_tasks parameter instead of hardcoded 3
            while not self.task_queue.empty() and len(available_tasks) < max_tasks:
                deadline, task_id = self.task_queue.get()
                task = self.pending_tasks.get(task_id)
                
                if task and task.status == "pending":
                    # Check if node can handle this task
                    if self._can_node_handle_task(node, task):
                        task.assign_to_node(node_id)
                        task_assignment = TaskAssignment(
                            task_id=task.task_id,
                            code_url=task.code_url,
                            analysis_type=task.analysis_type,
                            deadline=task.deadline,
                            assigned_node=node_id
                        )
                        available_tasks.append(task_assignment)
                        logger.info(f"Assigned task {task.task_id} to node {node_id}")
                    else:
                        temp_queue.append((deadline, task_id))
                        
            # Put back tasks that couldn't be assigned
            for item in temp_queue:
                self.task_queue.put(item)
                
        return available_tasks

    def submit_results(self, submission: ResultSubmission) -> bool:
        """Process results from a worker node"""
        with self.task_lock:
            if submission.task_id not in self.pending_tasks:
                logger.warning(f"Results for unknown task: {submission.task_id}")
                return False
                
            task = self.pending_tasks[submission.task_id]
            if task.assigned_node != submission.node_id:
                logger.warning(f"Results from wrong node for task: {submission.task_id}")
                return False
                
            # Move task to completed
            task.mark_completed(submission.results)
            self.completed_tasks[submission.task_id] = task
            del self.pending_tasks[submission.task_id]
            
            # Update node statistics
            with self.node_lock:
                if submission.node_id in self.registered_nodes:
                    node = self.registered_nodes[submission.node_id]
                    node.completed_tasks += 1
                    
        logger.info(f"Completed task: {submission.task_id}")
        return True
    
    def _can_node_handle_task(self, node: NodeInfo, task: Task) -> bool:
        """Check if a node can handle a specific task"""
        # For now, check if node supports the required analysis type
        # This can be extended to check capabilities, load, etc.
        return True  # Simplified for Week 1
    
    def get_node_status(self) -> Dict:
        """Get status of all registered nodes"""
        with self.node_lock:
            status = {}
            for node_id, node in self.registered_nodes.items():
                status[node_id] = {
                    'status': node.status,
                    'last_heartbeat': node.last_heartbeat,
                    'current_load': node.current_load,
                    'completed_tasks': node.completed_tasks,
                    'capabilities': node.capabilities,
                    'healthy': node.is_healthy()
                }
            return status
    
    def get_task_status(self) -> Dict:
        """Get status of all tasks"""
        with self.task_lock:
            return {
                'pending': len(self.pending_tasks),
                'completed': len(self.completed_tasks),
                'queue_size': self.task_queue.qsize()
            }
        
    def _select_best_node_for_task(self, task: Task) -> Optional[str]:
        available_nodes = []
        
        with self.node_lock:
            for node_id, node_info in self.registered_nodes.items():
                if node_info.is_healthy() and node_info.current_load < 0.8:
                    # Calculate fitness score
                    score = self._calculate_node_fitness(node_info, task)
                    available_nodes.append((node_id, score))
        
        if not available_nodes:
            return None
        
        # Sort by fitness score and select the best
        available_nodes.sort(key=lambda x: x[1], reverse=True)
        return available_nodes[0][0]

    def _calculate_node_fitness(self, node: NodeInfo, task: Task) -> float:
        score = 100.0
        
        # Factor 1: Current load (lower is better)
        score -= node.current_load * 50
        
        # Factor 2: Recent performance
        if node.completed_tasks > 0:
            score += min(node.completed_tasks, 10) * 2
        
        # Factor 3: Task type compatibility
        # (Add logic based on task.analysis_type and node.capabilities)
        
        return score