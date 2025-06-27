# Sequence Diagram - Statement Processing Flow

This diagram shows the complete flow of processing a bank statement from upload to transaction import. AI categorization and counterparty services have been removed, but background job infrastructure remains available.

```mermaid
sequenceDiagram
    participant User
    participant WebApp as React Web App
    participant API as FastAPI Backend
    participant FileDetector as File Type Detector
    participant SchemaDetector as Schema Detector
    participant Parser as Statement Parser
    participant Normalizer as Transaction Normalizer
    participant Orchestrator as Processing Orchestrator
    participant RuleCategorizer as Rule-Based Categorizer
    participant BackgroundJobs as Background Job Service
    participant Database as PostgreSQL
    participant GeminiAI as Google Gemini AI
    participant FileSystem as File System
    
    User->>WebApp: Upload bank statement file
    WebApp->>API: POST /statements/upload
    
    API->>FileDetector: detect_file_type(file)
    FileDetector-->>API: FileType (CSV/XLSX)
    
    API->>FileSystem: Save uploaded file
    FileSystem-->>API: File path
    
    API->>Database: Create UploadedFile record
    Database-->>API: UploadedFile ID
    
    API->>SchemaDetector: detect_schema(file_path)
    SchemaDetector->>GeminiAI: Analyze file structure
    GeminiAI-->>SchemaDetector: Column mappings
    SchemaDetector-->>API: StatementSchema
    
    API->>Database: Save FileAnalysisMetadata
    Database-->>API: Analysis ID
    
    API->>Parser: parse_statement(file_path, schema)
    Parser-->>API: List[TransactionDTO]
    
    API->>Normalizer: normalize_transactions(transactions)
    Normalizer-->>API: List[TransactionDTO] (normalized)
    
    API->>Orchestrator: process_transactions(transactions, account_id)
    
    loop For each transaction
        Orchestrator->>Database: Check for duplicates
        Database-->>Orchestrator: Duplicate status
        
        alt Not duplicate
            Orchestrator->>Database: Save transaction
            Database-->>Orchestrator: Transaction ID
        end
    end
    
    Orchestrator->>RuleCategorizer: Apply categorization rules
    RuleCategorizer->>Database: Match against enhancement rules
    Database-->>RuleCategorizer: Matching rules
    RuleCategorizer-->>Orchestrator: Rule-based categorizations
    
    Orchestrator->>Database: Update transactions with categories
    Database-->>Orchestrator: Update confirmation
    
    Orchestrator-->>API: ProcessingResult
    API-->>WebApp: StatementUploadResult
    WebApp-->>User: Upload success with statistics
    
    Note over BackgroundJobs: Background job infrastructure available
    Note over BackgroundJobs: AI categorization services removed
```