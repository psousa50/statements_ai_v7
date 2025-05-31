# US-21: Enhanced Transaction Processing Orchestrator

**As a** developer,  
**I want to** enhance the transaction processing orchestrator to use rule-based categorization first, then AI,  
**So that** the system efficiently processes transactions using the fastest method first.

**Acceptance Criteria:**

- Update `TransactionProcessor` to implement two-phase categorization:
  - Phase 1: Extract unique normalized descriptions and attempt rule-based categorization
  - Phase 2: Use AI categorization only for unmatched transactions
  - Phase 3: Update transaction_categorization table with new AI results
- Handle conflicts when AI returns different categories for same normalized description
- Implement learning mechanism that stores successful AI categorizations as rules
- Add comprehensive logging of processing stages and performance metrics
- Include progress tracking for large uploads
- Implement rollback capability on processing failures
- Add idempotency for retry scenarios
- Support both manual and automatic categorization triggers

**Dependencies:**

- US-20: Rule-Based Categorization Service
- US-13: Enhanced Batch Categorization with Detailed Results 