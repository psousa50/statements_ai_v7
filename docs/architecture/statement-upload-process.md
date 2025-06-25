# Statement Upload Process

This document explains the complete end-to-end process for uploading and processing bank statements in the Statements AI system.

## Overview

The statement upload process is designed as a **two-phase hybrid approach**:

1. **🔄 Synchronous Phase**: Immediate processing during upload (rule-based categorization)
2. **⚡ Asynchronous Phase**: Background processing (AI categorization + rule creation)

This approach provides **immediate user feedback** for known patterns while expensive AI processing happens seamlessly in the background.

**Key Architecture Change**: The system now uses a **DTO-based processing flow** that eliminates the inefficient save→load→update cycle by processing transactions in memory before persisting them once with all data complete.

---

## Complete Process Flow

```text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           STATEMENT UPLOAD PROCESS                                  │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  📁 File Upload                                                                     │
│       │                                                                             │
│       ▼                                                                             │
│  🔍 Schema Detection & Parsing                                                      │
│       │                                                                             │
│       ▼                                                                             │
│  ⚡ SYNCHRONOUS PHASE (< 500ms)                                                     │
│   ┌─────────────────────────────────────────────────────────────────────────────┐   │
│   │ • Parse to Transaction DTOs (unpersisted)                                  │   │
│   │ • DTO Processing & Rule-Based Categorization                               │   │
│   │ • Single Database Persistence (complete data)                              │   │
│   │ • Background Job Creation (for unmatched)                                  │   │
│   │ • Immediate Response with Results                                           │   │
│   └─────────────────────────────────────────────────────────────────────────────┘   │
│       │                                                                             │
│       ▼                                                                             │
│  🔄 ASYNCHRONOUS PHASE (background)                                                 │
│   ┌─────────────────────────────────────────────────────────────────────────────┐   │
│   │ • AI Categorization (unmatched transactions only)                          │   │
│   │ • New Rule Creation (from AI results)                                      │   │
│   │ • Progress Tracking & Updates                                               │   │
│   │ • Error Handling & Retry Logic                                             │   │
│   └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```text

---

## Phase 1: Synchronous Processing (During Upload)

### Step 1: File Upload & Initial Processing

```text
POST /statements/upload
│
├─► 📁 File Validation
│   ├─ File type check (.csv, .xlsx, etc.)
│   ├─ Size validation (< 10MB)
│   └─ Format verification
│
├─► 🔍 Schema Detection
│   ├─ HeuristicSchemaDetector (pattern matching)
│   ├─ LLMSchemaDetector (AI-powered fallback)
│   └─ Column mapping identification
│
└─► 📊 Transaction Parsing (to DTOs)
    ├─ Raw data extraction
    ├─ Data type conversion
    └─ TransactionDTO objects (unpersisted)
```text

### Step 2: StatementUploadService Orchestration

The **StatementUploadService** orchestrates the complete upload and processing flow:

```text
┌─────────────────────────────────────────────────────────────────┐
│                    StatementUploadService                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📝 Input: StatementUploadRequest                               │
│       │                                                         │
│       ▼                                                         │
│  📊 Parse to Transaction DTOs (unpersisted)                     │
│   ├─ Parse file content to dataframe                           │
│   ├─ Apply column mapping & normalization                      │
│   ├─ Create TransactionDTO objects                             │
│   └─ DTOs contain: description, amount, date, etc.             │
│       │                                                         │
│       ▼                                                         │
│  🎯 Process DTOs (TransactionProcessingOrchestrator)            │
│   ├─ Normalize descriptions for rule matching                  │
│   ├─ Query: transaction_categorization table                   │
│   ├─ Match: normalized_description → category_id               │
│   ├─ Enrich DTOs with categorization data                      │
│   └─ NO database writes - all in memory                        │
│       │                                                         │
│       ▼                                                         │
│  💾 Single Database Save (StatementPersistenceService)         │
│   ├─ Save processed DTOs with all data complete                │
│   ├─ Include: categories, status, normalized descriptions      │
│   └─ One batch insert operation                                │
│       │                                                         │
│       ▼                                                         │
│  🔄 Background Job Creation (post-persistence)                  │
│   ├─ Query database for unmatched transaction IDs              │
│   ├─ Create background job with unmatched IDs                  │
│   └─ Schedule AI categorization                                │
│       │                                                         │
│       ▼                                                         │
│  📤 Response: StatementUploadResult                             │
│   ├─ immediate_results: rule-based matches                     │
│   ├─ background_job_info: job_id + estimated_time              │
│   └─ statistics: processed/matched/unmatched counts            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```text

