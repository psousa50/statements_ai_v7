from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.domain.models.statement import Statement
from app.services.statement import StatementService


class TestStatementService:
    def setup_method(self):
        self.statement_repo = Mock()
        self.transaction_repo = Mock()
        self.user_id = uuid4()
        self.statement_service = StatementService(
            statement_repository=self.statement_repo,
            transaction_repository=self.transaction_repo,
        )

    def test_get_all_statements(self):
        mock_statements = [
            Mock(spec=Statement, id=uuid4(), filename="test1.csv"),
            Mock(spec=Statement, id=uuid4(), filename="test2.csv"),
        ]
        self.statement_repo.find_all.return_value = mock_statements

        result = self.statement_service.get_all_statements(self.user_id)

        assert result == mock_statements
        self.statement_repo.find_all.assert_called_once_with(self.user_id)

    def test_get_statement_by_id_found(self):
        statement_id = uuid4()
        mock_statement = Mock(spec=Statement, id=statement_id, filename="test.csv")
        self.statement_repo.find_by_id.return_value = mock_statement

        result = self.statement_service.get_statement_by_id(statement_id, self.user_id)

        assert result == mock_statement
        self.statement_repo.find_by_id.assert_called_once_with(statement_id, self.user_id)

    def test_get_statement_by_id_not_found(self):
        statement_id = uuid4()
        self.statement_repo.find_by_id.return_value = None

        result = self.statement_service.get_statement_by_id(statement_id, self.user_id)

        assert result is None
        self.statement_repo.find_by_id.assert_called_once_with(statement_id, self.user_id)

    def test_delete_statement_with_transactions_success(self):
        statement_id = uuid4()
        mock_statement = Mock(spec=Statement, id=statement_id, filename="test.csv")
        self.statement_repo.find_by_id.return_value = mock_statement
        self.transaction_repo.delete_by_statement_id.return_value = 5

        result = self.statement_service.delete_statement_with_transactions(statement_id, self.user_id)

        assert result == {
            "message": "Statement deleted successfully. 5 transactions were also deleted.",
            "transaction_count": 5,
        }
        self.statement_repo.find_by_id.assert_called_once_with(statement_id, self.user_id)
        self.transaction_repo.delete_by_statement_id.assert_called_once_with(statement_id)
        self.statement_repo.delete.assert_called_once_with(statement_id, self.user_id)

    def test_delete_statement_with_transactions_not_found(self):
        statement_id = uuid4()
        self.statement_repo.find_by_id.return_value = None

        with pytest.raises(ValueError, match=f"Statement with ID {statement_id} not found"):
            self.statement_service.delete_statement_with_transactions(statement_id, self.user_id)

        self.statement_repo.find_by_id.assert_called_once_with(statement_id, self.user_id)
        self.transaction_repo.delete_by_statement_id.assert_not_called()
        self.statement_repo.delete.assert_not_called()

    def test_delete_statement_with_transactions_zero_transactions(self):
        statement_id = uuid4()
        mock_statement = Mock(spec=Statement, id=statement_id, filename="test.csv")
        self.statement_repo.find_by_id.return_value = mock_statement
        self.transaction_repo.delete_by_statement_id.return_value = 0

        result = self.statement_service.delete_statement_with_transactions(statement_id, self.user_id)

        assert result == {
            "message": "Statement deleted successfully. 0 transactions were also deleted.",
            "transaction_count": 0,
        }
        self.statement_repo.find_by_id.assert_called_once_with(statement_id, self.user_id)
        self.transaction_repo.delete_by_statement_id.assert_called_once_with(statement_id)
        self.statement_repo.delete.assert_called_once_with(statement_id, self.user_id)

    def test_delete_statement_with_transactions_repository_error(self):
        statement_id = uuid4()
        mock_statement = Mock(spec=Statement, id=statement_id, filename="test.csv")
        self.statement_repo.find_by_id.return_value = mock_statement
        self.transaction_repo.delete_by_statement_id.side_effect = Exception("Database error")

        with pytest.raises(Exception, match="Database error"):
            self.statement_service.delete_statement_with_transactions(statement_id, self.user_id)

        self.statement_repo.find_by_id.assert_called_once_with(statement_id, self.user_id)
        self.transaction_repo.delete_by_statement_id.assert_called_once_with(statement_id)
        self.statement_repo.delete.assert_not_called()
