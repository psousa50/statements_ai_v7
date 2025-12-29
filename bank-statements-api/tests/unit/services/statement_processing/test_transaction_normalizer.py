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

        normalized_df, dropped_rows = normalizer.normalize(df, column_mapping)

        assert list(normalized_df.columns) == [
            "date",
            "amount",
            "description",
        ]
        assert len(normalized_df) == 2
        assert len(dropped_rows) == 0
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

        normalized_df, dropped_rows = normalizer.normalize(df, column_mapping)

        assert list(normalized_df.columns) == [
            "date",
            "amount",
            "description",
        ]
        assert len(normalized_df) == 2
        assert len(dropped_rows) == 0
        assert normalized_df["date"][0] == "2023-02-01"
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

    def test_normalize_drops_rows_with_invalid_dates(self):
        normalizer = TransactionNormalizer()

        df = pd.DataFrame(
            {
                "Date": ["2023-01-15", "invalid-date", None, "2023-02-20"],
                "Amount": [100.00, 200.00, 300.00, 400.00],
                "Description": ["Valid 1", "Invalid date", "Null date", "Valid 2"],
            }
        )

        column_mapping = {
            "date": "Date",
            "amount": "Amount",
            "description": "Description",
        }

        normalized_df, dropped_rows = normalizer.normalize(df, column_mapping, data_start_row_index=1)

        assert len(normalized_df) == 2
        assert normalized_df["date"].iloc[0] == "2023-01-15"
        assert normalized_df["date"].iloc[1] == "2023-02-20"
        assert normalized_df["description"].iloc[0] == "Valid 1"
        assert normalized_df["description"].iloc[1] == "Valid 2"

        assert len(dropped_rows) == 2
        assert dropped_rows[0].file_row_number == 3
        assert dropped_rows[0].date_value == "invalid-date"
        assert dropped_rows[0].description == "Invalid date"
        assert dropped_rows[0].reason == "invalid_date"
        assert dropped_rows[1].file_row_number == 4
        assert dropped_rows[1].description == "Null date"

    def test_normalize_drops_rows_with_invalid_amounts(self):
        normalizer = TransactionNormalizer()

        df = pd.DataFrame(
            {
                "Date": ["2023-01-15", "2023-01-16", "2023-01-17", "2023-01-18"],
                "Amount": ["100.00", "-49.9a9", "abc", "400.00"],
                "Description": ["Valid", "Invalid amount with letter", "Completely invalid", "Valid 2"],
            }
        )

        column_mapping = {
            "date": "Date",
            "amount": "Amount",
            "description": "Description",
        }

        normalized_df, dropped_rows = normalizer.normalize(df, column_mapping, data_start_row_index=1)

        assert len(normalized_df) == 2
        assert normalized_df["amount"].iloc[0] == 100.00
        assert normalized_df["amount"].iloc[1] == 400.00
        assert normalized_df["description"].iloc[0] == "Valid"
        assert normalized_df["description"].iloc[1] == "Valid 2"

        assert len(dropped_rows) == 2
        assert dropped_rows[0].file_row_number == 3
        assert dropped_rows[0].amount == "-49.9a9"
        assert dropped_rows[0].reason == "invalid_amount"
        assert dropped_rows[1].file_row_number == 4
        assert dropped_rows[1].amount == "abc"
        assert dropped_rows[1].reason == "invalid_amount"

    def test_normalize_drops_rows_with_both_invalid_dates_and_amounts(self):
        normalizer = TransactionNormalizer()

        df = pd.DataFrame(
            {
                "Date": ["2023-01-15", "invalid-date", "2023-01-17", "2023-01-18"],
                "Amount": ["100.00", "200.00", "-49.9a9", "400.00"],
                "Description": ["Valid", "Bad date", "Bad amount", "Valid 2"],
            }
        )

        column_mapping = {
            "date": "Date",
            "amount": "Amount",
            "description": "Description",
        }

        normalized_df, dropped_rows = normalizer.normalize(df, column_mapping, data_start_row_index=1)

        assert len(normalized_df) == 2
        assert len(dropped_rows) == 2

        date_drops = [r for r in dropped_rows if r.reason == "invalid_date"]
        amount_drops = [r for r in dropped_rows if r.reason == "invalid_amount"]

        assert len(date_drops) == 1
        assert len(amount_drops) == 1
        assert date_drops[0].description == "Bad date"
        assert amount_drops[0].description == "Bad amount"
