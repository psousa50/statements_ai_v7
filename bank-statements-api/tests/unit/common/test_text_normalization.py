"""
Unit tests for text normalization utilities.
"""

from app.common.text_normalization import normalize_description


class TestTextNormalization:
    """Test cases for text normalization functions."""

    def test_normalize_description_empty_input(self):
        """Test normalization with empty input."""
        assert normalize_description("") == ""
        assert normalize_description(None) == ""

    def test_normalize_description_lowercase(self):
        """Test conversion to lowercase."""
        assert normalize_description("PAYMENT") == "payment"
        assert normalize_description("Payment") == "payment"

    def test_normalize_description_remove_accents(self):
        """Test removal of accents/diacritics."""
        assert normalize_description("café") == "cafe"
        assert normalize_description("résumé") == "resume"

    def test_normalize_description_remove_prefixes(self):
        """Test removal of common transaction prefixes."""
        assert normalize_description("Payment to ACME Corp") == "payment acme corp"
        assert normalize_description("Transfer from John Doe") == "transfer john doe"
        assert normalize_description("POS Purchase at WALMART") == "pos purchase walmart"

    def test_normalize_description_remove_numbers_and_special_chars(
        self,
    ):
        """Test removal of numbers and special characters."""
        assert normalize_description("ACME Corp #12345") == "acme corp"
        assert normalize_description("Payment $123.45") == "payment"
        assert normalize_description("Transaction ID: ABC-123") == "transaction"

    def test_normalize_description_remove_dates(self):
        """Test removal of dates."""
        assert normalize_description("ACME Corp 01/02/2023") == "acme corp"
        assert normalize_description("Payment date: 2023-05-28") == "payment"

    def test_normalize_description_remove_reference_numbers(
        self,
    ):
        """Test removal of reference numbers."""
        assert normalize_description("ACME Corp REF123456") == "acme corp"
        assert normalize_description("Payment reference: 987654") == "payment"

    def test_normalize_description_comprehensive(self):
        """Test comprehensive normalization with multiple features."""
        input_text = "Payment to CAFÉ NOIR #12345 - REF:67890 on 01/02/2023"
        expected = "payment cafe noir"
        assert normalize_description(input_text) == expected
