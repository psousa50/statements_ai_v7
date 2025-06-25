# TransactionEnhancement Component

## Purpose

The `TransactionEnhancement` component is responsible for applying a set of predefined enhancement rules to a list of transactions. This component is **pure**, stateless, and does not interact with any storage or external systems.

It receives:
- A list of transactions (typically not yet enhanced)
- A list of rules that define how enhancements should be applied

And returns:
- A list of enhanced transactions, with applied fields such as `category_id`, `counterparty_account_id`, or others.

This component performs **rule matching and enhancement logic only**. It does not fetch rules, persist transactions, or manage execution order. These responsibilities belong to the `TransactionEnhancementOrchestrator`.

---

## Rule Matching Logic

Each enhancement rule includes:
- A `normalized_description_pattern` (string)
- A `match_type`: one of `exact`, `prefix`, or `infix`
- Optional `min_amount` and `max_amount`
- Optional date range (`start_date`, `end_date`)
- Enhancement fields such as `category_id`, `counterparty_account_id`

### Match Types
Rules are matched in the following **precedence order**:

1. `exact`: description must exactly match the rule pattern
2. `prefix`: transaction description must start with the rule pattern (e.g., `MBWAY*`)
3. `infix`: description must contain the rule pattern (e.g., `*MERCADO*`)

Matching stops at the **first rule that applies**, according to this order.

---

## Responsibilities

- Apply enhancements to transactions based on matching rules
- Respect rule matching precedence
- Apply only the first matching rule per transaction
- Leave transactions unchanged if no rules match

---

## Interface (Conceptual)

```python
class TransactionEnhancer:
    def apply_rules(
        self, 
        transactions: List[Transaction], 
        rules: List[EnhancementRule]
    ) -> List[EnhancedTransaction]:
```

## Tests

Add unit tests to verify the component's functionality

