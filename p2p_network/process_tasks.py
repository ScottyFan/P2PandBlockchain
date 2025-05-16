# p2p_network/process_tasks.py
import json
import uuid
import time
import logging
from sqs_manager import SQSManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_task(task_data):
    """Process a single analysis task"""
    task_id = task_data.get('taskId')
    logger.info(f"Processing task: {task_id}")
    
    # Simulate processing time
    time.sleep(2)
    
    # Create sample results
    results = {
        'taskId': task_id,
        'nodeId': 'node-001',
        'status': 'completed',
        'results': {
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
        },
        'timestamp': time.time()
    }
    
    return results

def main():
    """Main task processing loop"""
    sqs_manager = SQSManager()
    
    while True:
        # Get tasks from queue
        messages = sqs_manager.receive_tasks()
        
        if not messages:
            logger.info("No tasks available, waiting...")
            time.sleep(10)
            continue
        
        for message in messages:
            try:
                # Parse task data
                task_data = json.loads(message['Body'])
                receipt_handle = message['ReceiptHandle']
                
                # Process the task
                results = process_task(task_data)
                
                # Send results
                sqs_manager.send_result(results)
                
                # Delete processed message
                sqs_manager.delete_message(sqs_manager.task_queue_url, receipt_handle)
                
            except Exception as e:
                logger.error(f"Error processing task: {e}")
                # The task will return to the queue after visibility timeout

if __name__ == "__main__":
    main()
