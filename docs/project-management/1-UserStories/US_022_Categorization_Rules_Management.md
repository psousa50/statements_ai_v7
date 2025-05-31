# US-22: Categorization Rules Management

**As a** user,  
**I want to** view and manage categorization rules,  
**So that** I can understand and improve the automatic categorization system.

**Acceptance Criteria:**

- Create `GET /api/categorization-rules` endpoint with:
  - Pagination support
  - Filtering by source (MANUAL, AI)
  - Filtering by category
  - Sorting by confidence, created_at
  - Include usage statistics and match counts
- Create `POST /api/categorization-rules` endpoint for creating manual rules
- Create `PUT /api/categorization-rules/{id}` endpoint for updating rules
- Create `DELETE /api/categorization-rules/{id}` endpoint for removing rules
- Add validation to prevent conflicting rules (same normalized description)
- Include confidence scores and last used timestamps
- Frontend interface for rules management:
  - View rules in paginated table
  - Create new manual rules
  - Edit existing rules
  - Delete rules with confirmation
  - Search and filter rules
  - Bulk operations for rule management

**Dependencies:**

- US-19: Transaction Categorization Rules Database Schema
- US-20: Rule-Based Categorization Service 