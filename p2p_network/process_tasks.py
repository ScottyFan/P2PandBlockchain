# p2p_network/process_tasks.py
import json
import uuid
import time
import logging
from sqs_manager import SQSManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_task(task_data):
    task_id = task_data.get('taskId')
    logger.info(f"Processing task: {task_id}")
    
    time.sleep(2)
    
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
    sqs_manager = SQSManager()
    
    while True:
        messages = sqs_manager.receive_tasks()
        
        if not messages:
            logger.info("No tasks available, waiting...")
            time.sleep(10)
            continue
        
        for message in messages:
            try:
                task_data = json.loads(message['Body'])
                receipt_handle = message['ReceiptHandle']
                
                results = process_task(task_data)
                
                sqs_manager.send_result(results)
                
                sqs_manager.delete_message(sqs_manager.task_queue_url, receipt_handle)
                
            except Exception as e:
                logger.error(f"Error processing task: {e}")

if __name__ == "__main__":
    main()
