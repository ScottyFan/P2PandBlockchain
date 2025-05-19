'use strict';

const { Contract } = require('fabric-contract-api');

class CodeReviewContract extends Contract {
    async initLedger(ctx) {
        console.log('Code Review Contract initialized');
        return true;
    }
    
    async recordReview(ctx, reviewId, commitId, reviewer, timestamp, status) {
        const review = {
            reviewId,
            commitId,
            reviewer,
            timestamp,
            status,
            type: 'review'
        };
        
        await ctx.stub.putState(reviewId, Buffer.from(JSON.stringify(review)));
        return JSON.stringify(review);
    }
    
    async updateReviewStatus(ctx, reviewId, newStatus) {
        const reviewAsBytes = await ctx.stub.getState(reviewId);
        if (!reviewAsBytes || reviewAsBytes.length === 0) {
            throw new Error(`Review ${reviewId} does not exist`);
        }
        
        const review = JSON.parse(reviewAsBytes.toString());
        review.status = newStatus;
        
        await ctx.stub.putState(reviewId, Buffer.from(JSON.stringify(review)));
        return JSON.stringify(review);
    }
    
    async queryReview(ctx, reviewId) {
        const reviewAsBytes = await ctx.stub.getState(reviewId);
        if (!reviewAsBytes || reviewAsBytes.length === 0) {
            throw new Error(`Review ${reviewId} does not exist`);
        }
        return reviewAsBytes.toString();
    }
    
    async getReviewHistory(ctx, reviewId) {
        const iterator = await ctx.stub.getHistoryForKey(reviewId);
        const results = [];
        
        let result = await iterator.next();
        while (!result.done) {
            const value = result.value.value.toString('utf8');
            results.push(JSON.parse(value));
            result = await iterator.next();
        }
        
        await iterator.close();
        return JSON.stringify(results);
    }
}

module.exports = CodeReviewContract;
