# p2p_network/dynamodb_manager.py
import boto3
import time
import uuid
import logging
from boto3.dynamodb.conditions import Key, Attr

logger = logging.getLogger(__name__)

class DynamoDBManager:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table('TasksTable')
        
    def create_task(self, repository, commit_id, analysis_types=None):
        """Create a new task record"""
        task_id = f"task-{uuid.uuid4().hex[:8]}"
        timestamp = int(time.time())
        
        task = {
            'TaskId': task_id,
            'Status': 'PENDING',
            'Repository': repository,
            'CommitId': commit_id,
            'AnalysisTypes': analysis_types or ['style', 'security', 'quality'],
            'CreatedAt': timestamp,
            'AssignedNode': None,
            'CompletedAt': None,
            'Results': {}
        }
        
        try:
            self.table.put_item(Item=task)
            logger.info(f"Task created: {task_id}")
            return task
        except Exception as e:
            logger.error(f"Error creating task in DynamoDB: {e}")
            raise
    
    def update_task_status(self, task_id, status, node_id=None, results=None):
        """Update task status and results"""
        update_expression = "SET #status = :status"
        expression_values = {
            ':status': status
        }
        expression_names = {
            '#status': 'Status'
        }
        
        if node_id:
            update_expression += ", AssignedNode = :node"
            expression_values[':node'] = node_id
            
        if status == 'COMPLETED':
            update_expression += ", CompletedAt = :time"
            expression_values[':time'] = int(time.time())
            
        if results:
            update_expression += ", Results = :results"
            expression_values[':results'] = results
            
        try:
            response = self.table.update_item(
                Key={'TaskId': task_id},
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_names,
                ExpressionAttributeValues=expression_values,
                ReturnValues="UPDATED_NEW"
            )
            logger.info(f"Task updated: {task_id}, status: {status}")
            return response
        except Exception as e:
            logger.error(f"Error updating task in DynamoDB: {e}")
            raise
    
    def get_task(self, task_id):
        """Get a task by ID"""
        try:
            response = self.table.get_item(
                Key={'TaskId': task_id}
            )
            return response.get('Item')
        except Exception as e:
            logger.error(f"Error retrieving task from DynamoDB: {e}")
            return None
    
    def query_tasks_by_status(self, status, limit=50):
        """Get tasks by status using the StatusIndex GSI"""
        try:
            response = self.table.query(
                IndexName='StatusIndex',
                KeyConditionExpression=Key('Status').eq(status),
                Limit=limit
            )
            return response.get('Items', [])
        except Exception as e:
            logger.error(f"Error querying tasks by status: {e}")
            return []
            
    def list_tasks(self, limit=50):
        """List all tasks, with optional limit"""
        try:
            response = self.table.scan(Limit=limit)
            return response.get('Items', [])
        except Exception as e:
            logger.error(f"Error listing tasks: {e}")
            return []
