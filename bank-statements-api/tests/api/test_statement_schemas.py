from uuid import uuid4

from app.api.schemas import StatementAnalysisResponse, StatementUploadRequest, StatementUploadResponse


class TestStatementSchemas:
    def test_statement_analysis_response_schema(self):
        uploaded_file_id = str(uuid4())
        file_hash = "abc123"

        data = {
            "uploaded_file_id": uploaded_file_id,
            "file_type": "CSV",
            "column_mapping": {"date": "Date", "amount": "Amount", "description": "Description"},
            "header_row_index": 0,
            "data_start_row_index": 1,
            "sample_data": [{"date": "2023-01-01", "amount": 100.00, "description": "Test transaction"}],
            "file_hash": file_hash,
        }

        response = StatementAnalysisResponse(**data)

        assert response.uploaded_file_id == uploaded_file_id
        assert response.file_type == "CSV"
        assert response.column_mapping["date"] == "Date"
        assert response.column_mapping["amount"] == "Amount"
        assert response.column_mapping["description"] == "Description"
        assert response.header_row_index == 0
        assert response.data_start_row_index == 1
        assert len(response.sample_data) == 1
        assert response.file_hash == file_hash

    def test_statement_upload_request_schema(self):
        uploaded_file_id = str(uuid4())
        file_hash = "abc123"

        data = {
            "uploaded_file_id": uploaded_file_id,
            "file_type": "CSV",
            "column_mapping": {"date": "Date", "amount": "Amount", "description": "Description"},
            "header_row_index": 0,
            "data_start_row_index": 1,
            "file_hash": file_hash,
            "source": "Test Bank",
        }

        request = StatementUploadRequest(**data)

        assert request.uploaded_file_id == uploaded_file_id
        assert request.file_type == "CSV"
        assert request.column_mapping["date"] == "Date"
        assert request.column_mapping["amount"] == "Amount"
        assert request.column_mapping["description"] == "Description"
        assert request.header_row_index == 0
        assert request.data_start_row_index == 1
        assert request.file_hash == file_hash
        assert request.source == "Test Bank"

    def test_statement_upload_response_schema(self):
        uploaded_file_id = str(uuid4())

        data = {"uploaded_file_id": uploaded_file_id, "transactions_saved": 10, "success": True, "message": "Successfully saved 10 transactions"}

        response = StatementUploadResponse(**data)

        assert response.uploaded_file_id == uploaded_file_id
        assert response.transactions_saved == 10
        assert response.success is True
        assert response.message == "Successfully saved 10 transactions"
