from dataclasses import dataclass
from typing import Dict

import pandas as pd


@dataclass
class ConversionModel:
    column_map: Dict[str, str]
    header_row: int
    start_row: int


class SchemaDetectorProtocol:
    def detect_schema(self, df: pd.DataFrame) -> ConversionModel:
        pass
