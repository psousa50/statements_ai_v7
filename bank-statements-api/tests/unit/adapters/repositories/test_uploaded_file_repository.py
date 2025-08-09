import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

from app.adapters.repositories.uploaded_file import SQLAlchemyFileAnalysisMetadataRepository, SQLAlchemyUploadedFileRepository
from app.domain.dto.uploaded_file import FileAnalysisMetadataDTO, UploadedFileDTO


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

        file_type = "CSV"
        result = repo.save(filename, content, file_type)

        assert isinstance(result, UploadedFileDTO)
        assert result.id is not None
        assert result.filename == filename

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
            file_type="CSV",
            created_at=datetime.now(timezone.utc),
        )
        session.query.return_value.filter.return_value.first.return_value = mock_file

        repo = SQLAlchemyUploadedFileRepository(session)
        result = repo.find_by_id(file_id)

        assert isinstance(result, UploadedFileDTO)
        assert result.id == str(file_id)
        assert result.filename == "test.csv"
        assert result.content == b"test content"

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

        file_hash = "abc123"
        account_id = uuid.uuid4()
        column_mapping = {
            "date": "Date",
            "amount": "Amount",
            "description": "Description",
        }
        header_row_index = 0
        data_start_row_index = 1

        result = repo.save(
            file_hash=file_hash,
            column_mapping=column_mapping,
            header_row_index=header_row_index,
            data_start_row_index=data_start_row_index,
            account_id=account_id,
        )

        assert isinstance(result, FileAnalysisMetadataDTO)
        assert result.id is not None
        assert result.file_hash == file_hash
        assert result.account_id == str(account_id)
        assert result.column_mapping == column_mapping
        assert result.header_row_index == header_row_index
        assert result.data_start_row_index == data_start_row_index
        assert result.row_filters is None

        session.add.assert_called_once()
        session.commit.assert_called_once()
        session.refresh.assert_called_once()

    def test_save_metadata_with_row_filters(self):
        session = MagicMock()
        repo = SQLAlchemyFileAnalysisMetadataRepository(session)

        # Mock the behavior of SQLAlchemy
        def side_effect(metadata):
            metadata.id = uuid.uuid4()
            metadata.created_at = datetime.now(timezone.utc)
            return None

        session.add.side_effect = side_effect

        file_hash = "abc123"
        account_id = uuid.uuid4()
        column_mapping = {
            "date": "Date",
            "amount": "Amount",
            "description": "Description",
        }
        header_row_index = 0
        data_start_row_index = 1
        row_filters = [{"column_name": "amount", "operator": "greater_than", "value": "100", "case_sensitive": False}]

        result = repo.save(
            file_hash=file_hash,
            column_mapping=column_mapping,
            header_row_index=header_row_index,
            data_start_row_index=data_start_row_index,
            account_id=account_id,
            row_filters=row_filters,
        )

        assert isinstance(result, FileAnalysisMetadataDTO)
        assert result.id is not None
        assert result.file_hash == file_hash
        assert result.account_id == str(account_id)
        assert result.column_mapping == column_mapping
        assert result.header_row_index == header_row_index
        assert result.data_start_row_index == data_start_row_index
        assert result.row_filters == row_filters

        session.add.assert_called_once()
        session.commit.assert_called_once()
        session.refresh.assert_called_once()

    def test_find_by_hash(self):
        session = MagicMock()
        metadata_id = uuid.uuid4()
        row_filters = [{"column_name": "description", "operator": "contains", "value": "test", "case_sensitive": False}]
        mock_metadata = MagicMock(
            id=metadata_id,
            file_hash="abc123",
            account_id=uuid.uuid4(),
            column_mapping={
                "date": "Date",
                "amount": "Amount",
                "description": "Description",
            },
            header_row_index=0,
            data_start_row_index=1,
            row_filters=row_filters,
            created_at=datetime.now(timezone.utc),
        )
        session.query.return_value.filter.return_value.first.return_value = mock_metadata

        repo = SQLAlchemyFileAnalysisMetadataRepository(session)
        result = repo.find_by_hash("abc123")

        assert isinstance(result, FileAnalysisMetadataDTO)
        assert result.id == str(metadata_id)
        assert result.file_hash == "abc123"
        assert result.account_id is not None
        assert result.row_filters == row_filters

        session.query.assert_called_once()
        session.query.return_value.filter.assert_called_once()
