"""
Message format definitions for P2P network communication
"""
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Dict, Any
import json


@dataclass
class NodeRegistration:
    node_id: str
    ip_address: str
    port: int
    capabilities: List[str]
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NodeRegistration':
        return cls(**data)


@dataclass
class TaskAssignment:
    task_id: str
    code_url: str
    analysis_type: str
    deadline: str
    assigned_node: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskAssignment':
        return cls(**data)


@dataclass
class ResultSubmission:
    task_id: str
    results: Dict[str, Any]
    node_id: str
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ResultSubmission':
        return cls(**data)


@dataclass
class Heartbeat:
    node_id: str
    timestamp: str
    status: str = "active"
    current_load: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Heartbeat':
        return cls(**data)