### Step 3: DTO Processing Detail

```text
┌─────────────────────────────────────────────────────────────────┐
│              TransactionProcessingOrchestrator                  │
│                   (process_transaction_dtos)                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📝 Input: List<TransactionDTO> (unpersisted)                   │
│       │                                                         │
│       ▼                                                         │
│  🔧 DTO Normalization                                           │
│   ├─ For each DTO: normalize_description(dto.description)      │
│   ├─ Set: dto.normalized_description                           │
│   └─ Set: dto.categorization_status = UNCATEGORIZED            │
│       │                                                         │
│       ▼                                                         │
│  🎯 Rule-Based Categorization (in memory)                       │
│   ├─ Extract unique normalized descriptions                     │
│   ├─ Query: transaction_categorization table                   │
│   ├─ For each matched DTO:                                     │
│   │   ├─ dto.category_id = matched_category_id                 │
│   │   └─ dto.categorization_status = CATEGORIZED               │
│   └─ Unmatched DTOs remain UNCATEGORIZED                       │
│       │                                                         │
│       ▼                                                         │
│  📊 Results Summary (DTOProcessingResult)                       │
│   ├─ processed_dtos: All DTOs with enriched data               │
│   ├─ total_processed, rule_based_matches                       │
│   ├─ unmatched_dto_count                                       │
│   └─ processing_time_ms                                        │
│                                                                 │
│  ⚠️  NO Database Writes - Pure DTO Processing                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```text

### Step 4: Immediate Response

```textjson
{
  "immediate_results": {
    "total_processed": 12,
    "rule_matched": 8,
    "unmatched": 4,
    "rule_matched_transactions": [
      {
        "transaction_id": "123e4567-e89b-12d3-a456-426614174000",
        "description": "STARBUCKS COFFEE",
        "category": "Food & Dining",
        "confidence": 1.0,
        "source": "RULE_BASED"
      }
    ]
  },
  "background_job": {
    "job_id": "789e0123-e89b-12d3-a456-426614174999",
    "status": "PENDING",
    "estimated_completion_time": "2024-12-19T10:05:30Z",
    "unmatched_transaction_count": 4
  },
  "statistics": {
    "processing_time_ms": 245,
    "ai_cost_saved": 0.80,
    "rules_used": 3
  }
}
```text

---

## Phase 2: Asynchronous Processing (Background)

### Background Job Processor Architecture

```text
┌─────────────────────────────────────────────────────────────────┐
│                    Background Job Processor                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  🔄 Job Claiming (atomic)                                       │
│   ├─ SELECT FOR UPDATE from background_jobs                     │
│   ├─ Status: PENDING → IN_PROGRESS                              │
│   └─ Set: started_at = NOW(), worker_id                         │
│       │                                                         │
│       ▼                                                         │
│  📋 Job Data Extraction (session-safe)                          │
│   ├─ Extract: job_id, job_type, progress                        │
│   ├─ Get: unmatched_transaction_ids[]                           │
│   └─ Avoid: object session detachment                           │
│       │                                                         │
│       ▼                                                         │
│  🤖 AI Categorization Process                                   │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ For each transaction_id:                                │   │
│   │   ├─ 🔍 Fetch fresh Transaction from DB                 │   │
│   │   ├─ 🧠 LLM Categorization (single call)                │   │
│   │   ├─ ✅ Update: category_id + confidence + status       │   │
│   │   ├─ 💾 Database: transaction.update()                  │   │
│   │   ├─ 📝 Create Rule: normalized_description → category  │   │
│   │   └─ 📊 Progress Update                                 │   │
│   └─────────────────────────────────────────────────────────┘   │
│       │                                                         │
│       ▼                                                         │
│  📈 Progress Tracking                                           │
│   ├─ Update job.progress every batch                            │
│   ├─ WebSocket notifications (optional)                         │
│   └─ Real-time status updates                                   │
│       │                                                         │
│       ▼                                                         │
│  ✅ Job Completion                                              │
│   ├─ Status: IN_PROGRESS → COMPLETED                            │
│   ├─ Set: completed_at = NOW()                                  │
│   └─ Result: final statistics                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```text

