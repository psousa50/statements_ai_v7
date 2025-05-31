# US-20: Rule-Based Categorization Service

**As a** developer,  
**I want to** implement a service that categorizes transactions using database rules,  
**So that** known transaction patterns are quickly categorized without expensive AI calls.

**Acceptance Criteria:**

- Create `RuleBasedCategorizationService` with:
  - `categorizeBatch(normalizedDescriptions: string[])` method
  - Batch processing with configurable batch size (default 100)
  - Returns map of normalized_description → category_id
- Service queries `transaction_categorization` table efficiently using prepared statements
- Handle empty batches gracefully
- Log categorization statistics (matched vs unmatched)
- Include comprehensive unit and integration tests
- Use database connection pooling for performance
- Implement caching for frequently matched descriptions

**Dependencies:**

- US-19: Transaction Categorization Rules Database Schema 