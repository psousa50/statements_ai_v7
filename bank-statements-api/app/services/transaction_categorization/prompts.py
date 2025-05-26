import json
from dataclasses import dataclass
from typing import List

from app.domain.models.category import Category
from app.domain.models.transaction import Transaction


@dataclass
class Subcategory:
    sub_category_id: str  # Changed to str to handle UUIDs
    subcategory_name: str


def categorization_prompt(transactions: List[Transaction], categories: List[Category]) -> str:
    # Convert categories to the format expected by the LLM
    # For now, we'll treat all categories as potential subcategories
    expanded_categories = [Subcategory(str(cat.id), cat.name) for cat in categories]  # Convert UUID to string

    categories_info = [f"{{id: {cat.sub_category_id}, name: {cat.subcategory_name}}}" for cat in expanded_categories]

    transaction_descriptions = [t.description for t in transactions]

    prompt = f"""
You are a bank transaction categorization assistant. Your task is to categorize the following transaction description into one of the provided categories.

Transactions: 
{'\n'.join(transaction_descriptions)}

Available Categories:
{json.dumps(categories_info, indent=2)}

Analyze the transaction description and determine the most appropriate category ID from the list above.
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
