"""
Utility functions for text normalization.
Used for normalizing transaction descriptions to improve matching and categorization.
"""

import re
import unicodedata


def normalize_description(description: str) -> str:
    """
    Normalize a transaction description for consistent matching.

    This function:
    1. Converts to lowercase
    2. Removes accents/diacritics
    3. Removes special characters and extra whitespace
    4. Removes common transaction prefixes/suffixes
    5. Removes numbers and dates

    Args:
        description: The original transaction description

    Returns:
        Normalized description string
    """
    if not description:
        return ""

    # Convert to lowercase
    text = description.lower()

    # Remove accents/diacritics
    text = unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode("utf-8")

    # Remove reference numbers, dates, and transaction IDs
    # This pattern matches common formats like REF123456, #123456, 01/02/2023
    text = re.sub(r"\b(ref|reference|#|id|date)\b[:\s]*[\w\d\-\/\.]+", "", text, flags=re.IGNORECASE)

    # Remove common date patterns
    text = re.sub(r"\b\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b", "", text)
    text = re.sub(r"\bon\s+\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b", "", text)

    # Remove all digits and special characters, keeping only letters and spaces
    text = re.sub(r"[^a-z\s]", "", text)

    # Remove common words that aren't meaningful for categorization
    words_to_remove = ["id", "ref", "on", "at", "to", "from", "the", "and", "for"]
    for word in words_to_remove:
        text = re.sub(r"\b" + word + r"\b", "", text)

    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text
