# US-02: Analyze Bank Statement Schema

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