### AI Categorization Detail

```text
┌─────────────────────────────────────────────────────────────────┐
│                    _categorize_single_transaction_by_id          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  🔍 Input: transaction_id (UUID)                                │
│       │                                                         │
│       ▼                                                         │
│  📥 Fetch Fresh Transaction                                     │
│   ├─ transaction = repository.get_by_id(transaction_id)         │
│   └─ Ensures current session attachment                        │
│       │                                                         │
│       ▼                                                         │
│  🧠 LLM Categorization                                          │
│   ├─ Call: transaction_categorizer.categorize([transaction])    │
│   ├─ Input: transaction description + available categories     │
│   └─ Output: CategorizationResult                              │
│       │                                                         │
│       ▼                                                         │
│  ✅ Success Path                                                │
│   ├─ Update transaction:                                       │
│   │   ├─ category_id = result.category_id                      │
│   │   ├─ categorization_confidence = result.confidence         │
│   │   └─ categorization_status = CATEGORIZED                   │
│   ├─ 💾 repository.update(transaction)                         │
│   │                                                            │
│   ├─ 📝 Create Categorization Rule:                            │
│   │   ├─ Check: existing rule for normalized_description       │
│   │   ├─ Create: new rule if none exists                       │
│   │   │   ├─ normalized_description → category_id              │
│   │   │   ├─ source = AI                                       │
│   │   │   └─ created_at = NOW()                               │
│   │   └─ 🚫 Skip if rule already exists                        │
│   │                                                            │
│   └─ ✅ Success: Future uploads will use this rule              │
│       │                                                         │
│       ▼                                                         │
│  ❌ Error Handling                                              │
│   ├─ No results: status = FAILURE + log warning               │
│   ├─ LLM error: status = FAILURE + retry logic                │
│   └─ Rule creation error: log warning (don't fail transaction) │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```text

---

## Key Components & Responsibilities

### 1. StatementUploadService

```text
Responsibilities:
├─ Orchestrate complete upload and processing flow
├─ Coordinate: parsing → DTO processing → persistence
├─ Handle background job scheduling (post-persistence)
├─ Manage file analysis metadata
├─ Return comprehensive upload results
└─ Provide single entry point for statement uploads

Methods:
├─ upload_and_process(upload_request) → StatementUploadResult
├─ _parse_to_transaction_dtos(...) → List<TransactionDTO>
├─ _get_unmatched_transaction_ids(...) → List<UUID>
└─ _save_file_analysis_metadata(...)
```text

### 2. StatementAnalyzerService

```text
Responsibilities:
├─ File format detection
├─ Schema analysis (heuristic + LLM)
├─ Transaction parsing
└─ Data validation
```text

### 3. TransactionProcessingOrchestrator

```text
Responsibilities:
├─ DTO normalization and processing
├─ Rule-based categorization (in memory)
├─ Background job coordination
├─ Processing result generation
└─ Support both entity and DTO processing

Methods:
├─ process_transactions(transactions) → SyncCategorizationResult (legacy)
├─ process_transaction_dtos(dtos) → DTOProcessingResult (new)
└─ get_background_job_info(...) → BackgroundJobInfo
```text

### 4. StatementPersistenceService

