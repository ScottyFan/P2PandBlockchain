"""
REST API for supernode
"""
from flask import Flask, request, jsonify
from datetime import datetime
import logging

from ..common.message_formats import (
    NodeRegistration, TaskAssignment, 
    ResultSubmission, Heartbeat
)
from .supernode import SuperNode


app = Flask(__name__)
supernode = SuperNode()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.route('/register', methods=['POST'])
def register_node():
    """Register a new worker node"""
    try:
        data = request.json
        registration = NodeRegistration.from_dict(data)
        node_id = supernode.register_node(registration)
        
        return jsonify({
            'status': 'success',
            'node_id': node_id,
            'message': 'Node registered successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400


@app.route('/tasks', methods=['GET'])
def get_tasks():
    """Get available tasks for a node"""
    try:
        node_id = request.args.get('node_id')
        max_tasks = int(request.args.get('max_tasks', 3))  # Default to 3 if not provided
        
        if not node_id:
            return jsonify({
                'status': 'error',
                'message': 'node_id parameter required'
            }), 400
            
        tasks = supernode.get_available_tasks(node_id, max_tasks)
        task_dicts = [task.to_dict() for task in tasks]
        
        return jsonify({
            'status': 'success',
            'tasks': task_dicts
        }), 200
        
    except Exception as e:
        logger.error(f"Get tasks error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    
    
@app.route('/heartbeat', methods=['POST'])
def heartbeat():
    """Receive heartbeat from worker node"""
    try:
        data = request.json
        heartbeat_msg = Heartbeat.from_dict(data)
        success = supernode.handle_heartbeat(heartbeat_msg)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Heartbeat received'
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Unknown node'
            }), 404
            
    except Exception as e:
        logger.error(f"Heartbeat error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400


@app.route('/results', methods=['POST'])
def submit_results():
    """Submit analysis results"""
    try:
        data = request.json
        submission = ResultSubmission.from_dict(data)
        success = supernode.submit_results(submission)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Results submitted successfully'
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to submit results'
            }), 400
            
    except Exception as e:
        logger.error(f"Submit results error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400


@app.route('/status', methods=['GET'])
def get_status():
    """Get supernode status"""
    try:
        node_status = supernode.get_node_status()
        task_status = supernode.get_task_status()
        
        return jsonify({
            'status': 'success',
            'nodes': node_status,
            'tasks': task_status,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Status error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/create_task', methods=['POST'])
def create_task():
    """Create a new analysis task"""
    try:
        data = request.json
        required_fields = ['code_url', 'analysis_type', 'deadline']
        
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'status': 'error',
                    'message': f'Missing required field: {field}'
                }), 400
        
        task = supernode.create_task(
            code_url=data['code_url'],
            analysis_type=data['analysis_type'],
            deadline=data['deadline']
        )
        
        return jsonify({
            'status': 'success',
            'task_id': task.task_id,
            'message': 'Task created successfully'
        }), 201
        
    except Exception as e:
        logger.error(f"Create task error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)