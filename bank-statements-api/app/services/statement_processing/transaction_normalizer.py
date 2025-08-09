import logging
import re

import numpy as np
import pandas as pd

logger_content = logging.getLogger("app.llm.big")
logger = logging.getLogger("app")


class TransactionNormalizer:
    def normalize(self, df: pd.DataFrame, column_mapping: dict) -> pd.DataFrame:
        result_df = pd.DataFrame()

        has_amount = "amount" in column_mapping and column_mapping["amount"]
        has_debit_credit = (
            "debit_amount" in column_mapping
            and column_mapping["debit_amount"]
            and "credit_amount" in column_mapping
            and column_mapping["credit_amount"]
        )

        if has_amount:
            required_keys = [
                "date",
                "amount",
                "description",
            ]
        elif has_debit_credit:
            required_keys = [
                "date",
                "debit_amount",
                "credit_amount",
                "description",
            ]
        else:
            raise ValueError("No valid amount fields found")

        missing_keys = [key for key in required_keys if key not in column_mapping]
        if missing_keys:
            raise ValueError(f"Missing required keys in column mapping: {', '.join(missing_keys)}")

        date_col = column_mapping["date"]
        description_col = column_mapping["description"]

        if has_amount:
            amount_col = column_mapping["amount"]
        elif has_debit_credit:
            debit_col = column_mapping["debit_amount"]
            credit_col = column_mapping["credit_amount"]
        else:
            amount_col = column_mapping.get("amount", "")

        empty_columns = []
        for col_name, mapped_col in column_mapping.items():
            if col_name in required_keys and (not mapped_col or mapped_col.strip() == ""):
                empty_columns.append(col_name)

        if empty_columns:
            raise ValueError(f"Empty column mappings for: {', '.join(empty_columns)}")

        missing_df_columns = []
        for key in required_keys:
            col_name = column_mapping[key]
            if col_name not in df.columns:
                missing_df_columns.append(col_name)

        if missing_df_columns:
            raise ValueError(
                f"Not enough columns in DataFrame for positional mapping. Missing: {', '.join(missing_df_columns)}"
            )

        result_df["date"] = self._normalize_dates(df[date_col])

        if has_amount:
            result_df["amount"] = self._normalize_amounts(df[amount_col])
        else:
            debit_amounts = self._normalize_amounts(df[debit_col])
            credit_amounts = self._normalize_amounts(df[credit_col])

            debit_amounts = debit_amounts.fillna(0)
            credit_amounts = credit_amounts.fillna(0)

            # Debit amounts are negative (money going out), credit amounts are positive (money coming in)
            # Combine them into a single amount column
            result_df["amount"] = credit_amounts - debit_amounts

        descriptions = df[description_col]
        result_df["description"] = descriptions.fillna("").astype(str)

        if "date" in result_df.columns:
            result_df["date"] = result_df["date"].apply(
                lambda x: x.strftime("%Y-%m-%d") if pd.notna(x) and hasattr(x, "strftime") else x
            )

        return result_df

    def _normalize_dates(self, date_series: pd.Series) -> pd.Series:
        # First try with dayfirst=True (European format: DD/MM/YYYY)
        normalized = pd.to_datetime(
            date_series,
            errors="coerce",
            dayfirst=True,
            utc=False,
        )

        # If many dates failed to parse, try with American format (MM/DD/YYYY)
        if normalized.isna().sum() > len(normalized) * 0.5:
            logger.info("Many dates failed with European format, trying American format")
            normalized = pd.to_datetime(
                date_series,
                errors="coerce",
                dayfirst=False,
                utc=False,
            )

        return normalized

    def _normalize_amounts(self, amount_series: pd.Series) -> pd.Series:
        def clean_value(val):
            if pd.isna(val):
                return np.nan

            if isinstance(val, (int, float)):
                return float(val)

            val_str = str(val).strip()

            val_str = re.sub(r"[^\d,.\-eE]", "", val_str)

            if "," in val_str and "." in val_str:
                if val_str.rfind(",") > val_str.rfind("."):
                    val_str = val_str.replace(".", "").replace(",", ".")
                else:
                    val_str = val_str.replace(",", "")
            elif "," in val_str and "." not in val_str:
                val_str = val_str.replace(",", ".")

            try:
                return float(val_str)
            except ValueError:
                return np.nan

        return amount_series.apply(clean_value)
