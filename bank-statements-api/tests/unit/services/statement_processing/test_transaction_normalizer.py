import pandas as pd
import pytest

from app.services.statement_processing.transaction_normalizer import TransactionNormalizer


class TestTransactionNormalizer:
    def test_normalize_transactions(self):
        normalizer = TransactionNormalizer()

        df = pd.DataFrame(
            {
                "Transaction Date": [
                    "2023-01-01",
                    "2023-01-02",
                ],
                "Value (EUR)": [100.00, -200.00],
                "Transaction Details": [
                    "Deposit",
                    "Withdrawal",
                ],
            }
        )

        column_mapping = {
            "date": "Transaction Date",
            "amount": "Value (EUR)",
            "description": "Transaction Details",
        }

        normalized_df = normalizer.normalize(df, column_mapping)

        assert list(normalized_df.columns) == [
            "date",
            "amount",
            "description",
        ]
        assert len(normalized_df) == 2
        # Date is now a string for JSON serialization
        assert normalized_df["date"][0] == "2023-01-01"
        assert normalized_df["amount"][0] == 100.00
        assert normalized_df["amount"][1] == -200.00
        assert normalized_df["description"][0] == "Deposit"

    def test_normalize_with_date_format(self):
        normalizer = TransactionNormalizer()

        df = pd.DataFrame(
            {
                "Data": ["01/02/2023", "02/02/2023"],
                "Valor": ["1.000,50", "-2.000,75"],
                "Descrição": ["Depósito", "Levantamento"],
            }
        )

        column_mapping = {
            "date": "Data",
            "amount": "Valor",
            "description": "Descrição",
        }

        normalized_df = normalizer.normalize(df, column_mapping)

        assert list(normalized_df.columns) == [
            "date",
            "amount",
            "description",
        ]
        assert len(normalized_df) == 2
        # Date is now a string for JSON serialization
        assert normalized_df["date"][0] == "2023-01-02"
        assert normalized_df["amount"][0] == 1000.50
        assert normalized_df["amount"][1] == -2000.75

    def test_normalize_with_missing_columns(self):
        normalizer = TransactionNormalizer()

        df = pd.DataFrame(
            {
                "Date": ["2023-01-01", "2023-01-02"],
                "Other": ["A", "B"],
            }
        )

        column_mapping = {
            "date": "Date",
            "amount": "Amount",
            "description": "Description",
        }

        with pytest.raises(
            ValueError,
            match="Not enough columns in DataFrame for positional mapping. Missing: Amount, Description",
        ):
            normalizer.normalize(df, column_mapping)
