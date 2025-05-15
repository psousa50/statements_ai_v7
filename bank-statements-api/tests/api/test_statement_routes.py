# Import statement routes with patch to avoid dependency issues
import sys
from io import BytesIO
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.statements import register_statement_routes

# Mock the dependencies that might cause import issues
sys.modules["app.ai.gemini_ai"] = MagicMock()
sys.modules["google"] = MagicMock()
sys.modules["google.generativeai"] = MagicMock()

# Now we can safely import the module


@pytest.fixture
def mock_dependencies():
    mock_deps = MagicMock()
    mock_deps.statement_analyzer_service = MagicMock()
    mock_deps.statement_persistence_service = MagicMock()
    return mock_deps


@pytest.fixture
def app(mock_dependencies):
    app = FastAPI()

    def provide_dependencies():
        yield mock_dependencies

    register_statement_routes(app, provide_dependencies)
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


class TestStatementRoutes:
    def test_analyze_statement_success(self, client, mock_dependencies):
        # Prepare test data
        file_content = b"Date,Amount,Description\n2023-01-01,100.00,Test"
        uploaded_file_id = str(uuid4())
        file_hash = "abc123"

        # Configure mock
        mock_dependencies.statement_analyzer_service.analyze.return_value = {
            "uploaded_file_id": uploaded_file_id,
            "file_type": "CSV",
            "column_mapping": {"date": "Date", "amount": "Amount", "description": "Description"},
            "header_row_index": 0,
            "data_start_row_index": 1,
            "sample_data": [{"date": "2023-01-01", "amount": 100.00, "description": "Test"}],
            "file_hash": file_hash,
        }

        # Make request
        response = client.post("/api/v1/statements/analyze", files={"file": ("test.csv", BytesIO(file_content), "text/csv")})

        # Assertions
        assert response.status_code == 200
        assert response.json()["uploaded_file_id"] == uploaded_file_id
        assert response.json()["file_type"] == "CSV"
        assert response.json()["column_mapping"]["date"] == "Date"
        assert response.json()["file_hash"] == file_hash

        # Verify mock was called correctly
        mock_dependencies.statement_analyzer_service.analyze.assert_called_once()
        args, kwargs = mock_dependencies.statement_analyzer_service.analyze.call_args
        assert kwargs["filename"] == "test.csv"
        assert kwargs["file_content"] == file_content

    def test_analyze_statement_error(self, client, mock_dependencies):
        # Configure mock to raise an exception
        mock_dependencies.statement_analyzer_service.analyze.side_effect = Exception("Test error")

        # Make request
        response = client.post("/api/v1/statements/analyze", files={"file": ("test.csv", BytesIO(b"test"), "text/csv")})

        # Assertions
        assert response.status_code == 400
        assert "Test error" in response.json()["detail"]

    def test_upload_statement_success(self, client, mock_dependencies):
        # Prepare test data
        uploaded_file_id = str(uuid4())
        source_id = uuid4()

        # Configure mock for source service
        mock_source = MagicMock()
        mock_source.id = source_id
        mock_dependencies.source_service.get_source_by_name.return_value = mock_source

        # Configure mock for persistence service
        mock_dependencies.statement_persistence_service.persist.return_value = {"uploaded_file_id": uploaded_file_id, "transactions_saved": 10}

        # Request data
        request_data = {
            "uploaded_file_id": uploaded_file_id,
            "file_type": "CSV",
            "column_mapping": {"date": "Date", "amount": "Amount", "description": "Description"},
            "header_row_index": 0,
            "data_start_row_index": 1,
            "file_hash": "abc123",
            "source": "Test Bank",
        }

        # Expected data with source_id
        expected_data = request_data.copy()
        expected_data["source_id"] = source_id

        # Make request
        response = client.post("/api/v1/statements/upload", json=request_data)

        # Assertions
        assert response.status_code == 200
        assert response.json()["uploaded_file_id"] == uploaded_file_id
        assert response.json()["transactions_saved"] == 10
        assert response.json()["success"] is True

        # Verify source service was called correctly
        mock_dependencies.source_service.get_source_by_name.assert_called_once_with("Test Bank")

        # Verify persistence service was called with the source_id
        mock_dependencies.statement_persistence_service.persist.assert_called_once()
        call_args = mock_dependencies.statement_persistence_service.persist.call_args[0][0]
        assert call_args["source_id"] == source_id

    def test_upload_statement_error(self, client, mock_dependencies):
        # Configure mock to raise an exception
        mock_dependencies.statement_persistence_service.persist.side_effect = Exception("Test error")

        # Request data
        request_data = {
            "uploaded_file_id": str(uuid4()),
            "file_type": "CSV",
            "column_mapping": {"date": "Date", "amount": "Amount", "description": "Description"},
            "header_row_index": 0,
            "data_start_row_index": 1,
            "file_hash": "abc123",
        }

        # Make request
        response = client.post("/api/v1/statements/upload", json=request_data)

        # Assertions
        assert response.status_code == 400
        assert "Test error" in response.json()["detail"]
