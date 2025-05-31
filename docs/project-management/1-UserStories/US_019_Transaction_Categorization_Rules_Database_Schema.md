# US-19: Transaction Categorization Rules Database Schema

**As a** developer,  
**I want to** create a database schema to store transaction categorization rules,  
**So that** the system can perform efficient rule-based categorization before using AI.

**Acceptance Criteria:**

- Create `transaction_categorization` table with:
  - `id` (UUID, primary key)
  - `normalized_description` (VARCHAR, unique constraint)
  - `category_id` (UUID, foreign key to categories table)
  - `source` (ENUM: 'MANUAL', 'AI')
  - `created_at` (TIMESTAMP)
  - `updated_at` (TIMESTAMP)
- Add database indexes for performance on `normalized_description`
- Create database migration scripts
- Verify foreign key constraints with categories table
- Ensure unique constraint prevents duplicate normalized descriptions

**Dependencies:**

- US-18: Add Normalized Description Field 