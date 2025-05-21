from flask import Flask, request, jsonify
from datetime import datetime
import logging

from ..common.message_formats import (
    NodeRegistration, TaskAssignment, 
    ResultSubmission, Heartbeat
)
from .supernode import SuperNode
from ..blockchain.api import blockchain_api


app = Flask(__name__)
supernode = SuperNode()

app.register_blueprint(blockchain_api, url_prefix='/blockchain')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.route('/register', methods=['POST'])
def register_node():
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
    try:
        node_id = request.args.get('node_id')
        max_tasks = int(request.args.get('max_tasks', 3)) 
        
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
    try:
        data = request.json
        submission = ResultSubmission.from_dict(data)
        success = supernode.submit_results(submission)
        
        if success:
            blockchain_record = {
                "review_id": submission.task_id,
                "commit_id": submission.results.get("commit_id", "unknown"),
                "reviewer": submission.node_id,
                "status": "COMPLETED",
                "timestamp": datetime.now().timestamp(),
                "results": submission.results
            }
            
            try:
                from ..blockchain.blockchain import blockchain
                blockchain.add_block(blockchain_record)
                logger.info(f"Added result to blockchain for task {submission.task_id}")
            except Exception as blockchain_error:
                logger.error(f"Error adding to blockchain: {blockchain_error}")
        
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
    try:
        node_status = supernode.get_node_status()
        task_status = supernode.get_task_status()
        
        blockchain_status = {
            "enabled": True,
            "blocks": 0
        }
        
        try:
            from ..blockchain.blockchain import blockchain
            blockchain_status["blocks"] = len(blockchain.chain)
            blockchain_status["is_valid"] = blockchain.is_chain_valid()
        except Exception as blockchain_error:
            logger.error(f"Error getting blockchain status: {blockchain_error}")
            blockchain_status["enabled"] = False
        
        return jsonify({
            'status': 'success',
            'nodes': node_status,
            'tasks': task_status,
            'blockchain': blockchain_status,
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
        
        try:
            from ..blockchain.blockchain import blockchain
            blockchain_record = {
                "review_id": task.task_id,
                "commit_id": data.get("commit_id", "unknown"),
                "reviewer": "supernode",
                "status": "CREATED",
                "timestamp": datetime.now().timestamp(),
                "task_details": {
                    "code_url": data['code_url'],
                    "analysis_type": data['analysis_type'],
                    "deadline": data['deadline']
                }
            }
            blockchain.add_block(blockchain_record)
            logger.info(f"Added task creation to blockchain for {task.task_id}")
        except Exception as blockchain_error:
            logger.error(f"Error adding to blockchain: {blockchain_error}")
        
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
