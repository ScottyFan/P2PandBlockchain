"""
Tests for supernode implementation
"""
import unittest
import json
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from p2p_network.common.message_formats import (
    NodeRegistration, Heartbeat, ResultSubmission
)
from p2p_network.supernode.supernode import SuperNode


class TestSuperNode(unittest.TestCase):
    def setUp(self):
        self.supernode = SuperNode()
        
    def test_node_registration(self):
        registration = NodeRegistration(
            node_id="test-node-1",
            ip_address="192.168.1.100",
            port=8080,
            capabilities=["python", "javascript"],
            timestamp=datetime.now().isoformat()
        )
        
        node_id = self.supernode.register_node(registration)
        self.assertEqual(node_id, "test-node-1")
        self.assertIn("test-node-1", self.supernode.registered_nodes)
        
    def test_heartbeat_handling(self):
        registration = NodeRegistration(
            node_id="test-node-2",
            ip_address="192.168.1.101",
            port=8081,
            capabilities=["python"],
            timestamp=datetime.now().isoformat()
        )
        self.supernode.register_node(registration)
        
        # Send heartbeat
        heartbeat = Heartbeat(
            node_id="test-node-2",
            timestamp=datetime.now().isoformat(),
            status="active",
            current_load=0.5
        )
        
        success = self.supernode.handle_heartbeat(heartbeat)
        self.assertTrue(success)
        
        # Check node status
        node = self.supernode.registered_nodes["test-node-2"]
        self.assertEqual(node.current_load, 0.5)
        self.assertTrue(node.is_healthy())
        
    def test_task_creation(self):
        task = self.supernode.create_task(
            code_url="https://example.com/code.git",
            analysis_type="security_scan",
            deadline=(datetime.now() + timedelta(hours=1)).isoformat()
        )
        
        self.assertIsNotNone(task.task_id)
        self.assertEqual(task.status, "pending")
        self.assertIn(task.task_id, self.supernode.pending_tasks)
        
    def test_task_assignment(self):
        registration = NodeRegistration(
            node_id="test-node-3",
            ip_address="192.168.1.102",
            port=8082,
            capabilities=["python"],
            timestamp=datetime.now().isoformat()
        )
        self.supernode.register_node(registration)
        
        # Create a task
        task = self.supernode.create_task(
            code_url="https://example.com/code.git",
            analysis_type="lint",
            deadline=(datetime.now() + timedelta(hours=1)).isoformat()
        )
        
        tasks = self.supernode.get_available_tasks("test-node-3")
        
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].task_id, task.task_id)
        self.assertEqual(tasks[0].assigned_node, "test-node-3")
        
        assigned_task = self.supernode.pending_tasks[task.task_id]
        self.assertEqual(assigned_task.status, "assigned")
        self.assertEqual(assigned_task.assigned_node, "test-node-3")


if __name__ == '__main__':
    unittest.main()
