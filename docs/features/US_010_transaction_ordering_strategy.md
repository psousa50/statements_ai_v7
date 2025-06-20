
# Transaction Ordering Strategy for Bank Statements

This document outlines how to ensure correct transaction ordering in the database, including mixed scenarios where transactions are both **uploaded from files** and **manually entered** by the user.

---

## ✅ Problem

- Many bank statements contain only **dates** (no times).
- Within a date, transaction **order matters** (based on how they appear in the statement).
- Users may **manually enter** or adjust transactions later.
- We must **preserve visual/logical order** and allow edits while keeping consistency.

---

## 💡 Solution Overview

### 1. Preserve Original File Order

When a file is uploaded:

- Each transaction is assigned a `row_index` (based on its order in the file).
- All transactions reference the `statement_file_id`.

This allows consistent reordering based on the original file even when times are missing.

```sql
SELECT * FROM transactions
WHERE statement_file_id = :id
ORDER BY transaction_date, row_index;
```

---

### 2. Use a Sort Index for Mixed Entry Sources

Introduce a `sort_index` column:

- Used for **ordering transactions within a day**
- Applies to both uploaded and manually entered transactions

#### Fields:
| Field                   | Type       | Description |
|------------------------|------------|-------------|
| `sort_index`           | INTEGER    | Defines relative order of transactions on the same day |
| `source_type`          | TEXT       | `'upload'` or `'manual'` |
| `manual_position_after`| UUID (opt) | Reference to another transaction to help with drag-and-drop ordering |
| `statement_file_id`    | UUID       | Points to source file if uploaded |

---

### 3. Assigning Sort Index

#### Uploaded Entries:
- `sort_index` = same as `row_index`

#### Manual Entries:
- Assign `sort_index` = highest `sort_index` + 1 for that date/account
- Or insert with gap strategy (e.g., 10, 20, 30) to allow in-between inserts

```sql
SELECT MAX(sort_index) FROM transactions
WHERE bank_account_id = :account_id AND transaction_date = :date;
```

---

### 4. Query Strategy

To retrieve transactions in visual order:

```sql
SELECT * FROM transactions
WHERE bank_account_id = :account_id
ORDER BY transaction_date, sort_index;
```

---

## 🧠 Optional UI Support

- Allow drag-and-drop reordering in the frontend
- Update `sort_index` in the backend accordingly
- `manual_position_after` can be used to express relative movement

---

## 🗃 Example Schema Snippet

```sql
CREATE TABLE transactions (
    id UUID PRIMARY KEY,
    bank_account_id UUID,
    statement_file_id UUID,
    transaction_date DATE NOT NULL,
    transaction_time TIME, -- nullable
    description TEXT,
    amount NUMERIC,
    row_index INTEGER, -- used for uploads
    sort_index INTEGER NOT NULL,
    source_type TEXT CHECK (source_type IN ('upload', 'manual')),
    manual_position_after UUID,
    created_at TIMESTAMP DEFAULT now()
);
```

---

## ✅ Summary

This approach:
- Ensures consistent ordering
- Supports both automatic and manual workflows
- Enables flexible and user-friendly interfaces
