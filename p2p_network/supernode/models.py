#### 3. `p2p_network/supernode/models.py`
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
import time


@dataclass
class NodeInfo:
    node_id: str
    ip_address: str
    port: int
    capabilities: List[str]
    last_heartbeat: float = field(default_factory=time.time)
    status: str = "active"
    current_load: float = 0.0
    completed_tasks: int = 0
    
    def is_healthy(self) -> bool:
        current_time = time.time()
        return (current_time - self.last_heartbeat) < 90
    
    def update_heartbeat(self, timestamp: float, load: float = 0.0):
        self.last_heartbeat = timestamp
        self.current_load = load
        self.status = "active" if self.is_healthy() else "inactive"


@dataclass
class Task:
    task_id: str
    code_url: str
    analysis_type: str
    deadline: str
    status: str = "pending"
    assigned_node: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    results: Optional[Dict] = None
    
    def assign_to_node(self, node_id: str):
        """Assign task to a specific node"""
        self.assigned_node = node_id
        self.status = "assigned"
    
    def mark_completed(self, results: Dict):
        """Mark task as completed with results"""
        self.status = "completed"
        self.completed_at = time.time()
        self.results = results
