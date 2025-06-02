# Statement Upload Process

This document explains the complete end-to-end process for uploading and processing bank statements in the Statements AI system.

## Overview

The statement upload process is designed as a **two-phase hybrid approach**:

1. **🔄 Synchronous Phase**: Immediate processing during upload (rule-based categorization)
2. **⚡ Asynchronous Phase**: Background processing (AI categorization + rule creation)

This approach provides **immediate user feedback** for known patterns while expensive AI processing happens seamlessly in the background.

---

## Complete Process Flow

```
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
│   │ • Transaction Normalization                                                │   │
│   │ • Rule-Based Categorization (existing rules)                               │   │
│   │ • Database Persistence                                                     │   │
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
```

---

## Phase 1: Synchronous Processing (During Upload)

### Step 1: File Upload & Initial Processing

```
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
└─► 📊 Transaction Parsing
    ├─ Raw data extraction
    ├─ Data type conversion
    └─ Initial transaction objects
```

### Step 2: Transaction Processing Orchestrator

The **TransactionProcessingOrchestrator** handles the immediate categorization:

```
┌─────────────────────────────────────────────────────────────────┐
│                TransactionProcessingOrchestrator                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📝 Input: List<Transaction> (parsed from file)                 │
│       │                                                         │
│       ▼                                                         │
│  🔧 Transaction Normalization                                   │
│   ├─ Clean descriptions (remove extra spaces, etc.)            │
│   ├─ Generate normalized_description                            │
│   └─ Set initial status: UNCATEGORIZED                         │
│       │                                                         │
│       ▼                                                         │
│  🎯 Rule-Based Categorization                                   │
│   ├─ Query: transaction_categorization table                    │
│   ├─ Match: normalized_description → category_id                │
│   ├─ Update: category_id + status = CATEGORIZED                 │
│   └─ 💾 Database Persistence (transaction.update())             │
│       │                                                         │
│       ▼                                                         │
│  📊 Results Summary                                             │
│   ├─ ✅ rule_matched_count                                       │
│   ├─ ❓ unmatched_count                                          │
│   └─ 📋 unmatched_transaction_ids[]                             │
│       │                                                         │
│       ▼                                                         │
│  🔄 Background Job Creation (if unmatched > 0)                  │
│   ├─ JobType: AI_CATEGORIZATION                                │
│   ├─ Data: unmatched_transaction_ids                            │
│   └─ Status: PENDING                                           │
│                                                                 │
│  📤 Response: SyncCategorizationResult                          │
│   ├─ immediate_results: rule-based matches                     │
│   ├─ background_job_info: job_id + estimated_time              │
│   └─ statistics: processed/matched/unmatched counts            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Step 3: Immediate Response

```json
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
```

---

## Phase 2: Asynchronous Processing (Background)

### Background Job Processor Architecture

```
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
```

### AI Categorization Detail

```
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
```

---

## Key Components & Responsibilities

### 1. StatementAnalyzerService

```
Responsibilities:
├─ File format detection
├─ Schema analysis (heuristic + LLM)
├─ Transaction parsing
└─ Data validation
```

### 2. TransactionProcessingOrchestrator

```
Responsibilities:
├─ Transaction normalization
├─ Rule-based categorization (sync)
├─ Database persistence
├─ Background job creation
└─ Response formatting
```

### 3. RuleBasedCategorizationService

```
Responsibilities:
├─ Query transaction_categorization table
├─ Batch categorization matching
├─ Normalized description lookup
└─ Category mapping
```

### 4. JobProcessor

```
Responsibilities:
├─ Atomic job claiming
├─ AI categorization coordination
├─ Session management (ID-based)
├─ Progress tracking
├─ Rule creation
└─ Error handling
```

### 5. LLMTransactionCategorizer

```
Responsibilities:
├─ AI-powered categorization
├─ Prompt engineering
├─ Category selection
├─ Confidence scoring
└─ Error handling
```

---

## Database Schema Integration

### Transaction Flow

```sql
-- Initial state after parsing
INSERT INTO transactions (
  description, 
  normalized_description, 
  categorization_status = 'UNCATEGORIZED'
);

