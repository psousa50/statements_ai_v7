from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.domain.models.source import Source
from app.ports.repositories.source import SourceRepository
from app.services.source import SourceService


class TestSourceService:
    """Unit tests for SourceService"""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock repository for testing"""
        repository = MagicMock(spec=SourceRepository)
        return repository

    @pytest.fixture
    def service(self, mock_repository):
        """Create a service with the mock repository"""
        return SourceService(mock_repository)

    @pytest.fixture
    def sample_source(self):
        """Create a sample source for testing"""
        source = Source(
            id=uuid4(),
            name="Test Source",
        )
        return source

    def test_create_source(self, service, mock_repository, sample_source):
        """Test creating a source"""
        # Arrange
        mock_repository.create.return_value = sample_source
        name = "Test Source"

        # Act
        result = service.create_source(name=name)

        # Assert
        assert result == sample_source
        mock_repository.create.assert_called_once()
        # Check that the source passed to create has the correct attributes
        created_source = mock_repository.create.call_args[0][0]
        assert created_source.name == name

    def test_get_source_by_id(self, service, mock_repository, sample_source):
        """Test getting a source by ID"""
        # Arrange
        source_id = sample_source.id
        mock_repository.get_by_id.return_value = sample_source

        # Act
        result = service.get_source_by_id(source_id)

        # Assert
        assert result == sample_source
        mock_repository.get_by_id.assert_called_once_with(source_id)

    def test_get_source_by_id_not_found(self, service, mock_repository):
        """Test getting a source that doesn't exist"""
        # Arrange
        source_id = uuid4()
        mock_repository.get_by_id.return_value = None

        # Act
        result = service.get_source_by_id(source_id)

        # Assert
        assert result is None
        mock_repository.get_by_id.assert_called_once_with(source_id)

    def test_get_source_by_name(self, service, mock_repository, sample_source):
        """Test getting a source by name"""
        # Arrange
        name = sample_source.name
        mock_repository.get_by_name.return_value = sample_source

        # Act
        result = service.get_source_by_name(name)

        # Assert
        assert result == sample_source
        mock_repository.get_by_name.assert_called_once_with(name)

    def test_get_source_by_name_not_found(self, service, mock_repository):
        """Test getting a source by name that doesn't exist"""
        # Arrange
        name = "Nonexistent Source"
        mock_repository.get_by_name.return_value = None

        # Act
        result = service.get_source_by_name(name)

        # Assert
        assert result is None
        mock_repository.get_by_name.assert_called_once_with(name)

    def test_get_all_sources(self, service, mock_repository):
        """Test getting all sources"""
        # Arrange
        sources = [
            Source(id=uuid4(), name="Source 1"),
            Source(id=uuid4(), name="Source 2"),
        ]
        mock_repository.get_all.return_value = sources

        # Act
        result = service.get_all_sources()

        # Assert
        assert result == sources
        mock_repository.get_all.assert_called_once()

    def test_update_source(self, service, mock_repository, sample_source):
        """Test updating a source"""
        # Arrange
        source_id = sample_source.id
        mock_repository.get_by_id.return_value = sample_source
        mock_repository.update.return_value = sample_source

        new_name = "Updated Source"

        # Act
        result = service.update_source(
            source_id=source_id,
            name=new_name,
        )

        # Assert
        assert result == sample_source
        mock_repository.get_by_id.assert_called_once_with(source_id)
        mock_repository.update.assert_called_once_with(sample_source)

        # Check that the source was updated with the new values
        assert sample_source.name == new_name

    def test_update_source_not_found(self, service, mock_repository):
        """Test updating a source that doesn't exist"""
        # Arrange
        source_id = uuid4()
        mock_repository.get_by_id.return_value = None

        # Act
        result = service.update_source(
            source_id=source_id,
            name="Updated Source",
        )

        # Assert
        assert result is None
        mock_repository.get_by_id.assert_called_once_with(source_id)
        mock_repository.update.assert_not_called()

    def test_delete_source(self, service, mock_repository, sample_source):
        """Test deleting a source"""
        # Arrange
        source_id = sample_source.id
        mock_repository.get_by_id.return_value = sample_source

        # Act
        result = service.delete_source(source_id)

        # Assert
        assert result is True
        mock_repository.get_by_id.assert_called_once_with(source_id)
        mock_repository.delete.assert_called_once_with(source_id)

    def test_delete_source_not_found(self, service, mock_repository):
        """Test deleting a source that doesn't exist"""
        # Arrange
        source_id = uuid4()
        mock_repository.get_by_id.return_value = None

        # Act
        result = service.delete_source(source_id)

        # Assert
        assert result is False
        mock_repository.get_by_id.assert_called_once_with(source_id)
        mock_repository.delete.assert_not_called()
