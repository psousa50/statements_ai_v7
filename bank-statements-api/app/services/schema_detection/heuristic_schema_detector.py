from collections import Counter
from typing import Dict, Optional

import pandas as pd
from dateutil.parser import parse

from app.services.schema_detection.schema_detector import ConversionModel, SchemaDetectorProtocol


def is_probable_date(val) -> bool:
    if pd.isna(val):
        return False
    if not isinstance(val, str):
        val = str(val)
    try:
        parse(val.strip(), fuzzy=False, dayfirst=True)
        return True
    except Exception:
        return False


def is_probable_amount(val) -> bool:
    if pd.isna(val):
        return False
    if not isinstance(val, str):
        val = str(val)
    try:
        cleaned = val.replace(",", "").replace(".", "", val.count(".") - 1)
        float(cleaned.replace("€", "").replace("$", "").replace("£", "").replace(" ", "").strip())
        return True
    except Exception:
        return False


def is_probable_description(val) -> bool:
    if pd.isna(val):
        return False
    if not isinstance(val, str):
        val = str(val)
    stripped = val.strip()
    return len(stripped) >= 5 and not is_probable_date(stripped) and not is_probable_amount(stripped)


def find_first_valid_streak(series: pd.Series, predicate, streak_length: int = 2) -> Optional[int]:
    values = series.tolist()
    max_index = len(values) - streak_length + 1
    if max_index <= 0:
        return None
    for i in range(max_index):
        window = values[i : i + streak_length]
        if all(predicate(v) for v in window):
            return i
    return None


class HeuristicSchemaDetector(SchemaDetectorProtocol):
    def detect_schema(self, df: pd.DataFrame) -> ConversionModel:
        if df.empty:
            raise ValueError("Cannot detect schema from an empty DataFrame")

        row_count = len(df)

        start_row = self._infer_data_start_row(df) + 1
        start_row = min(start_row, row_count - 1)
        header_row = max(0, start_row - 1)

        if header_row == 0:
            header = df.columns.tolist()
        else:
            header = df.iloc[header_row - 1].astype(str).tolist()

        data_df = df.iloc[start_row:].reset_index(drop=True).copy()
        data_df.columns = header

        column_map = self._infer_standard_columns(data_df)

        return ConversionModel(
            column_map=column_map,
            header_row=header_row,
            start_row=start_row,
        )

    def _infer_data_start_row(self, df: pd.DataFrame) -> int:
        first_data_rows = []

        for col in df.columns:
            col_data = df[col]
            i_date = find_first_valid_streak(col_data, is_probable_date)
            i_amt = find_first_valid_streak(col_data, is_probable_amount)
            i = min([i for i in [i_date, i_amt] if i is not None], default=None)
            if i is not None:
                first_data_rows.append(i)

        if not first_data_rows:
            return 1 if len(df) > 1 else 0  # fallback

        most_common_row, _ = Counter(first_data_rows).most_common(1)[0]
        return most_common_row

    def _infer_standard_columns(self, df: pd.DataFrame) -> Dict[str, str]:
        candidates = {"date": None, "description": None, "amount": None}
        sample = df.head(10)

        scores = {}
        for col in df.columns:
            values = sample[col].dropna().astype(str)
            if values.empty:
                continue

            score = {
                "date": sum(is_probable_date(v) for v in values),
                "amount": sum(is_probable_amount(v) for v in values),
                "description": sum(is_probable_description(v) for v in values),
            }
            scores[col] = score

        for key in candidates:
            best_col = max(scores.items(), key=lambda item: item[1][key], default=(None, {}))
            if best_col[1].get(key, 0) >= len(sample) // 2:
                candidates[key] = best_col[0]

        return candidates
