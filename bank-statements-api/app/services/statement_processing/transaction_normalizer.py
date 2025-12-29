import logging
import re
from typing import Tuple

import numpy as np
import pandas as pd

from app.domain.dto.statement_processing import DroppedRowInfo

logger_content = logging.getLogger("app.llm.big")
logger = logging.getLogger("app")


class TransactionNormalizer:
    def normalize(
        self,
        df: pd.DataFrame,
        column_mapping: dict,
        data_start_row_index: int = 0,
    ) -> Tuple[pd.DataFrame, list[DroppedRowInfo]]:
        result_df = pd.DataFrame()
        dropped_rows: list[DroppedRowInfo] = []

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

        original_dates = df[date_col].copy()
        result_df["date"] = self._normalize_dates(df[date_col])

        if has_amount:
            original_amounts = df[amount_col].copy()
            result_df["amount"], invalid_amount_mask = self._normalize_amounts(df[amount_col])
        else:
            debit_amounts, debit_invalid = self._normalize_amounts(df[debit_col])
            credit_amounts, credit_invalid = self._normalize_amounts(df[credit_col])

            debit_amounts = debit_amounts.fillna(0)
            credit_amounts = credit_amounts.fillna(0)

            result_df["amount"] = credit_amounts - debit_amounts
            original_amounts = df[debit_col].astype(str) + " / " + df[credit_col].astype(str)
            invalid_amount_mask = debit_invalid | credit_invalid

        descriptions = df[description_col]
        result_df["description"] = descriptions.fillna("").astype(str)

        if "date" in result_df.columns:
            result_df["date"] = result_df["date"].apply(
                lambda x: x.strftime("%Y-%m-%d") if pd.notna(x) and hasattr(x, "strftime") else x
            )

            invalid_date_mask = result_df["date"].isna() | result_df["date"].apply(
                lambda x: not isinstance(x, str) or not x.strip()
            )
            invalid_date_count = invalid_date_mask.sum()
            if invalid_date_count > 0:
                logger.warning(f"Dropping {invalid_date_count} rows with invalid/missing dates")

                for idx in result_df[invalid_date_mask].index:
                    file_row = data_start_row_index + idx + 1
                    dropped_rows.append(
                        DroppedRowInfo(
                            file_row_number=file_row,
                            date_value=str(original_dates.iloc[idx]) if pd.notna(original_dates.iloc[idx]) else "",
                            description=result_df.at[idx, "description"],
                            amount=str(original_amounts.iloc[idx]) if pd.notna(original_amounts.iloc[idx]) else "",
                            reason="invalid_date",
                        )
                    )

                result_df = result_df[~invalid_date_mask].reset_index(drop=True)
                invalid_amount_mask = invalid_amount_mask[~invalid_date_mask].reset_index(drop=True)
                original_amounts = original_amounts[~invalid_date_mask].reset_index(drop=True)
                original_dates = original_dates[~invalid_date_mask].reset_index(drop=True)

        invalid_amount_count = invalid_amount_mask.sum()
        if invalid_amount_count > 0:
            logger.warning(f"Dropping {invalid_amount_count} rows with invalid amounts")

            for idx in result_df[invalid_amount_mask].index:
                file_row = data_start_row_index + idx + 1
                dropped_rows.append(
                    DroppedRowInfo(
                        file_row_number=file_row,
                        date_value=str(original_dates.iloc[idx]) if pd.notna(original_dates.iloc[idx]) else "",
                        description=result_df.at[idx, "description"],
                        amount=str(original_amounts.iloc[idx]) if pd.notna(original_amounts.iloc[idx]) else "",
                        reason="invalid_amount",
                    )
                )

            result_df = result_df[~invalid_amount_mask].reset_index(drop=True)

        return result_df, dropped_rows

    def _normalize_dates(self, date_series: pd.Series) -> pd.Series:
        first_valid = date_series.dropna().iloc[0] if not date_series.dropna().empty else None
        is_iso_format = (
            first_valid is not None
            and isinstance(first_valid, str)
            and len(first_valid) >= 10
            and first_valid[4] == "-"
            and first_valid[7] == "-"
        )

        if is_iso_format:
            return pd.to_datetime(date_series, errors="coerce", utc=False)

        normalized = pd.to_datetime(date_series, errors="coerce", dayfirst=True, utc=False)

        if normalized.isna().sum() > len(normalized) * 0.5:
            logger.info("Many dates failed with European format, trying American format")
            normalized = pd.to_datetime(date_series, errors="coerce", dayfirst=False, utc=False)

        return normalized

    def _normalize_amounts(self, amount_series: pd.Series) -> Tuple[pd.Series, pd.Series]:
        invalid_mask = pd.Series([False] * len(amount_series), index=amount_series.index)

        def clean_value(idx, val):
            if pd.isna(val):
                return np.nan

            if isinstance(val, (int, float)):
                return float(val)

            val_str = str(val).strip()

            if re.search(r"[^\d,.\-eE\s$€£¥₹%()]", val_str):
                invalid_mask.iloc[idx] = True
                return np.nan

            cleaned = re.sub(r"[^\d,.\-eE]", "", val_str)

            if "," in cleaned and "." in cleaned:
                if cleaned.rfind(",") > cleaned.rfind("."):
                    cleaned = cleaned.replace(".", "").replace(",", ".")
                else:
                    cleaned = cleaned.replace(",", "")
            elif "," in cleaned and "." not in cleaned:
                cleaned = cleaned.replace(",", ".")

            try:
                return float(cleaned)
            except ValueError:
                invalid_mask.iloc[idx] = True
                return np.nan

        result = pd.Series([clean_value(i, v) for i, v in enumerate(amount_series)], index=amount_series.index)
        return result, invalid_mask