```text
Responsibilities:
├─ Traditional file parsing and persistence
├─ DTO-based persistence (new)
├─ Transaction normalization
└─ Database operations

Methods:
├─ persist(request) → PersistenceResultDTO (legacy)
├─ save_processed_transactions(dtos) → PersistenceResultDTO (new)
└─ File analysis metadata management
```text

### 5. RuleBasedCategorizationService

```text
Responsibilities:
├─ Query transaction_categorization table
├─ Batch categorization matching
├─ Normalized description lookup
└─ Category mapping
```text

---

## Database Schema Integration

### New Transaction Flow (DTO-Based)

```textsql
-- Single persistence with all data complete
INSERT INTO transactions (
  description, 
  normalized_description,     -- ← Set during DTO processing
  category_id,               -- ← Set during DTO processing (if rule matched)
  categorization_status,     -- ← Set during DTO processing
  categorization_confidence, -- ← Set during DTO processing
  amount,
  date,
  source_id,
  uploaded_file_id,
  created_at
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NOW());

-- Background job creation (after persistence)
INSERT INTO background_jobs (
  job_type = 'AI_CATEGORIZATION',
  status = 'PENDING',
  progress = '{"unmatched_transaction_ids": [...]}'
) WHERE unmatched_count > 0;

-- AI categorization (background - unchanged)
UPDATE transactions SET 
  category_id = ?, 
  categorization_confidence = ?,
  categorization_status = 'CATEGORIZED'
WHERE id = ?;

-- Rule creation from AI results (background - unchanged)
INSERT INTO transaction_categorization (
  normalized_description,
  category_id,
  source = 'AI',
  created_at = NOW()
);
```text

### Performance Benefits

```text
Old Flow (save→load→update):
├─ INSERT transactions (incomplete data)     ~50ms
├─ SELECT transactions (reload)              ~20ms  
├─ UPDATE transactions (add categories)      ~30ms
└─ Total: ~100ms + N+1 query problems

New Flow (DTO-based):
├─ Process DTOs in memory                    ~15ms
├─ INSERT transactions (complete data)       ~50ms
└─ Total: ~65ms (35% faster)
```text

---

## Performance Characteristics

### Cost Optimization Over Time

```text
Upload Scenario          | Rule Matches | AI Calls | Cost Impact
-------------------------|--------------|----------|-------------
First upload (cold)      | 0%          | 100%     | $$ Full cost
After 5 uploads          | 60%         | 40%      | $$ 40% cost
After 20 uploads         | 85%         | 15%      | $$ 15% cost
Mature system (100+)     | 95%         | 5%       | $$ 5% cost
```text

### Response Time Targets (Improved)

```text
Phase                    | Target Time  | Old Performance | New Performance
-------------------------|--------------|-----------------|------------------
File upload & parsing    | < 200ms     | ~150ms          | ~150ms
DTO processing + rules   | < 250ms     | N/A             | ~180ms (new)
Database persistence     | < 100ms     | ~100ms (2 ops)  | ~65ms (1 op)
Total sync response      | < 500ms     | ~450ms          | ~395ms
AI categorization/tx     | < 2000ms    | ~1500ms         | ~1500ms
Background job complete  | < 5min      | ~2-3min         | ~2-3min
```text

### Architecture Benefits

```text
Metric                   | Old Architecture | New Architecture | Improvement
-------------------------|------------------|------------------|-------------
Database operations      | 2-3 per upload  | 1 per upload     | 50-66% reduction
Memory efficiency        | Load + process   | Process only     | Lower memory usage
Code complexity          | Route heavy      | Service focused  | Better separation
Testability              | Route mocking    | Service mocking  | Easier testing
Error handling           | Distributed      | Centralized      | Better reliability
```text

---

## New DTO Processing Models

### StatementUploadResult

```textpython
class StatementUploadResult:
    uploaded_file_id: str
    transactions_saved: int
    total_processed: int
    rule_based_matches: int
    match_rate_percentage: float
    processing_time_ms: int
    background_job_info: Optional[BackgroundJobInfo]
```text

