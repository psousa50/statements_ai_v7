# User Stories

This document contains all the user stories for the Bank Statement Analyzer application. Each story has a title, description, acceptance criteria, and dependencies.

## File Upload and Processing

### US-01: Upload Bank Statement

**As a** user,  
**I want to** upload my bank statement file,  
**So that** I can analyze my transactions without manual data entry.

**Acceptance Criteria:**
- User can drag and drop a file onto the upload zone
- User can click to browse and select a file
- Supported file formats: CSV, Excel (XLSX)
- User receives feedback during the upload process
- User is notified if the file format is unsupported
- File is securely transmitted to the backend for processing

**Dependencies:**
- None

### US-02: Analyze Bank Statement Schema

**As a** user,  
**I want the** system to automatically detect the structure of my bank statement,  
**So that** I don't have to manually map columns.

**Acceptance Criteria:**
- System detects file type (CSV, XLSX)
- System identifies header row
- System identifies where data rows begin
- System suggests column mappings for date, description, and amount
- User is shown the analysis results
- System detects and prevents duplicate file uploads via file hashing

**Dependencies:**
- US-01: Upload Bank Statement

### US-03: Customize Column Mapping

**As a** user,  
**I want to** review and customize the column mapping for my bank statement,  
**So that** I can correct any misidentified columns.

**Acceptance Criteria:**
- User can view the suggested column mappings
- User can modify the mappings through a user-friendly interface
- User can see a preview of how the data will be imported
- User can confirm the mappings to proceed with import
- User can cancel the import process

**Dependencies:**
- US-02: Analyze Bank Statement Schema

### US-04: Select Statement Source

**As a** user,  
**I want to** specify the source (bank) of my statement,  
**So that** my transactions are properly organized.

**Acceptance Criteria:**
- User can select from a list of existing sources
- User can add a new source if needed
- Source selection is required before finalizing import
- Selected source is associated with imported transactions

**Dependencies:**
- US-02: Analyze Bank Statement Schema

### US-05: Import Transactions

**As a** user,  
**I want to** finalize the import of my bank statement,  
**So that** the transactions are saved to the system.

**Acceptance Criteria:**
- User can confirm the import after reviewing mappings and source
- System extracts and normalizes transactions from the file
- System saves transactions to the database
- System associates transactions with the uploaded file and source
- User is shown a summary of imported transactions
- User is redirected to the transactions page after successful import
- System handles errors gracefully and provides clear error messages

**Dependencies:**
- US-03: Customize Column Mapping
- US-04: Select Statement Source

## Transaction Management

### US-06: View Transactions

**As a** user,  
**I want to** view my imported transactions,  
**So that** I can review my financial activity.

**Acceptance Criteria:**
- User can see a list of all transactions
- Transactions are displayed in a table format
- Table shows date, description, amount, and category
- Transactions are sorted by date (newest first) by default
- User can see the categorization status of each transaction

**Dependencies:**
- None (can view empty state before any imports)

### US-07: Add Transaction Manually

**As a** user,  
**I want to** add a transaction manually,  
**So that** I can include transactions not in my bank statements.

**Acceptance Criteria:**
- User can access a form to add a new transaction
- Form includes fields for date, description, amount, and category
- Form validates input before submission
- Successfully added transaction appears in the transactions list
- User receives confirmation after successful addition

**Dependencies:**
- None

### US-08: Edit Transaction

**As a** user,  
**I want to** edit an existing transaction,  
**So that** I can correct any errors or update information.

**Acceptance Criteria:**
- User can select a transaction to edit
- Edit form is pre-populated with current transaction data
- User can modify any field
- Form validates input before submission
- Changes are saved to the database
- Updated transaction is reflected in the transactions list
- User receives confirmation after successful update

**Dependencies:**
- US-06: View Transactions

### US-09: Delete Transaction

**As a** user,  
**I want to** delete a transaction,  
**So that** I can remove duplicate or erroneous entries.

**Acceptance Criteria:**
- User can select a transaction to delete
- User is asked to confirm deletion
- Transaction is removed from the database after confirmation
- Transaction is removed from the transactions list
- User receives confirmation after successful deletion

**Dependencies:**
- US-06: View Transactions

## Categorization

### US-10: Manage Categories