-- After rule-based categorization
UPDATE transactions SET 
  category_id = ?, 
  categorization_status = 'CATEGORIZED'
WHERE normalized_description IN (
  SELECT normalized_description 
  FROM transaction_categorization
);

-- After AI categorization
UPDATE transactions SET 
  category_id = ?, 
  categorization_confidence = ?,
  categorization_status = 'CATEGORIZED'
WHERE id = ?;

-- Rule creation from AI results
INSERT INTO transaction_categorization (
  normalized_description,
  category_id,
  source = 'AI',
  created_at = NOW()
);
```

### Background Jobs Tracking

```sql
-- Job creation
INSERT INTO background_jobs (
  job_type = 'AI_CATEGORIZATION',
  status = 'PENDING',
  progress = '{"unmatched_transaction_ids": [...]}'
);

-- Job processing
UPDATE background_jobs SET 
  status = 'IN_PROGRESS',
  started_at = NOW()
WHERE id = ? AND status = 'PENDING';

-- Job completion
UPDATE background_jobs SET 
  status = 'COMPLETED',
  completed_at = NOW(),
  result = '{"processed": 4, "successful": 3, "failed": 1}'
WHERE id = ?;
```

---

## Performance Characteristics

### Cost Optimization Over Time

```
Upload Scenario          | Rule Matches | AI Calls | Cost Impact
-------------------------|--------------|----------|-------------
First upload (cold)      | 0%          | 100%     | $$ Full cost
After 5 uploads          | 60%         | 40%      | $$ 40% cost
After 20 uploads         | 85%         | 15%      | $$ 15% cost
Mature system (100+)     | 95%         | 5%       | $$ 5% cost
```

### Response Time Targets

```
Phase                    | Target Time  | Actual Performance
-------------------------|--------------|-------------------
File upload & parsing    | < 200ms     | ~150ms
Rule-based categorization| < 300ms     | ~245ms
Total sync response      | < 500ms     | ~395ms
AI categorization/tx     | < 2000ms    | ~1500ms
Background job complete  | < 5min      | ~2-3min (100 tx)
```

---

## Error Handling & Recovery

### Synchronous Phase Errors

```
Error Type                | Handling Strategy
--------------------------|------------------------------------------
File format invalid       | Immediate 400 error + user feedback
Schema detection fails    | Fallback to LLM detector
Parsing errors            | Skip invalid rows + warning
Database connection       | 500 error + retry suggestion
Rule query timeout        | Continue without rules + warning
```

### Asynchronous Phase Errors

```
Error Type                | Handling Strategy
--------------------------|------------------------------------------
LLM API timeout           | Retry with exponential backoff
LLM API rate limit        | Queue for retry with delay
Transaction not found     | Log warning + skip (data consistency)
Database deadlock         | Retry transaction
Rule creation conflict    | Log warning + continue (duplicate key)
Job processor crash       | Job remains IN_PROGRESS + manual reset
```

---

## Monitoring & Operations

### Key Metrics to Track

```
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
```

### Operational Scripts

```bash
# Monitor system health
python check_jobs_status.py

# Reset stuck jobs
python reset_stuck_jobs.py

# Check rule effectiveness
python check_categorization_rules.py
```

---

## Testing Strategy

### Unit Tests

- ✅ Transaction parsing and normalization
- ✅ Rule-based categorization logic
- ✅ Background job processor (ID-based architecture)
- ✅ LLM categorizer with mocked AI responses
- ✅ Error handling and edge cases

### Integration Tests

- ✅ End-to-end upload flow
- ✅ Database persistence verification
- ✅ Background job lifecycle
- ✅ Rule creation and application

### Performance Tests

- 📋 Large file upload (1000+ transactions)
- 📋 Concurrent upload handling
- 📋 Background job throughput
- 📋 Database performance under load

---

This architecture provides a robust, scalable, and cost-effective solution for transaction categorization that improves over time through machine learning and rule accumulation. 