# p2p_network/sqs_manager.py
import boto3
import json
import logging

logger = logging.getLogger(__name__)

class SQSManager:
    def __init__(self):
        self.sqs = boto3.client('sqs')
        self.task_queue_url = "https://sqs.us-east-1.amazonaws.com/559050241209/analysis-tasks"
        self.result_queue_url = "https://sqs.us-east-1.amazonaws.com/559050241209/analysis-results"
        
    def send_task(self, task):
        try:
            response = self.sqs.send_message(
                QueueUrl=self.task_queue_url,
                MessageBody=json.dumps(task)
            )
            logger.info(f"Task sent to queue: {task.get('taskId')}")
            return response
        except Exception as e:
            logger.error(f"Error sending task to SQS: {e}")
            raise
    
    def receive_tasks(self, max_messages=10):
        try:
            response = self.sqs.receive_message(
                QueueUrl=self.task_queue_url,
                MaxNumberOfMessages=max_messages,
                WaitTimeSeconds=10,
                VisibilityTimeout=300  
            )
            return response.get('Messages', [])
        except Exception as e:
            logger.error(f"Error receiving tasks from SQS: {e}")
            return []
    
    def send_result(self, result):
        try:
            response = self.sqs.send_message(
                QueueUrl=self.result_queue_url,
                MessageBody=json.dumps(result)
            )
            logger.info(f"Results sent for task: {result.get('taskId')}")
            return response
        except Exception as e:
            logger.error(f"Error sending results to SQS: {e}")
            raise
    
    def delete_message(self, queue_url, receipt_handle):
        try:
            self.sqs.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=receipt_handle
            )
            logger.info("Message deleted from queue")
        except Exception as e:
            logger.error(f"Error deleting message from SQS: {e}")
            raise
