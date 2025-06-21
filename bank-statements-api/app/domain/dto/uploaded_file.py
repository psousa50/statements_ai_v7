from datetime import datetime
from typing import Optional


class UploadedFileDTO:
    def __init__(
        self,
        id: str,
        filename: str,
        file_type: str,
        created_at: datetime,
        content: Optional[bytes] = None,
    ):
        self.id = id
        self.filename = filename
        self.file_type = file_type
        self.created_at = created_at
        self.content = content

    @classmethod
    def from_entity(cls, entity):
        return cls(
            id=str(entity.id),
            filename=entity.filename,
            file_type=entity.file_type,
            created_at=entity.created_at,
            content=entity.content,
        )


class FileAnalysisMetadataDTO:
    def __init__(
        self,
        id: str,
        file_hash: str,
        account_id: Optional[str],
        column_mapping: dict,
        header_row_index: int,
        data_start_row_index: int,
        created_at: datetime,
    ):
        self.id = id
        self.file_hash = file_hash
        self.account_id = account_id
        self.column_mapping = column_mapping
        self.header_row_index = header_row_index
        self.data_start_row_index = data_start_row_index
        self.created_at = created_at

    @classmethod
    def from_entity(cls, entity):
        return cls(
            id=str(entity.id),
            uploaded_file_id=str(entity.uploaded_file_id),
            file_hash=entity.file_hash,
            account_id=str(entity.account_id) if entity.account_id else None,
            column_mapping=entity.column_mapping,
            header_row_index=entity.header_row_index,
            data_start_row_index=entity.data_start_row_index,
            created_at=entity.created_at,
        )
