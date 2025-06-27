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
        account_id: Optional[str] = None,
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
        self.account_id = account_id
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
        account_id: UUID,
        uploaded_file_id: str,
        column_mapping: dict,
        header_row_index: int,
        data_start_row_index: int,
    ):
        self.account_id = account_id
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
        statement=None,
    ):
        self.uploaded_file_id = uploaded_file_id
        self.transactions_saved = transactions_saved
        self.duplicated_transactions = duplicated_transactions
        self.statement = statement


class TransactionDTO:
    def __init__(
        self,
        date: str,
        amount: float,
        description: str,
        statement_id: Optional[str] = None,
        account_id: Optional[str] = None,
        id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        category_id: Optional[UUID] = None,
        categorization_status: Optional[str] = None,
        normalized_description: Optional[str] = None,
        row_index: Optional[int] = None,
        sort_index: Optional[int] = None,
        source_type: str = "upload",
        manual_position_after: Optional[UUID] = None,
        counterparty_account_id: Optional[UUID] = None,
    ):
        self.id = id
        self.date = date
        self.amount = amount
        self.description = description
        self.statement_id = statement_id
        self.account_id = account_id
        self.created_at = created_at
        self.category_id = category_id
        self.categorization_status = categorization_status
        self.normalized_description = normalized_description
        self.row_index = row_index
        self.sort_index = sort_index
        self.source_type = source_type
        self.manual_position_after = manual_position_after
        self.counterparty_account_id = counterparty_account_id

    @classmethod
    def from_entity(cls, entity):
        return cls(
            id=str(entity.id) if entity.id else None,
            date=entity.date,
            amount=entity.amount,
            description=entity.description,
            statement_id=str(entity.statement_id) if entity.statement_id else None,
            account_id=str(entity.account_id) if entity.account_id else None,
            created_at=entity.created_at,
            category_id=entity.category_id,
            categorization_status=entity.categorization_status.value if entity.categorization_status else None,
            normalized_description=entity.normalized_description,
            row_index=entity.row_index,
            sort_index=entity.sort_index,
            source_type=entity.source_type.value if entity.source_type else "upload",
            manual_position_after=entity.manual_position_after,
            counterparty_account_id=entity.counterparty_account_id,
        )
