import hashlib
import time
import json
from typing import List, Dict, Any


class Block:
    def __init__(self, index: int, timestamp: float, data: Dict[str, Any], previous_hash: str):
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.hash = self.calculate_hash()
        
    def calculate_hash(self) -> str:
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash
        }, sort_keys=True).encode()
        
        return hashlib.sha256(block_string).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash,
            "hash": self.hash
        }


class Blockchain:
    def __init__(self):
        self.chain: List[Block] = []
        self.create_genesis_block()
        
    def create_genesis_block(self):
        genesis_block = Block(0, time.time(), {"message": "Genesis Block"}, "0")
        self.chain.append(genesis_block)
        
    def get_latest_block(self) -> Block:
        return self.chain[-1]
    
    def add_block(self, data: Dict[str, Any]) -> Block:
        previous_block = self.get_latest_block()
        new_index = previous_block.index + 1
        new_timestamp = time.time()
        new_hash = previous_block.hash
        
        new_block = Block(new_index, new_timestamp, data, new_hash)
        self.chain.append(new_block)
        return new_block
    
    def is_chain_valid(self) -> bool:
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]
            
            # Check if the hash is still valid
            if current_block.hash != current_block.calculate_hash():
                return False
                
            # Check if this block points to the correct previous hash
            if current_block.previous_hash != previous_block.hash:
                return False
                
        return True
    
    def get_block_by_index(self, index: int) -> Dict[str, Any]:
        if 0 <= index < len(self.chain):
            return self.chain[index].to_dict()
        return None
    
    def get_blocks_by_review_id(self, review_id: str) -> List[Dict[str, Any]]:
        matching_blocks = []
        
        for block in self.chain:
            if block.index > 0:
                if block.data.get("review_id") == review_id:
                    matching_blocks.append(block.to_dict())
                    
        return matching_blocks
    
    def get_all_blocks(self) -> List[Dict[str, Any]]:
        """Get all blocks in the chain as dictionaries"""
        return [block.to_dict() for block in self.chain]


blockchain = Blockchain()
