from io import BytesIO
from uuid import uuid4

from fastapi.encoders import jsonable_encoder

from app.api.schemas import StatementUploadRequest, StatementUploadResponse, StatementAnalysisResponse
from app.domain.dto.statement_processing import AnalysisResultDTO, PersistenceRequestDTO, PersistenceResultDTO

from tests.api.helpers import build_client, mocked_dependencies


class TestStatementRoutes:
    def test_analyze_statement_success(self):
        file_content = b"Date,Amount,Description\n2023-01-01,100.00,Test"
        uploaded_file_id = str(uuid4())

        internal_dependencies = mocked_dependencies()
        client = build_client(internal_dependencies)

        internal_dependencies.statement_analyzer_service.analyze.return_value = AnalysisResultDTO(
            uploaded_file_id=uploaded_file_id,
            file_type="CSV",
            column_mapping={"date": "Date", "amount": "Amount", "description": "Description"},
            header_row_index=0,
            data_start_row_index=1,
            sample_data=[["2023-01-01", 100.00, "Test"]],
        )

        response = client.post("/api/v1/statements/analyze", files={"file": ("test.csv", BytesIO(file_content), "text/csv")})

        analysis_result = StatementAnalysisResponse.model_validate(response.json())

        assert response.status_code == 200
        assert analysis_result.uploaded_file_id == uploaded_file_id
        assert analysis_result.file_type == "CSV"
        assert analysis_result.column_mapping["date"] == "Date"

        internal_dependencies.statement_analyzer_service.analyze.assert_called_once()
        args, kwargs = internal_dependencies.statement_analyzer_service.analyze.call_args
        assert kwargs["filename"] == "test.csv"
        assert kwargs["file_content"] == file_content

    def test_analyze_statement_error(self):
        internal_dependencies = mocked_dependencies()
        client = build_client(internal_dependencies)
        internal_dependencies.statement_analyzer_service.analyze.side_effect = Exception("Test error")

        response = client.post("/api/v1/statements/analyze", files={"file": ("test.csv", BytesIO(b"test"), "text/csv")})

        assert response.status_code == 400
        assert "Test error" in response.json()["detail"]

    def test_upload_statement_success(self):
        internal_dependencies = mocked_dependencies()
        client = build_client(internal_dependencies)
        uploaded_file_id = str(uuid4())
        source_id = uuid4()

        internal_dependencies.statement_persistence_service.persist.return_value = PersistenceResultDTO(
            uploaded_file_id=uploaded_file_id, transactions_saved=10
        )

        request_data = StatementUploadRequest(
            uploaded_file_id=uploaded_file_id,
            column_mapping={"date": "Date", "amount": "Amount", "description": "Description"},
            header_row_index=0,
            data_start_row_index=1,
            source_id=str(source_id),
        )

        response = client.post("/api/v1/statements/upload", json=jsonable_encoder(request_data))

        persistence_result = StatementUploadResponse.model_validate(response.json())

        assert response.status_code == 200
        assert persistence_result.uploaded_file_id == uploaded_file_id
        assert persistence_result.transactions_saved == 10
        assert persistence_result.success is True

        internal_dependencies.statement_persistence_service.persist.assert_called_once()
        call_args = internal_dependencies.statement_persistence_service.persist.call_args[0][0]
        assert isinstance(call_args, PersistenceRequestDTO)
        assert call_args.source_id == source_id

    def test_upload_statement_error(self):
        internal_dependencies = mocked_dependencies()
        client = build_client(internal_dependencies)
        internal_dependencies.statement_persistence_service.persist.side_effect = Exception("Test error")

        request_data = StatementUploadRequest(
            uploaded_file_id=str(uuid4()),
            column_mapping={"date": "Date", "amount": "Amount", "description": "Description"},
            header_row_index=0,
            data_start_row_index=1,
            source_id=str(uuid4()),
        )

        response = client.post("/api/v1/statements/upload", json=jsonable_encoder(request_data))

        assert response.status_code == 400
        assert "Test error" in response.json()["detail"]
