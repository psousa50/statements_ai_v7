from datetime import datetime
from typing import List, Optional
from uuid import UUID


class AnalysisResultDTO:
    def __init__(
        self,
        uploaded_file_id: str,
        file_type: str,
        column_mapping: dict,
        header_row_index: int,
        data_start_row_index: int,
        file_hash: str,
        sample_data: Optional[List[dict]] = None,
    ):
        self.uploaded_file_id = uploaded_file_id
        self.file_type = file_type
        self.column_mapping = column_mapping
        self.header_row_index = header_row_index
        self.data_start_row_index = data_start_row_index
        self.file_hash = file_hash
        self.sample_data = sample_data


class PersistenceResultDTO:
    def __init__(
        self,
        uploaded_file_id: str,
        transactions_saved: int,
    ):
        self.uploaded_file_id = uploaded_file_id
        self.transactions_saved = transactions_saved


class TransactionDTO:
    def __init__(
        self,
        date: str,
        amount: float,
        description: str,
        uploaded_file_id: str,
        source_id: Optional[str] = None,
        id: Optional[str] = None,
        created_at: Optional[datetime] = None,
    ):
        self.id = id
        self.date = date
        self.amount = amount
        self.description = description
        self.uploaded_file_id = uploaded_file_id
        self.source_id = source_id
        self.created_at = created_at

    @classmethod
    def from_entity(cls, entity):
        return cls(
            id=str(entity.id) if entity.id else None,
            date=entity.date,
            amount=entity.amount,
            description=entity.description,
            uploaded_file_id=str(entity.uploaded_file_id),
            source_id=str(entity.source_id) if entity.source_id else None,
            created_at=entity.created_at,
        )
