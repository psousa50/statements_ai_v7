# In Progress

## US-18: Add Normalized Description Field

**As a** developer,  
**I want to** store a normalized version of the transaction description in the database,  
**So that** we can use it for fast and consistent matching during categorization.

### Implementation Plan

#### 1. Database Changes
- Create new migration file to add normalized_description column with an index
- Update Transaction model to include the new column

#### 2. Utility Function
- Create text_normalization.py with normalize_description function
- Write unit tests for the normalize_description function

#### 3. Service Layer Updates
- Update TransactionService to use normalize_description when creating/updating transactions
- Update SQLAlchemyTransactionRepository to handle normalized_description in batch operations

#### 4. Testing
- Run all unit tests to ensure nothing is broken
- Manually test transaction creation and updates to verify normalized descriptions are set correctly

#### 5. Documentation
- Update API documentation to mention the new field (if applicable)
- Add comments explaining the normalization process and its purpose
