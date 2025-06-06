# US-18: Add Normalized Description Field

**As a** developer,  
**I want to** store a normalized version of the transaction description in the database,  
**So that** we can use it for fast and consistent matching during categorization.

**Acceptance Criteria:**

- Add `normalized_description` column to transactions table
- Create `normalize_description()` utility function
- Add DB index on `normalized_description` for performance

**Dependencies:**

- None
