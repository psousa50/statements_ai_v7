import pytest
from unittest.mock import MagicMock, patch
import uuid
from datetime import datetime, timezone

from app.adapters.repositories.uploaded_file import SQLAlchemyUploadedFileRepository, SQLAlchemyFileAnalysisMetadataRepository
from app.domain.models.uploaded_file import UploadedFile, FileAnalysisMetadata


class TestUploadedFileRepository:
    def test_save_uploaded_file(self):
        session = MagicMock()
        repo = SQLAlchemyUploadedFileRepository(session)
        
        # Mock the behavior of SQLAlchemy
        def side_effect(uploaded_file):
            uploaded_file.id = uuid.uuid4()
            uploaded_file.created_at = datetime.now(timezone.utc)
            return None
        
        session.add.side_effect = side_effect
        
        filename = "test.csv"
        content = b"test content"
        
        result = repo.save(filename, content)
        
        assert "id" in result
        assert result["filename"] == filename
        
        session.add.assert_called_once()
        session.commit.assert_called_once()
        session.refresh.assert_called_once()
    
    def test_find_by_id(self):
        session = MagicMock()
        file_id = uuid.uuid4()
        mock_file = MagicMock(
            id=file_id,
            filename="test.csv",
            content=b"test content",
            created_at=datetime.now(timezone.utc)
        )
        session.query.return_value.filter.return_value.first.return_value = mock_file
        
        repo = SQLAlchemyUploadedFileRepository(session)
        result = repo.find_by_id(file_id)
        
        assert result["id"] == str(file_id)
        assert result["filename"] == "test.csv"
        assert result["content"] == b"test content"
        
        session.query.assert_called_once()
        session.query.return_value.filter.assert_called_once()


class TestFileAnalysisMetadataRepository:
    def test_save_metadata(self):
        session = MagicMock()
        repo = SQLAlchemyFileAnalysisMetadataRepository(session)
        
        # Mock the behavior of SQLAlchemy
        def side_effect(metadata):
            metadata.id = uuid.uuid4()
            metadata.created_at = datetime.now(timezone.utc)
            return None
        
        session.add.side_effect = side_effect
        
        uploaded_file_id = uuid.uuid4()
        file_hash = "abc123"
        file_type = "CSV"
        column_mapping = {"date": "Date", "amount": "Amount", "description": "Description"}
        header_row_index = 0
        data_start_row_index = 1
        normalized_sample = [{"date": "2023-01-01", "amount": 100.0}]
        
        result = repo.save(
            uploaded_file_id=uploaded_file_id,
            file_hash=file_hash,
            file_type=file_type,
            column_mapping=column_mapping,
            header_row_index=header_row_index,
            data_start_row_index=data_start_row_index,
            normalized_sample=normalized_sample
        )
        
        assert "id" in result
        assert result["uploaded_file_id"] == str(uploaded_file_id)
        assert result["file_hash"] == file_hash
        assert result["file_type"] == file_type
        assert result["column_mapping"] == column_mapping
        assert result["header_row_index"] == header_row_index
        assert result["data_start_row_index"] == data_start_row_index
        assert result["normalized_sample"] == normalized_sample
        
        session.add.assert_called_once()
        session.commit.assert_called_once()
        session.refresh.assert_called_once()
    
    def test_find_by_hash(self):
        session = MagicMock()
        metadata_id = uuid.uuid4()
        uploaded_file_id = uuid.uuid4()
        mock_metadata = MagicMock(
            id=metadata_id,
            uploaded_file_id=uploaded_file_id,
            file_hash="abc123",
            file_type="CSV",
            column_mapping={"date": "Date", "amount": "Amount", "description": "Description"},
            header_row_index=0,
            data_start_row_index=1,
            normalized_sample=[{"date": "2023-01-01", "amount": 100.0}],
            created_at=datetime.now(timezone.utc)
        )
        session.query.return_value.filter.return_value.first.return_value = mock_metadata
        
        repo = SQLAlchemyFileAnalysisMetadataRepository(session)
        result = repo.find_by_hash("abc123")
        
        assert result["id"] == str(metadata_id)
        assert result["uploaded_file_id"] == str(uploaded_file_id)
        assert result["file_hash"] == "abc123"
        assert result["file_type"] == "CSV"
        
        session.query.assert_called_once()
        session.query.return_value.filter.assert_called_once()
