from dataclasses import dataclass
from typing import Dict

import pandas as pd


@dataclass
class ConversionModel:
    column_mapping: Dict[str, str]
    header_row_index: int
    data_start_row_index: int


class SchemaDetectorProtocol:
    def detect_schema(self, df: pd.DataFrame) -> ConversionModel:
        pass
