import unittest
import threading
import time
import sys
import os
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from p2p_network.worker.worker_node import WorkerNode
from p2p_network.worker.task_executor import TaskExecutor
from p2p_network.common.message_formats import TaskAssignment


class TestWorkerNode(unittest.TestCase):
    def setUp(self):
        self.worker = WorkerNode(
            node_id="test-worker-1",
            ip_address="localhost",
            port=8081,
            capabilities=["python"]
        )
        self.mock_supernode_url = "http://localhost:5000"
    
    def test_initialization(self):
        self.assertEqual(self.worker.node_id, "test-worker-1")
        self.assertEqual(self.worker.ip_address, "localhost")
        self.assertEqual(self.worker.port, 8081)
        self.assertEqual(self.worker.capabilities, ["python"])
        self.assertFalse(self.worker.is_running)
    
    @patch('p2p_network.worker.worker_node.NetworkClient')
    def test_registration(self, mock_network_client):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "node_id": "test-worker-1"
        }
        
        mock_network_client.return_value.post.return_value = mock_response
        
        # Test registration
        result = self.worker.register_with_supernode(self.mock_supernode_url)
        self.assertTrue(result)
        self.assertEqual(self.worker.supernode_url, self.mock_supernode_url)
    
    def test_load_calculation(self):
        self.assertEqual(self.worker._calculate_load(), 0.0)
        
        # With current task
        self.worker.current_task = Mock()
        self.assertEqual(self.worker._calculate_load(), 1.0)
    
    def test_status(self):
        status = self.worker.get_status()
        
        self.assertEqual(status["node_id"], "test-worker-1")
        self.assertEqual(status["ip_address"], "localhost")
        self.assertEqual(status["port"], 8081)
        self.assertEqual(status["capabilities"], ["python"])
        self.assertFalse(status["is_running"])
        self.assertIsNone(status["current_task"])
        self.assertEqual(status["load"], 0.0)


class TestTaskExecutor(unittest.TestCase):
    def setUp(self):
        self.executor = TaskExecutor()
    
    def test_detect_language(self):
        with patch('os.walk') as mock_walk:
            mock_walk.return_value = [
                ('/test/path', ['src'], ['main.py', 'test.py']),
                ('/test/path/src', [], ['module.py', '__init__.py'])
            ]
            
            language = self.executor._detect_language('/test/path')
            self.assertEqual(language, 'python')
    
    def test_analysis_result_structure(self):
        with patch.object(self.executor, '_download_code') as mock_download, \
             patch.object(self.executor, '_detect_language') as mock_detect, \
             patch.object(self.executor, '_run_analysis') as mock_analysis:
            
            mock_download.return_value = '/tmp/test_repo'
            mock_detect.return_value = 'python'
            mock_analysis.return_value = {'test': 'results'}
            
            result = self.executor.execute_analysis(
                task_id='test-123',
                code_url='https://github.com/test/repo.git',
                analysis_type='pylint'
            )
            
            self.assertEqual(result['task_id'], 'test-123')
            self.assertEqual(result['status'], 'completed')
            self.assertEqual(result['language'], 'python')
            self.assertEqual(result['analysis_type'], 'pylint')
            self.assertIn('results', result)


if __name__ == '__main__':
    unittest.main()
