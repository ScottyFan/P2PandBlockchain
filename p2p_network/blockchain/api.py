# p2p_network/blockchain/api.py
from flask import Blueprint, request, jsonify
import time
import logging

from .blockchain import blockchain

blockchain_api = Blueprint('blockchain_api', __name__)
logger = logging.getLogger(__name__)

@blockchain_api.route('/record', methods=['POST'])
def add_review_record():
    """Add a new code review record to the blockchain"""
    try:
        data = request.json
        required_fields = ['review_id', 'commit_id', 'reviewer', 'status']
        
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'status': 'error',
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Add timestamp if not provided
        if 'timestamp' not in data:
            data['timestamp'] = time.time()
            
        # Create a new block with this review record
        new_block = blockchain.add_block(data)
        
        return jsonify({
            'status': 'success',
            'message': 'Review record added to blockchain',
            'block_index': new_block.index,
            'block_hash': new_block.hash
        }), 201
        
    except Exception as e:
        logger.error(f"Error adding review record: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@blockchain_api.route('/history/<review_id>', methods=['GET'])
def get_review_history(review_id):
    """Get the history of a specific review from the blockchain"""
    try:
        blocks = blockchain.get_blocks_by_review_id(review_id)
        
        if not blocks:
            return jsonify({
                'status': 'error',
                'message': f'No records found for review ID: {review_id}'
            }), 404
            
        return jsonify({
            'status': 'success',
            'review_id': review_id,
            'history': blocks
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving review history: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@blockchain_api.route('/validate', methods=['GET'])
def validate_chain():
    """Validate the integrity of the blockchain"""
    try:
        is_valid = blockchain.is_chain_valid()
        
        return jsonify({
            'status': 'success',
            'is_valid': is_valid,
            'chain_length': len(blockchain.chain)
        }), 200
        
    except Exception as e:
        logger.error(f"Error validating blockchain: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@blockchain_api.route('/blocks', methods=['GET'])
def get_all_blocks():
    """Get all blocks in the blockchain"""
    try:
        blocks = blockchain.get_all_blocks()
        
        return jsonify({
            'status': 'success',
            'block_count': len(blocks),
            'blocks': blocks
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving blocks: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500