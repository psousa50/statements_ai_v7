from typing import Dict, List, Optional
from uuid import UUID

from app.domain.models.uploaded_file import FileAnalysisMetadata, UploadedFile
from app.ports.repositories.uploaded_file import FileAnalysisMetadataRepository, UploadedFileRepository


class SQLAlchemyUploadedFileRepository(UploadedFileRepository):
    def __init__(self, session):
        self.session = session

    def save(self, filename: str, content: bytes) -> Dict:
        uploaded_file = UploadedFile(filename=filename, content=content)

        self.session.add(uploaded_file)
        self.session.commit()
        self.session.refresh(uploaded_file)

        return {
            "id": str(uploaded_file.id),
            "filename": uploaded_file.filename,
            "created_at": uploaded_file.created_at,
        }

    def find_by_id(self, file_id: UUID) -> Optional[Dict]:
        uploaded_file = self.session.query(UploadedFile).filter(UploadedFile.id == file_id).first()

        if not uploaded_file:
            return None

        return {
            "id": str(uploaded_file.id),
            "filename": uploaded_file.filename,
            "content": uploaded_file.content,
            "created_at": uploaded_file.created_at,
        }


class SQLAlchemyFileAnalysisMetadataRepository(FileAnalysisMetadataRepository):
    def __init__(self, session):
        self.session = session

    def save(
        self,
        uploaded_file_id: UUID,
        file_hash: str,
        file_type: str,
        column_mapping: Dict,
        header_row_index: int,
        data_start_row_index: int,
    ) -> Dict:
        metadata = FileAnalysisMetadata(
            uploaded_file_id=uploaded_file_id,
            file_hash=file_hash,
            file_type=file_type,
            column_mapping=column_mapping,
            header_row_index=header_row_index,
            data_start_row_index=data_start_row_index,
        )

        self.session.add(metadata)
        self.session.commit()
        self.session.refresh(metadata)

        result = {
            "id": str(metadata.id),
            "uploaded_file_id": str(metadata.uploaded_file_id),
            "file_hash": metadata.file_hash,
            "file_type": metadata.file_type,
            "column_mapping": metadata.column_mapping,
            "header_row_index": metadata.header_row_index,
            "data_start_row_index": metadata.data_start_row_index,
            "created_at": metadata.created_at,
        }

        return result

    def find_by_hash(self, file_hash: str) -> Optional[Dict]:
        metadata = self.session.query(FileAnalysisMetadata).filter(FileAnalysisMetadata.file_hash == file_hash).first()

        if not metadata:
            return None

        result = {
            "id": str(metadata.id),
            "uploaded_file_id": str(metadata.uploaded_file_id),
            "file_hash": metadata.file_hash,
            "file_type": metadata.file_type,
            "column_mapping": metadata.column_mapping,
            "header_row_index": metadata.header_row_index,
            "data_start_row_index": metadata.data_start_row_index,
            "created_at": metadata.created_at,
        }

        # Include normalized_sample if it exists (for backward compatibility)
        if hasattr(metadata, "normalized_sample") and metadata.normalized_sample is not None:
            result["normalized_sample"] = metadata.normalized_sample

        return result
