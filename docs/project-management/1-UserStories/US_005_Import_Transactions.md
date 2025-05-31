# US-05: Import Transactions

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