import pytest
from unittest.mock import Mock
from uuid import uuid4

from app.services.statement import StatementService
from app.domain.models.statement import Statement


class TestStatementService:
    """Test cases for StatementService"""

    def setup_method(self):
        """Set up test fixtures"""
        self.statement_repo = Mock()
        self.transaction_repo = Mock()
        self.statement_service = StatementService(
            statement_repository=self.statement_repo,
            transaction_repository=self.transaction_repo,
        )

    def test_get_all_statements(self):
        """Test getting all statements"""
        # Arrange
        mock_statements = [
            Mock(spec=Statement, id=uuid4(), filename="test1.csv"),
            Mock(spec=Statement, id=uuid4(), filename="test2.csv"),
        ]
        self.statement_repo.find_all.return_value = mock_statements

        # Act
        result = self.statement_service.get_all_statements()

        # Assert
        assert result == mock_statements
        self.statement_repo.find_all.assert_called_once()

    def test_get_statement_by_id_found(self):
        """Test getting a statement by ID when it exists"""
        # Arrange
        statement_id = uuid4()
        mock_statement = Mock(spec=Statement, id=statement_id, filename="test.csv")
        self.statement_repo.find_by_id.return_value = mock_statement

        # Act
        result = self.statement_service.get_statement_by_id(statement_id)

        # Assert
        assert result == mock_statement
        self.statement_repo.find_by_id.assert_called_once_with(statement_id)

    def test_get_statement_by_id_not_found(self):
        """Test getting a statement by ID when it doesn't exist"""
        # Arrange
        statement_id = uuid4()
        self.statement_repo.find_by_id.return_value = None

        # Act
        result = self.statement_service.get_statement_by_id(statement_id)

        # Assert
        assert result is None
        self.statement_repo.find_by_id.assert_called_once_with(statement_id)

    def test_delete_statement_with_transactions_success(self):
        """Test successful deletion of statement with transactions"""
        # Arrange
        statement_id = uuid4()
        mock_statement = Mock(spec=Statement, id=statement_id, filename="test.csv")
        self.statement_repo.find_by_id.return_value = mock_statement
        self.transaction_repo.delete_by_statement_id.return_value = 5

        # Act
        result = self.statement_service.delete_statement_with_transactions(statement_id)

        # Assert
        assert result == {
            "message": "Statement deleted successfully. 5 transactions were also deleted.",
            "transaction_count": 5,
        }
        self.statement_repo.find_by_id.assert_called_once_with(statement_id)
        self.transaction_repo.delete_by_statement_id.assert_called_once_with(statement_id)
        self.statement_repo.delete.assert_called_once_with(statement_id)

    def test_delete_statement_with_transactions_not_found(self):
        """Test deletion of statement that doesn't exist"""
        # Arrange
        statement_id = uuid4()
        self.statement_repo.find_by_id.return_value = None

        # Act & Assert
        with pytest.raises(ValueError, match=f"Statement with ID {statement_id} not found"):
            self.statement_service.delete_statement_with_transactions(statement_id)

        self.statement_repo.find_by_id.assert_called_once_with(statement_id)
        self.transaction_repo.delete_by_statement_id.assert_not_called()
        self.statement_repo.delete.assert_not_called()

    def test_delete_statement_with_transactions_zero_transactions(self):
        """Test deletion of statement with no transactions"""
        # Arrange
        statement_id = uuid4()
        mock_statement = Mock(spec=Statement, id=statement_id, filename="test.csv")
        self.statement_repo.find_by_id.return_value = mock_statement
        self.transaction_repo.delete_by_statement_id.return_value = 0

        # Act
        result = self.statement_service.delete_statement_with_transactions(statement_id)

        # Assert
        assert result == {
            "message": "Statement deleted successfully. 0 transactions were also deleted.",
            "transaction_count": 0,
        }
        self.statement_repo.find_by_id.assert_called_once_with(statement_id)
        self.transaction_repo.delete_by_statement_id.assert_called_once_with(statement_id)
        self.statement_repo.delete.assert_called_once_with(statement_id)

    def test_delete_statement_with_transactions_repository_error(self):
        """Test handling of repository errors during deletion"""
        # Arrange
        statement_id = uuid4()
        mock_statement = Mock(spec=Statement, id=statement_id, filename="test.csv")
        self.statement_repo.find_by_id.return_value = mock_statement
        self.transaction_repo.delete_by_statement_id.side_effect = Exception("Database error")

        # Act & Assert
        with pytest.raises(Exception, match="Database error"):
            self.statement_service.delete_statement_with_transactions(statement_id)

        self.statement_repo.find_by_id.assert_called_once_with(statement_id)
        self.transaction_repo.delete_by_statement_id.assert_called_once_with(statement_id)
        self.statement_repo.delete.assert_not_called()  # Should not reach this point
