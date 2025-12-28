from typing import Optional
from uuid import UUID

from app.domain.dto.uploaded_file import FileAnalysisMetadataDTO, UploadedFileDTO
from app.domain.models.account import Account
from app.domain.models.uploaded_file import FileAnalysisMetadata, UploadedFile
from app.ports.repositories.uploaded_file import FileAnalysisMetadataRepository, UploadedFileRepository


class SQLAlchemyUploadedFileRepository(UploadedFileRepository):
    def __init__(self, session):
        self.session = session

    def save(self, filename: str, content: bytes, file_type: str) -> UploadedFileDTO:
        uploaded_file = UploadedFile(
            filename=filename,
            content=content,
            file_type=file_type,
        )

        self.session.add(uploaded_file)
        self.session.commit()
        self.session.refresh(uploaded_file)

        return UploadedFileDTO(
            id=str(uploaded_file.id),
            filename=uploaded_file.filename,
            file_type=uploaded_file.file_type,
            created_at=uploaded_file.created_at,
            content=None,
        )

    def find_by_id(self, file_id: UUID) -> Optional[UploadedFileDTO]:
        uploaded_file = self.session.query(UploadedFile).filter(UploadedFile.id == file_id).first()

        if not uploaded_file:
            return None

        return UploadedFileDTO(
            id=str(uploaded_file.id),
            filename=uploaded_file.filename,
            file_type=uploaded_file.file_type,
            content=uploaded_file.content,
            created_at=uploaded_file.created_at,
        )


class SQLAlchemyFileAnalysisMetadataRepository(FileAnalysisMetadataRepository):
    def __init__(self, session):
        self.session = session

    def save(
        self,
        file_hash: str,
        column_mapping: dict,
        header_row_index: int,
        data_start_row_index: int,
        account_id: Optional[UUID] = None,
        row_filters: Optional[dict] = None,
    ) -> FileAnalysisMetadataDTO:
        metadata = FileAnalysisMetadata(
            file_hash=file_hash,
            account_id=account_id,
            column_mapping=column_mapping,
            header_row_index=header_row_index,
            data_start_row_index=data_start_row_index,
            row_filters=row_filters,
        )

        self.session.add(metadata)
        self.session.commit()
        self.session.refresh(metadata)

        return FileAnalysisMetadataDTO(
            id=str(metadata.id),
            file_hash=metadata.file_hash,
            account_id=str(metadata.account_id) if metadata.account_id else None,
            column_mapping=metadata.column_mapping,
            header_row_index=metadata.header_row_index,
            data_start_row_index=metadata.data_start_row_index,
            created_at=metadata.created_at,
            row_filters=metadata.row_filters,
        )

    def update(
        self,
        file_hash: str,
        column_mapping: dict,
        header_row_index: int,
        data_start_row_index: int,
        account_id: Optional[UUID] = None,
        row_filters: Optional[dict] = None,
    ) -> FileAnalysisMetadataDTO:
        metadata = (
            self.session.query(FileAnalysisMetadata)
            .filter(FileAnalysisMetadata.file_hash == file_hash, FileAnalysisMetadata.account_id == account_id)
            .first()
        )

        if not metadata:
            raise ValueError(f"Metadata with file_hash {file_hash} and account_id {account_id} not found")

        metadata.column_mapping = column_mapping
        metadata.header_row_index = header_row_index
        metadata.data_start_row_index = data_start_row_index
        metadata.row_filters = row_filters

        self.session.commit()
        self.session.refresh(metadata)

        return FileAnalysisMetadataDTO(
            id=str(metadata.id),
            file_hash=metadata.file_hash,
            account_id=str(metadata.account_id) if metadata.account_id else None,
            column_mapping=metadata.column_mapping,
            header_row_index=metadata.header_row_index,
            data_start_row_index=metadata.data_start_row_index,
            created_at=metadata.created_at,
            row_filters=metadata.row_filters,
        )

    def find_by_hash(self, file_hash: str, user_id: UUID) -> Optional[FileAnalysisMetadataDTO]:
        metadata = (
            self.session.query(FileAnalysisMetadata)
            .join(Account, FileAnalysisMetadata.account_id == Account.id)
            .filter(FileAnalysisMetadata.file_hash == file_hash, Account.user_id == user_id)
            .first()
        )

        if not metadata:
            return None

        return FileAnalysisMetadataDTO(
            id=str(metadata.id),
            file_hash=metadata.file_hash,
            account_id=str(metadata.account_id) if metadata.account_id else None,
            column_mapping=metadata.column_mapping,
            header_row_index=metadata.header_row_index,
            data_start_row_index=metadata.data_start_row_index,
            created_at=metadata.created_at,
            row_filters=metadata.row_filters,
        )

    def find_by_hash_and_account(self, file_hash: str, account_id: UUID) -> Optional[FileAnalysisMetadataDTO]:
        metadata = (
            self.session.query(FileAnalysisMetadata)
            .filter(FileAnalysisMetadata.file_hash == file_hash, FileAnalysisMetadata.account_id == account_id)
            .first()
        )

        if not metadata:
            return None

        return FileAnalysisMetadataDTO(
            id=str(metadata.id),
            file_hash=metadata.file_hash,
            account_id=str(metadata.account_id) if metadata.account_id else None,
            column_mapping=metadata.column_mapping,
            header_row_index=metadata.header_row_index,
            data_start_row_index=metadata.data_start_row_index,
            created_at=metadata.created_at,
            row_filters=metadata.row_filters,
        )
