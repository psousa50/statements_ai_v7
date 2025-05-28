# Common Utilities

This directory contains common utility functions used across the application.

## Text Normalization

The `text_normalization.py` module provides utilities for normalizing text, particularly transaction descriptions.

### `normalize_description(description: str) -> str`

This function normalizes transaction descriptions to improve matching and categorization accuracy. It performs the following operations:

1. Converts text to lowercase
2. Removes accents/diacritics
3. Removes special characters and extra whitespace
4. Removes common transaction prefixes/suffixes
5. Removes numbers, dates, and reference IDs

Example usage:

```python
from app.common.text_normalization import normalize_description

original_description = "Payment to CAFÉ NOIR #12345 - REF:67890 on 01/02/2023"
normalized = normalize_description(original_description)  # Returns "cafe noir"
```

This normalized description is stored in the database alongside the original description and is used for more efficient and consistent matching during categorization.

**Note**: The normalized_description field is mandatory for all transactions and is automatically generated from the original description.
