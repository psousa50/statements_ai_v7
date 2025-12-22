from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from app.domain.dto.uploaded_file import FileAnalysisMetadataDTO, UploadedFileDTO


class UploadedFileRepository(ABC):
    @abstractmethod
    def save(self, filename: str, content: bytes) -> UploadedFileDTO:
        pass

    @abstractmethod
    def find_by_id(self, file_id: UUID) -> Optional[UploadedFileDTO]:
        pass


class FileAnalysisMetadataRepository(ABC):
    @abstractmethod
    def save(
        self,
        file_hash: str,
        column_mapping: dict,
        header_row_index: int,
        data_start_row_index: int,
        account_id: Optional[UUID] = None,
        row_filters: Optional[dict] = None,
    ) -> FileAnalysisMetadataDTO:
        pass

    @abstractmethod
    def update(
        self,
        file_hash: str,
        column_mapping: dict,
        header_row_index: int,
        data_start_row_index: int,
        account_id: Optional[UUID] = None,
        row_filters: Optional[dict] = None,
    ) -> FileAnalysisMetadataDTO:
        pass

    @abstractmethod
    def find_by_hash(self, file_hash: str, user_id: UUID) -> Optional[FileAnalysisMetadataDTO]:
        pass
