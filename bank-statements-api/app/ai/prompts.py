import json
from dataclasses import dataclass
from typing import List

import pandas as pd

from app.domain.models.account import Account
from app.domain.models.category import Category
from app.domain.models.transaction import Transaction


@dataclass
class Subcategory:
    sub_category_id: str
    subcategory_name: str


def categorization_prompt(
    transactions: List[Transaction],
    categories: List[Category],
) -> str:
    # Provide subcategories (leaf nodes) for more specific categorization
    # Include both subcategories and root categories that don't have subcategories
    root_categories_with_children = {cat.parent_id for cat in categories if cat.parent_id is not None}

    expanded_categories = [
        Subcategory(str(cat.id), cat.name)
        for cat in categories
        if cat.parent_id is not None or cat.id not in root_categories_with_children
    ]

    categories_info = [f"{{id: {cat.sub_category_id}, name: {cat.subcategory_name}}}" for cat in expanded_categories]

    transaction_descriptions = [t.description for t in transactions]

    prompt = f"""
You are a bank transaction categorization assistant. Your task is to categorize the following transaction descriptions into the most specific and appropriate categories from the provided list.

Transactions: 
{"\n".join(transaction_descriptions)}

Available Categories:
{json.dumps(categories_info, indent=2)}

For each transaction, analyze the description and determine the most specific and appropriate category ID from the list above.
Choose the category that best matches the nature of the transaction.

Return your answer as a JSON object with the following format:
[
    {{
        "transaction_description": <description of the transaction>,
        "sub_category_id": <id of the selected subcategory>,
        "confidence": <a number between 0 and 1 indicating your confidence in this categorization>
    }},
    {{
        "transaction_description": <description of the transaction>,
        "sub_category_id": <id of the selected subcategory>,
        "confidence": <a number between 0 and 1 indicating your confidence in this categorization>
    }}
]

Only return the JSON object, nothing else.
"""
    return prompt


def schema_detection_prompt(df: pd.DataFrame) -> str:
    return f"""
From this bank statement excerpt, extract the column map and header information in the following format:

{{
  "column_mapping": {{
    "date": "<column name for date>",
    "description": "<column name for description>",
    "amount": "<column name for amount>",
    "debit_amount": "<column name for debit amount>",
    "credit_amount": "<column name for credit amount>",
    "currency": "<column name for currency>",
    "balance": "<column name for balance>"
  }},
  "header_row_index": <0-based index of the header row>,
  "data_start_row_index": <0-based index of the first row of actual transaction data>
}}

Guidelines:
	•	Only use actual column names from the transaction table header row (not metadata or sample values).
	•	If a field is missing (e.g. no currency column), set its value to an empty string: "".
	•	header_row_index is the 0-based index of the row where the column headers (like "Date", "Description", etc.) appear.
	•	data_start_row_index is the 0-based index of the first row after the header that contains actual transaction data.
	•	Do not guess or generate column names—only use what's present in the header row.
	•	Only output valid JSON matching the format above. No explanations. No extra text.
	•	Transaction rows contain actual dates and amounts; ignore rows that have empty fields, labels, or static information.

Example:
---------------------------------------------------------
Account Statement,,,,,
Currency: EUR,,,,,
Date Range: 2023-01-01 to 2023-01-31,,,,,

Transaction Date,Value Date,Details,Amount,Balance
2023-01-01,2023-01-01,Coffee Shop,-3.50,996.50
2023-01-02,2023-01-02,Grocery Store,-25.00,971.50

---------------------------------------------------------

{{
  "column_mapping": {{
    "date": "Transaction Date",
    "description": "Details",
    "amount": "Amount",
    "debit_amount": "",
    "credit_amount": "",
    "currency": "",
    "balance": "Balance"
  }},
  "header_row_index": 4,
  "data_start_row_index": 5
}}


---------------------------------------------------------
{df.iloc[:10].to_csv(index=False)}
---------------------------------------------------------
"""


def counterparty_identification_prompt(transactions: List[Transaction], accounts: List[Account]) -> str:
    """Create a prompt for LLM to identify counterparty accounts for transactions"""

    accounts_info = [f"{{id: {account.id}, name: {account.name}}}" for account in accounts]

    transaction_data = []
    for t in transactions:
        transaction_data.append(
            {
                "description": t.description,
                "amount": str(t.amount),
            }
        )

    prompt = f"""
You are a bank transaction counterparty identification assistant. Your task is to identify the most likely counterparty account for each transaction based on the transaction description and amount.

Transactions: 
{json.dumps(transaction_data, indent=2)}

Available Counterparty Accounts:
{json.dumps(accounts_info, indent=2)}

For each transaction, analyze the description and amount to determine which counterparty account is most likely involved in this transaction.

Consider:
- Transaction descriptions that might indicate transfers between accounts
- Positive amounts typically indicate money coming FROM the counterparty account TO the current account
- Negative amounts typically indicate money going FROM the current account TO the counterparty account
- Account names that might match or relate to the transaction description
- Common patterns in inter-account transfers

Return your answer as a JSON object with the following format:
[
    {{
        "transaction_description": <description of the transaction>,
        "counterparty_account_id": <id of the identified counterparty account, or null if no clear counterparty>,
        "confidence": <a number between 0 and 1 indicating your confidence in this identification>
    }},
    {{
        "transaction_description": <description of the transaction>,
        "counterparty_account_id": <id of the identified counterparty account, or null if no clear counterparty>,
        "confidence": <a number between 0 and 1 indicating your confidence in this identification>
    }}
]

Only return the JSON object, nothing else.
"""
    return prompt
