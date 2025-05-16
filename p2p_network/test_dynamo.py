# p2p_network/test_dynamo.py
import logging
import time
from dynamodb_manager import DynamoDBManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Test DynamoDB operations"""
    db = DynamoDBManager()
    
    # Create a sample task
    task = db.create_task(
        repository="https://github.com/example/repo",
        commit_id="a1b2c3d4",
        analysis_types=["security", "style", "quality"]
    )
    
    task_id = task['TaskId']
    logger.info(f"Created task with ID: {task_id}")
    
    # Retrieve the task
    retrieved_task = db.get_task(task_id)
    logger.info(f"Retrieved task: {retrieved_task}")
    
    # Update task status to PROCESSING
    db.update_task_status(task_id, "PROCESSING", node_id="node-001")
    logger.info("Updated task status to PROCESSING")
    
    # Simulate task processing
    time.sleep(2)
    
    # Complete the task with results
    results = {
        'security': {
            'vulnerabilities': 2,
            'issues': [
                {
                    'file': 'src/app.js',
                    'line': 42,
                    'description': 'Potential security issue',
                    'severity': 'medium'
                }
            ]
        }
    }
    
    db.update_task_status(task_id, "COMPLETED", results=results)
    logger.info("Updated task status to COMPLETED with results")
    
    # Get the updated task
    completed_task = db.get_task(task_id)
    logger.info(f"Completed task: {completed_task}")
    
    # Query tasks by status
    completed_tasks = db.query_tasks_by_status("COMPLETED")
    logger.info(f"Found {len(completed_tasks)} completed tasks")
    
if __name__ == "__main__":
    main()
