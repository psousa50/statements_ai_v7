from datetime import datetime
from typing import Optional, Tuple
from uuid import UUID


class AnalysisResultDTO:
    def __init__(
        self,
        uploaded_file_id: str,
        file_type: str,
        column_mapping: dict,
        header_row_index: int,
        data_start_row_index: int,
        sample_data: list[list],
        source_id: Optional[str] = None,
        total_transactions: int = 0,
        unique_transactions: int = 0,
        duplicate_transactions: int = 0,
        date_range: Tuple[str, str] = ("", ""),
        total_amount: float = 0.0,
        total_debit: float = 0.0,
        total_credit: float = 0.0,
    ):
        self.uploaded_file_id = uploaded_file_id
        self.file_type = file_type
        self.column_mapping = column_mapping
        self.header_row_index = header_row_index
        self.data_start_row_index = data_start_row_index
        self.sample_data = sample_data
        self.source_id = source_id
        self.total_transactions = total_transactions
        self.unique_transactions = unique_transactions
        self.duplicate_transactions = duplicate_transactions
        self.date_range = date_range
        self.total_amount = total_amount
        self.total_debit = total_debit
        self.total_credit = total_credit


class PersistenceRequestDTO:
    def __init__(
        self,
        source_id: UUID,
        uploaded_file_id: str,
        column_mapping: dict,
        header_row_index: int,
        data_start_row_index: int,
    ):
        self.source_id = source_id
        self.uploaded_file_id = uploaded_file_id
        self.column_mapping = column_mapping
        self.header_row_index = header_row_index
        self.data_start_row_index = data_start_row_index


class PersistenceResultDTO:
    def __init__(
        self,
        uploaded_file_id: str,
        transactions_saved: int,
        duplicated_transactions: int = 0,
    ):
        self.uploaded_file_id = uploaded_file_id
        self.transactions_saved = transactions_saved
        self.duplicated_transactions = duplicated_transactions


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
        category_id: Optional[UUID] = None,
        categorization_status: Optional[str] = None,
        normalized_description: Optional[str] = None,
    ):
        self.id = id
        self.date = date
        self.amount = amount
        self.description = description
        self.uploaded_file_id = uploaded_file_id
        self.source_id = source_id
        self.created_at = created_at
        self.category_id = category_id
        self.categorization_status = categorization_status
        self.normalized_description = normalized_description

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
            category_id=entity.category_id,
            categorization_status=entity.categorization_status.value
            if entity.categorization_status
            else None,
            normalized_description=entity.normalized_description,
        )
