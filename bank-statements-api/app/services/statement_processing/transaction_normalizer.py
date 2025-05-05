import re
from datetime import datetime

import pandas as pd


class TransactionNormalizer:
    def normalize(self, df: pd.DataFrame, column_mapping: dict) -> pd.DataFrame:
        for standard_col, mapped_col in column_mapping.items():
            if mapped_col not in df.columns:
                raise ValueError("Missing mapped columns in DataFrame")

        result_df = pd.DataFrame()

        date_col = column_mapping["date"]
        amount_col = column_mapping["amount"]
        description_col = column_mapping["description"]

        result_df["date"] = self._normalize_dates(df[date_col])
        result_df["amount"] = self._normalize_amounts(df[amount_col])
        result_df["description"] = df[description_col]

        # Convert pandas Timestamp objects to string format for JSON serialization
        if "date" in result_df.columns:
            result_df["date"] = result_df["date"].apply(lambda x: x.strftime("%Y-%m-%d") if hasattr(x, "strftime") else x)

        return result_df

    def _normalize_dates(self, date_series):
        normalized_dates = []

        for date_str in date_series:
            try:
                date_formats = ["%d/%m/%Y", "%Y-%m-%d", "%m/%d/%Y"]
                for fmt in date_formats:
                    try:
                        date_obj = datetime.strptime(date_str, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    try:
                        date_obj = pd.to_datetime(date_str)
                    except ValueError:
                        date_obj = None
            except ValueError:
                date_obj = None

            normalized_dates.append(date_obj)

        return normalized_dates

    def _normalize_amounts(self, amount_series):
        normalized_amounts = []

        for amount_val in amount_series:
            if isinstance(amount_val, (int, float)):
                normalized_amounts.append(float(amount_val))
                continue

            amount_str = str(amount_val)

            if "," in amount_str and "." in amount_str:
                if amount_str.find(",") > amount_str.find("."):
                    amount_str = amount_str.replace(".", "").replace(",", ".")
                else:
                    amount_str = amount_str.replace(",", "")
            elif "," in amount_str:
                amount_str = amount_str.replace(",", ".")

            amount_str = re.sub(r"[^\d.-]", "", amount_str)

            try:
                amount = float(amount_str)
                normalized_amounts.append(amount)
            except ValueError:
                normalized_amounts.append(None)

        return normalized_amounts
