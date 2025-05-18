"""
Network utility functions for P2P communication
"""
import requests
import time
import logging
from typing import Dict, Any, Optional
from requests.exceptions import RequestException, Timeout, ConnectionError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NetworkClient:
    def __init__(self, timeout: int = 10, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
    
    def post(self, url: str, json_data: Dict[str, Any], 
             headers: Optional[Dict[str, str]] = None) -> Optional[requests.Response]:
        headers = headers or {'Content-Type': 'application/json'}
        
        for attempt in range(self.max_retries):
            try:
                response = self.session.post(
                    url,
                    json=json_data,
                    headers=headers,
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response
                
            except Timeout:
                logger.warning(f"Timeout on attempt {attempt + 1} for {url}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  
                    
            except ConnectionError:
                logger.error(f"Connection error for {url}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                    
            except RequestException as e:
                logger.error(f"Request error: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                    
        return None
    
    def get(self, url: str, params: Optional[Dict[str, str]] = None,
            headers: Optional[Dict[str, str]] = None) -> Optional[requests.Response]:
        headers = headers or {}
        
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response
                
            except Timeout:
                logger.warning(f"Timeout on attempt {attempt + 1} for {url}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                    
            except ConnectionError:
                logger.error(f"Connection error for {url}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                    
            except RequestException as e:
                logger.error(f"Request error: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                    
        return None


def validate_ip_address(ip: str) -> bool:
    parts = ip.split('.')
    if len(parts) != 4:
        return False
    
    for part in parts:
        try:
            num = int(part)
            if num < 0 or num > 255:
                return False
        except ValueError:
            return False
            
    return True


def generate_node_id(ip: str, port: int) -> str:
    """Generate a unique node ID based on IP and port"""
    import hashlib
    node_string = f"{ip}:{port}"
    return hashlib.sha256(node_string.encode()).hexdigest()[:16]
