import uuid
from datetime import datetime, timezone
from uuid import UUID

from app.domain.models.uploaded_file import FileAnalysisMetadata, UploadedFile


class TestUploadedFileModel:
    def test_uploaded_file_model_attributes(self):
        file = UploadedFile(
            id=uuid.uuid4(),
            filename="test.csv",
            content=b"test content",
            created_at=datetime.now(timezone.utc),
        )

        assert isinstance(file.id, UUID)
        assert file.filename == "test.csv"
        assert file.content == b"test content"
        assert isinstance(file.created_at, datetime)
        assert file.__tablename__ == "uploaded_files"


class TestFileAnalysisMetadataModel:
    def test_file_analysis_metadata_model_attributes(self):
        metadata = FileAnalysisMetadata(
            id=uuid.uuid4(),
            file_hash="abc123",
            account_id=uuid.uuid4(),
            column_mapping={
                "date": "Date",
                "amount": "Amount",
                "description": "Description",
            },
            header_row_index=0,
            data_start_row_index=1,
            created_at=datetime.now(timezone.utc),
        )

        assert isinstance(metadata.id, UUID)
        assert metadata.file_hash == "abc123"
        assert isinstance(metadata.account_id, UUID)
        assert metadata.column_mapping == {
            "date": "Date",
            "amount": "Amount",
            "description": "Description",
        }
        assert metadata.header_row_index == 0
        assert metadata.data_start_row_index == 1
        # normalized_sample field has been removed
        assert isinstance(metadata.created_at, datetime)
        assert metadata.__tablename__ == "file_analysis_metadata"
