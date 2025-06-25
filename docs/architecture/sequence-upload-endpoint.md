# Upload Endpoint Sequence Diagram

This document contains a Mermaid sequence diagram showing the complete flow of the `/upload` endpoint in the Bank Statement Analyzer API.

## Sequence Diagram

```mermaid
sequenceDiagram
    participant Client
    participant API as /upload Endpoint
    participant SUS as StatementUploadService
    participant UFR as UploadedFileRepository
    participant SP as StatementParser
    participant TN as TransactionNormalizer
    participant TRES as TransactionRuleEnhancementService
    participant RBCS as RuleBasedCategorizationService
    participant RBCPS as RuleBasedCounterpartyService
    participant SR as StatementRepository
    participant TR as TransactionRepository
    participant BJS as BackgroundJobService
    participant BT as BackgroundTasks
    participant FAMR as FileAnalysisMetadataRepository

    Client->>API: POST /upload (StatementUploadRequest)
    API->>SUS: upload_statement(upload_data, background_tasks)
    
    Note over SUS: Step 1: Parse Statement
    SUS->>UFR: get_by_id(uploaded_file_id)
    UFR-->>SUS: UploadedFile
    SUS->>SP: parse(filename, file_content)
    SP-->>SUS: DataFrame
    SUS->>TN: normalize(df, column_mapping)
    TN-->>SUS: normalized_df
    SUS-->>SUS: convert to TransactionDTOs
    SUS-->>SUS: ParsedStatement
    
    Note over SUS: Step 2: Enhance Transactions
    SUS->>TRES: enhance_transactions(transaction_dtos)
    TRES->>RBCS: categorize_batch(normalized_descriptions)
    RBCS-->>TRES: categorization_results
    TRES->>RBCPS: identify_counterparty_batch(description_amount_pairs)
    RBCPS-->>TRES: counterparty_results
    TRES-->>SUS: EnhancedTransactions
    
    Note over SUS: Step 3: Save Statement
    SUS->>UFR: find_by_id(uploaded_file_id)
    UFR-->>SUS: UploadedFile
    SUS->>SR: save(account_id, filename, file_type, content)
    SR-->>SUS: Statement
    SUS-->>SUS: enrich DTOs with statement_id
    SUS->>TR: save_batch(enhanced_dtos)
    TR-->>SUS: persistence_results
    SUS->>FAMR: save(file_analysis_metadata)
    FAMR-->>SUS: saved_metadata
    SUS-->>SUS: SavedStatement
    
    Note over SUS: Step 4: Schedule Background Jobs
    alt Has unmatched transactions
        SUS->>BJS: queue_ai_categorization_job(statement_id, unmatched_transaction_ids)
        BJS-->>SUS: categorization_job
    end
    
    SUS->>BJS: queue_ai_counterparty_identification_job(statement_id, all_transaction_ids)
    BJS-->>SUS: counterparty_job
    SUS-->>SUS: ScheduledJobs
    
    Note over SUS: Optional: Trigger Immediate Processing
    opt Background tasks provided
        SUS->>BT: add_task(process_pending_jobs)
    end
    
    Note over SUS: Build and Return Result
    SUS-->>API: StatementUploadResult
    API-->>Client: StatementUploadResponse
    
    Note over BT: Background Processing (Async)
    BT->>BJS: process_ai_categorization_job
    BT->>BJS: process_ai_counterparty_job
```

## Flow Description

### Simplified 4-Step Process

1. **Parse Statement** - Convert uploaded file to structured transaction DTOs
2. **Enhance Transactions** - Apply rule-based categorization and counterparty identification  
3. **Save Statement** - Persist transactions to database with deduplication and metadata
4. **Schedule Background Jobs** - Queue AI processing for unmatched transactions

### Key Components

- **StatementUploadService**: Main orchestrator using clean 4-step process
- **TransactionRuleEnhancementService**: Pure enhancement service (no side effects)
- **StatementRepository & TransactionRepository**: Handle database persistence
- **BackgroundJobService**: Manages asynchronous AI processing
- **RuleBasedCategorizationService**: Applies categorization rules
- **RuleBasedCounterpartyService**: Identifies transaction counterparties

### Architectural Improvements

**Separation of Concerns:**
- **Enhancement** is now pure (no database operations)
- **Persistence** is handled directly by repositories (no intermediate service layer)
- **Job scheduling** is isolated as its own step

**Benefits:**
- Easier to test each step independently
- Clear responsibility boundaries
- Better error handling per step
- More maintainable and readable code

### Background Processing

The system queues two types of background jobs:
- **AI Categorization**: For transactions not matched by rules
- **AI Counterparty Identification**: For all transactions to enhance counterparty data

Background jobs can run immediately via FastAPI BackgroundTasks or be processed later by cron jobs.