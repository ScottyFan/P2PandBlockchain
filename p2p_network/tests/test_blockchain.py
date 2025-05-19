# test_blockchain.py
import json
import time
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from p2p_network.blockchain.blockchain import blockchain

def main():
    for i in range(1, 4):
        review_id = f"review-{i}"
        commit_id = f"commit-{i}"
        
        record = {
            "review_id": review_id,
            "commit_id": commit_id,
            "reviewer": f"developer-{i}",
            "status": "PENDING",
            "timestamp": time.time(),
            "comments": []
        }
        blockchain.add_block(record)
        print(f"Added review {review_id} to blockchain (Block #{blockchain.get_latest_block().index})")
        
        time.sleep(1)  # Small delay 
        
        update1 = {
            "review_id": review_id,
            "commit_id": commit_id, 
            "reviewer": f"reviewer-{i}",
            "status": "IN_PROGRESS",
            "timestamp": time.time(),
            "comments": [
                {
                    "line": 42,
                    "text": "This code could be optimized",
                    "author": f"reviewer-{i}"
                }
            ]
        }
        blockchain.add_block(update1)
        print(f"Added comment to review {review_id} (Block #{blockchain.get_latest_block().index})")
        
        time.sleep(1)  # Small delay
        
        update2 = {
            "review_id": review_id,
            "commit_id": commit_id,
            "reviewer": f"reviewer-{i}",
            "status": "COMPLETED",
            "timestamp": time.time(),
            "approved": True,
            "comments": [
                {
                    "line": 42,
                    "text": "This code could be optimized",
                    "author": f"reviewer-{i}"
                },
                {
                    "line": 55,
                    "text": "Good fix!",
                    "author": f"reviewer-{i}"
                }
            ]
        }
        blockchain.add_block(update2)
        print(f"Completed review {review_id} (Block #{blockchain.get_latest_block().index})")
    
    print(f"\nValidating blockchain integrity: {blockchain.is_chain_valid()}")
    
    review_id = "review-2"
    history = blockchain.get_blocks_by_review_id(review_id)
    
    print(f"\nReview history for {review_id}:")
    for i, block in enumerate(history):
        status = block['data']['status']
        timestamp = datetime.fromtimestamp(block['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
        print(f"  {i+1}. Status: {status} at {timestamp}")
        if 'comments' in block['data'] and block['data']['comments']:
            print(f"     Comments: {len(block['data']['comments'])}")
    
    print("\nFull blockchain:")
    for block in blockchain.chain:
        print(f"Block #{block.index} - Hash: {block.hash[:10]}... - Prev: {block.previous_hash[:10]}...")

if __name__ == "__main__":
    main()
