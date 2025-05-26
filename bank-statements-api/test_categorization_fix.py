#!/usr/bin/env python3
"""
Quick test script to verify the categorization fix works
"""
import os
import sys
from uuid import UUID

sys.path.append(os.path.join(os.path.dirname(__file__), "app"))

from app.services.transaction_categorization.llm_transaction_categorizer import LLMCategorizationResult
from app.services.transaction_categorization.prompts import categorization_prompt


# Mock the necessary objects
class MockCategory:
    def __init__(self, id_val, name):
        self.id = id_val
        self.name = name


class MockTransaction:
    def __init__(self, id_val, description):
        self.id = id_val
        self.description = description


# Test the prompt generation


def test_prompt_generation():
    print("Testing prompt generation...")

    # Create some mock categories with UUIDs
    categories = [
        MockCategory(UUID("8a28a030-3c78-432e-a0db-9c3d8fb73449"), "Food & Dining"),
        MockCategory(UUID("b1234567-89ab-cdef-0123-456789abcdef"), "Transportation"),
        MockCategory(UUID("c2345678-9abc-def0-1234-56789abcdef0"), "Shopping"),
    ]

    # Create some mock transactions
    transactions = [
        MockTransaction(UUID("f1234567-89ab-cdef-0123-456789abcdef"), "McDonald's Restaurant"),
        MockTransaction(UUID("f2345678-9abc-def0-1234-56789abcdef0"), "Uber Ride"),
    ]

    try:
        prompt = categorization_prompt(transactions, categories)
        print("✅ Prompt generation successful!")
        print("Sample prompt output:")
        print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
        return True
    except Exception as e:
        print(f"❌ Prompt generation failed: {e}")
        return False


# Test the LLM result parsing


def test_llm_result_parsing():
    print("\nTesting LLM result parsing...")

    try:
        # Test with UUID string
        result = LLMCategorizationResult(
            transaction_description="McDonald's Restaurant", sub_category_id="8a28a030-3c78-432e-a0db-9c3d8fb73449", confidence=0.95
        )
        print("✅ LLM result parsing with UUID successful!")
        print(f"Result: {result}")
        return True
    except Exception as e:
        print(f"❌ LLM result parsing failed: {e}")
        return False


if __name__ == "__main__":
    print("Testing categorization fixes...")

    success1 = test_prompt_generation()
    success2 = test_llm_result_parsing()

    if success1 and success2:
        print("\n🎉 All tests passed! The categorization fix should work.")
    else:
        print("\n❌ Some tests failed. Check the errors above.")