**As a** user,  
**I want to** create, edit, and delete categories,  
**So that** I can organize my transactions according to my needs.

**Acceptance Criteria:**
- User can view a list of existing categories
- User can create a new category with a name
- User can create hierarchical categories (parent-child relationships)
- User can edit a category's name and parent
- User can delete a category if it has no associated transactions
- Categories are displayed in a hierarchical structure
- User receives appropriate feedback after each action

**Dependencies:**
- None

### US-11: Categorize Transaction

**As a** user,  
**I want to** assign a category to a transaction,  
**So that** I can organize my spending.

**Acceptance Criteria:**
- User can select a category for a transaction
- User can select from a hierarchical list of categories
- User can change a transaction's category
- User can remove a category from a transaction
- Categorization status is updated accordingly
- Changes are saved to the database
- User receives confirmation after successful categorization

**Dependencies:**
- US-06: View Transactions
- US-10: Manage Categories

### US-12: Batch Categorize Transactions

**As a** user,  
**I want the** system to automatically categorize transactions in batches,  
**So that** I can save time on manual categorization.

**Acceptance Criteria:**
- User can trigger batch categorization
- System processes uncategorized transactions
- System assigns categories based on transaction descriptions
- System updates categorization status for processed transactions
- User can specify the batch size
- User receives a summary of categorization results
- User can still manually categorize transactions as needed

**Dependencies:**
- US-10: Manage Categories
- US-11: Categorize Transaction

### US-13: Enhanced Batch Categorization with Detailed Results

**As a** system administrator or power user,  
**I want the** categorization system to process multiple transactions efficiently and provide detailed results for each transaction,  
**So that** I can track the success and failure of categorization attempts and handle large volumes of transactions effectively.

**Acceptance Criteria:**
- System can accept a list of transactions for batch processing
- System returns detailed results for each transaction including:
  - Transaction ID
  - Assigned category ID (if successful)
  - Categorization status (Categorized or Failed)
- System processes transactions efficiently in batch mode
- Failed categorizations include error information
- System maintains transaction order in results
- System handles partial failures gracefully (some succeed, some fail)
- System provides performance improvements over single-transaction processing
- API supports both single and batch categorization modes

**Dependencies:**
- US-10: Manage Categories
- US-11: Categorize Transaction
- US-12: Batch Categorize Transactions

## Future Stories (Planned)

### US-14: Visualize Spending by Category

**As a** user,  
**I want to** see visual representations of my spending by category,  
**So that** I can understand my spending patterns.

**Acceptance Criteria:**
- User can view a pie chart of spending by category
- User can view a bar chart of spending over time
- User can filter visualizations by date range
- Visualizations are interactive and responsive
- Data is accurate and reflects categorized transactions

**Dependencies:**
- US-11: Categorize Transaction

### US-15: Export Transactions

**As a** user,  
**I want to** export my transactions,  
**So that** I can use the data in other applications.

**Acceptance Criteria:**
- User can export transactions in CSV or JSON format
- User can select which transactions to export
- User can choose which fields to include in the export
- Export includes category information
- User can download the exported file

**Dependencies:**
- US-06: View Transactions

### US-16: User Authentication

**As a** user,  
**I want to** securely log in to the application,  
**So that** my financial data is protected.

**Acceptance Criteria:**
- User can register with email and password
- User can log in with credentials
- User can log out
- User can reset password
- User data is isolated from other users
- Sessions expire after a period of inactivity
story- Passwords are securely hashed and stored

**Dependencies:**
- None

### US-17: Search and Filter Transactions

**As a** user,  
**I want to** search and filter my transactions,  
**So that** I can find specific transactions or groups of transactions.

**Acceptance Criteria:**
- User can search transactions by description
- User can filter transactions by date range
- User can filter transactions by amount range
- User can filter transactions by category
- User can filter transactions by source
- User can filter transactions by categorization status
- User can combine multiple filters
- Search and filter results update in real-time
- User can clear all filters

**Dependencies:**
- US-06: View Transactions

### US-18: Add Normalized Description Field

**As a** developer,  
**I want to** store a normalized version of the transaction description in the database,  
**So that** we can use it for fast and consistent matching during categorization.

**Acceptance Criteria:**
- Add `normalized_description` column to transactions table
- Create `normalize_description()` utility function
- Add DB index on `normalized_description` for performance