### DTOProcessingResult

```textpython
class DTOProcessingResult:
    processed_dtos: List[TransactionDTO]      # All DTOs with enriched data
    total_processed: int
    rule_based_matches: int
    unmatched_dto_count: int
    processing_time_ms: int
    match_rate_percentage: float
    
    @property
    def has_unmatched_transactions(self) -> bool:
        return self.unmatched_dto_count > 0
```text

### Enhanced TransactionDTO

```textpython
class TransactionDTO:
    # Core transaction data
    date: str
    amount: float
    description: str
    uploaded_file_id: str
    source_id: Optional[str]
    
    # Processing metadata (new)
    category_id: Optional[UUID]              # ← Set during DTO processing
    categorization_status: Optional[str]     # ← Set during DTO processing
    normalized_description: Optional[str]    # ← Set during DTO processing
    
    # Database metadata
    id: Optional[str]
    created_at: Optional[datetime]
```text

---

## Error Handling & Recovery

### Synchronous Phase Errors

```text
Error Type                | Handling Strategy
--------------------------|------------------------------------------
File format invalid       | Immediate 400 error + user feedback
Schema detection fails    | Fallback to LLM detector
Parsing errors            | Skip invalid rows + warning
Database connection       | 500 error + retry suggestion
Rule query timeout        | Continue without rules + warning
```text

### Asynchronous Phase Errors

```text
Error Type                | Handling Strategy
--------------------------|------------------------------------------
LLM API timeout           | Retry with exponential backoff
LLM API rate limit        | Queue for retry with delay
Transaction not found     | Log warning + skip (data consistency)
Database deadlock         | Retry transaction
Rule creation conflict    | Log warning + continue (duplicate key)
Job processor crash       | Job remains IN_PROGRESS + manual reset
```text

---

## Monitoring & Operations

### Key Metrics to Track

```text
📊 Performance Metrics:
├─ Upload response time (sync phase)
├─ Background job completion time
├─ Rule-based match percentage
├─ AI categorization success rate
└─ Cost per transaction over time

🔍 Health Checks:
├─ Background job queue length
├─ Failed job count
├─ Stuck job detection (> 10min IN_PROGRESS)
├─ Database connection pool health
└─ LLM API availability

💰 Cost Tracking:
├─ AI calls per upload
├─ Monthly AI spend
├─ Cost savings from rules
└─ ROI on rule creation
```text

### Operational Scripts

```textbash
# Monitor system health
python check_jobs_status.py

# Reset stuck jobs
python reset_stuck_jobs.py

# Check rule effectiveness
python check_categorization_rules.py
```text

---

## Testing Strategy

### Unit Tests

- ✅ Transaction DTO processing and normalization
- ✅ Rule-based categorization logic (in-memory)
- ✅ StatementUploadService orchestration
- ✅ Background job processor (ID-based architecture)
- ✅ LLM categorizer with mocked AI responses
- ✅ Error handling and edge cases
- ✅ Service layer separation of concerns

### Integration Tests

- ✅ End-to-end upload flow (route → service → persistence)
- ✅ DTO processing pipeline verification
- ✅ Database persistence verification (single operation)
- ✅ Background job lifecycle
- ✅ Rule creation and application

### Service Layer Tests

- ✅ StatementUploadService.upload_and_process()
- ✅ TransactionProcessingOrchestrator.process_transaction_dtos()
- ✅ StatementPersistenceService.save_processed_transactions()
- ✅ Route delegation and HTTP response transformation
- ✅ Mock-based testing for service dependencies

### Performance Tests

- 📋 Large file upload (1000+ transactions)
- 📋 DTO processing throughput
- 📋 Single-persistence performance validation
- 📋 Concurrent upload handling
- 📋 Background job throughput
- 📋 Database performance under load

---

This architecture provides a robust, scalable, and cost-effective solution for transaction categorization that improves over time through machine learning and rule accumulation. **The new DTO-based processing eliminates inefficient database operations while maintaining all existing functionality.**

