from unittest.mock import Mock, patch
from uuid import UUID, uuid4

import pytest

from app.api.schemas import StatementUploadRequest
from app.services.statement_processing.statement_upload import StatementUploadService


class TestStatementUploadServiceRowFilters:
    @pytest.fixture
    def user_id(self):
        return uuid4()

    @pytest.fixture
    def mock_statement_parser(self):
        return Mock()

    @pytest.fixture
    def mock_transaction_normalizer(self):
        return Mock()

    @pytest.fixture
    def mock_uploaded_file_repo(self):
        return Mock()

    @pytest.fixture
    def mock_file_analysis_metadata_repo(self):
        return Mock()

    @pytest.fixture
    def mock_transaction_rule_enhancement_service(self):
        return Mock()

    @pytest.fixture
    def mock_transaction_service(self):
        return Mock()

    @pytest.fixture
    def mock_statement_repo(self):
        return Mock()

    @pytest.fixture
    def mock_transaction_repo(self):
        return Mock()

    @pytest.fixture
    def mock_background_job_service(self):
        return Mock()

    @pytest.fixture
    def statement_upload_service(
        self,
        mock_statement_parser,
        mock_transaction_normalizer,
        mock_uploaded_file_repo,
        mock_file_analysis_metadata_repo,
        mock_transaction_rule_enhancement_service,
        mock_transaction_service,
        mock_statement_repo,
        mock_transaction_repo,
        mock_background_job_service,
    ):
        return StatementUploadService(
            statement_parser=mock_statement_parser,
            transaction_normalizer=mock_transaction_normalizer,
            uploaded_file_repo=mock_uploaded_file_repo,
            file_analysis_metadata_repo=mock_file_analysis_metadata_repo,
            transaction_rule_enhancement_service=mock_transaction_rule_enhancement_service,
            transaction_service=mock_transaction_service,
            statement_repo=mock_statement_repo,
            transaction_repo=mock_transaction_repo,
            background_job_service=mock_background_job_service,
        )

    @pytest.fixture
    def sample_upload_request_with_filters(self):
        from app.api.schemas import FilterConditionRequest, RowFilterRequest
        from app.domain.dto.statement_processing import FilterOperator, LogicalOperator

        return StatementUploadRequest(
            uploaded_file_id=str(uuid4()),
            account_id=str(uuid4()),
            column_mapping={
                "date": "Date",
                "amount": "Amount",
                "description": "Description",
            },
            header_row_index=0,
            data_start_row_index=1,
            row_filters=RowFilterRequest(
                conditions=[
                    FilterConditionRequest(
                        column_name="amount", operator=FilterOperator.GREATER_THAN, value="100", case_sensitive=False
                    )
                ],
                logical_operator=LogicalOperator.AND,
            ),
        )

    @pytest.fixture
    def sample_upload_request_without_filters(self):
        return StatementUploadRequest(
            uploaded_file_id=str(uuid4()),
            account_id=str(uuid4()),
            column_mapping={
                "date": "Date",
                "amount": "Amount",
                "description": "Description",
            },
            header_row_index=0,
            data_start_row_index=1,
        )

    def test_save_file_analysis_metadata_with_row_filters(
        self,
        statement_upload_service,
        mock_uploaded_file_repo,
        mock_file_analysis_metadata_repo,
        sample_upload_request_with_filters,
        user_id,
    ):
        """Test that row filters are saved in file analysis metadata"""
        from datetime import datetime, timezone

        from app.domain.dto.uploaded_file import UploadedFileDTO

        # Setup mocks
        uploaded_file_dto = UploadedFileDTO(
            id=sample_upload_request_with_filters.uploaded_file_id,
            filename="test.csv",
            file_type="CSV",
            created_at=datetime.now(timezone.utc),
            content=b"test,content\n1,2\n3,4",
        )
        mock_uploaded_file_repo.find_by_id.return_value = uploaded_file_dto
        mock_file_analysis_metadata_repo.find_by_hash_and_account.return_value = None

        # Mock the compute_hash and statement_parser
        with patch("app.services.common.compute_hash", return_value="test_hash"):
            with patch.object(statement_upload_service.statement_parser, "parse", return_value=Mock()):
                # Execute
                statement_upload_service._save_file_analysis_metadata(
                    uploaded_file_id=sample_upload_request_with_filters.uploaded_file_id,
                    column_mapping=sample_upload_request_with_filters.column_mapping,
                    header_row_index=sample_upload_request_with_filters.header_row_index,
                    data_start_row_index=sample_upload_request_with_filters.data_start_row_index,
                    account_id=UUID(sample_upload_request_with_filters.account_id),
                    user_id=user_id,
                    row_filters=sample_upload_request_with_filters.row_filters,
                )

                mock_file_analysis_metadata_repo.find_by_hash_and_account.assert_called_once_with(
                    "test_hash", UUID(sample_upload_request_with_filters.account_id)
                )
                mock_file_analysis_metadata_repo.save.assert_called_once_with(
                    file_hash="test_hash",
                    column_mapping=sample_upload_request_with_filters.column_mapping,
                    header_row_index=sample_upload_request_with_filters.header_row_index,
                    data_start_row_index=sample_upload_request_with_filters.data_start_row_index,
                    account_id=UUID(sample_upload_request_with_filters.account_id),
                    row_filters=sample_upload_request_with_filters.row_filters,
                )

    def test_save_file_analysis_metadata_without_row_filters(
        self,
        statement_upload_service,
        mock_uploaded_file_repo,
        mock_file_analysis_metadata_repo,
        sample_upload_request_without_filters,
        user_id,
    ):
        """Test that None row filters are handled correctly"""
        from datetime import datetime, timezone

        from app.domain.dto.uploaded_file import UploadedFileDTO

        # Setup mocks
        uploaded_file_dto = UploadedFileDTO(
            id=sample_upload_request_without_filters.uploaded_file_id,
            filename="test.csv",
            file_type="CSV",
            created_at=datetime.now(timezone.utc),
            content=b"test,content\n1,2\n3,4",
        )
        mock_uploaded_file_repo.find_by_id.return_value = uploaded_file_dto
        mock_file_analysis_metadata_repo.find_by_hash_and_account.return_value = None

        # Mock the compute_hash and statement_parser
        with patch("app.services.common.compute_hash", return_value="test_hash"):
            with patch.object(statement_upload_service.statement_parser, "parse", return_value=Mock()):
                # Execute
                statement_upload_service._save_file_analysis_metadata(
                    uploaded_file_id=sample_upload_request_without_filters.uploaded_file_id,
                    column_mapping=sample_upload_request_without_filters.column_mapping,
                    header_row_index=sample_upload_request_without_filters.header_row_index,
                    data_start_row_index=sample_upload_request_without_filters.data_start_row_index,
                    account_id=UUID(sample_upload_request_without_filters.account_id),
                    user_id=user_id,
                    row_filters=None,
                )

                mock_file_analysis_metadata_repo.find_by_hash_and_account.assert_called_once_with(
                    "test_hash", UUID(sample_upload_request_without_filters.account_id)
                )
                mock_file_analysis_metadata_repo.save.assert_called_once_with(
                    file_hash="test_hash",
                    column_mapping=sample_upload_request_without_filters.column_mapping,
                    header_row_index=sample_upload_request_without_filters.header_row_index,
                    data_start_row_index=sample_upload_request_without_filters.data_start_row_index,
                    account_id=UUID(sample_upload_request_without_filters.account_id),
                    row_filters=None,
                )

    def test_parse_statement_reuses_saved_row_filters(
        self,
        statement_upload_service,
        mock_uploaded_file_repo,
        mock_file_analysis_metadata_repo,
        sample_upload_request_without_filters,
        user_id,
    ):
        """Test that saved row filters are automatically applied when uploading the same file"""
        from datetime import datetime, timezone
        from unittest.mock import Mock, patch

        import pandas as pd

        from app.domain.dto.uploaded_file import FileAnalysisMetadataDTO

        # Setup: Mock a file upload request without filters
        upload_request = sample_upload_request_without_filters

        # Mock existing metadata with saved row filters
        saved_row_filters = [{"column_name": "Amount", "operator": "greater_than", "value": "100", "case_sensitive": False}]

        existing_metadata = FileAnalysisMetadataDTO(
            id="metadata-id",
            file_hash="test_hash",
            account_id=upload_request.account_id,
            column_mapping={"date": "Date", "amount": "Amount", "description": "Description"},
            header_row_index=0,
            data_start_row_index=1,
            created_at=datetime.now(timezone.utc),
            row_filters=saved_row_filters,
        )

        # Setup mocks
        uploaded_file_dto = Mock()
        uploaded_file_dto.content = b"Date,Amount,Description\n2023-01-01,50.00,Small\n2023-01-02,150.00,Large"
        uploaded_file_dto.file_type = "CSV"

        mock_uploaded_file_repo.find_by_id.return_value = uploaded_file_dto
        mock_file_analysis_metadata_repo.find_by_hash.return_value = existing_metadata

        # Mock the services
        raw_df = pd.DataFrame(
            {"Date": ["2023-01-01", "2023-01-02"], "Amount": ["50.00", "150.00"], "Description": ["Small", "Large"]}
        )

        # Mock normalized DataFrame (after transaction normalizer)
        normalized_df = pd.DataFrame(
            {"date": ["2023-01-01", "2023-01-02"], "amount": [50.00, 150.00], "description": ["Small", "Large"]}
        )

        with patch.object(statement_upload_service.statement_parser, "parse", return_value=raw_df):
            with patch("app.services.common.compute_hash", return_value="test_hash"):
                with patch("app.services.common.process_dataframe", return_value=raw_df):
                    with patch.object(
                        statement_upload_service.row_filter_service, "apply_filters", return_value=raw_df
                    ) as mock_apply_filters:
                        with patch.object(
                            statement_upload_service.transaction_normalizer,
                            "normalize",
                            return_value=(normalized_df, []),
                        ):
                            # Execute
                            statement_upload_service.parse_statement(user_id, upload_request)

                            # Verify that row filters were applied even though none were provided in the request
                            mock_apply_filters.assert_called_once()

                            # Verify the filter was constructed from saved metadata
                            called_args = mock_apply_filters.call_args
                            applied_filter = called_args[0][1]  # Second argument is the RowFilter

                            assert len(applied_filter.conditions) == 1
                            condition = applied_filter.conditions[0]
                            assert condition.column_name == "Amount"
                            assert condition.operator.value == "greater_than"
                            assert condition.value == "100"
