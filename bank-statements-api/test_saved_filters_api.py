#!/usr/bin/env python3
"""
Quick test script to verify that saved row filters are returned in API responses.
"""

import os
import tempfile
from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.routes.statements import register_statement_routes
from app.core.database import Base
from app.core.dependencies import ExternalDependencies, build_internal_dependencies
from app.domain.models.account import Account
from app.domain.models.uploaded_file import FileAnalysisMetadata


def test_saved_filters_in_api_response():
    """Test that saved row filters are returned in the analysis API response."""

    # Setup test database
    database_url = os.environ.get("TEST_DATABASE_URL")
    if not database_url:
        print("TEST_DATABASE_URL environment variable not set")
        return

    engine = create_engine(database_url)
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Mock LLM client
        llm_client = MagicMock()
        llm_client.generate.return_value = """
        {
            "column_mapping": {
                "date": "Date",
                "amount": "Amount", 
                "description": "Description"
            },
            "header_row_index": 0,
            "data_start_row_index": 1
        }
        """

        # Build dependencies
        dependencies = build_internal_dependencies(ExternalDependencies(db=session, llm_client=llm_client))

        # Create FastAPI app with statement routes
        app = FastAPI()
        register_statement_routes(app, lambda: iter([dependencies]))
        client = TestClient(app)

        # Test CSV content
        csv_content = b"""Date,Amount,Description
2023-01-01,50.00,Small Purchase
2023-01-02,150.00,Large Purchase
2023-01-03,25.00,Tiny Purchase
2023-01-04,300.00,Big Purchase"""

        # Step 1: Upload file for first time (this will create metadata without filters)
        with tempfile.NamedTemporaryFile(suffix=".csv") as temp_file:
            temp_file.write(csv_content)
            temp_file.flush()

            with open(temp_file.name, "rb") as f:
                response = client.post("/api/v1/statements/analyze", files={"file": ("test.csv", f, "text/csv")})

        if response.status_code != 200:
            print(f"Error: {response.status_code}, {response.text}")
            return
        initial_data = response.json()
        print("Initial response (no saved filters):")
        print(f"  saved_row_filters: {initial_data.get('saved_row_filters')}")
        assert initial_data["saved_row_filters"] is None

        # Step 2: Manually add saved row filters to the file analysis metadata
        # Find the metadata record
        metadata = session.query(FileAnalysisMetadata).first()
        assert metadata is not None

        # Add saved row filters
        saved_filters = [{"column_name": "Amount", "operator": "greater_than", "value": "100", "case_sensitive": False}]
        metadata.row_filters = saved_filters
        session.commit()

        # Step 3: Upload the same file again (should return saved filters)
        with tempfile.NamedTemporaryFile(suffix=".csv") as temp_file:
            temp_file.write(csv_content)
            temp_file.flush()

            with open(temp_file.name, "rb") as f:
                response = client.post("/api/v1/statements/analyze", files={"file": ("test.csv", f, "text/csv")})

        if response.status_code != 200:
            print(f"Error: {response.status_code}, {response.text}")
            return
        data = response.json()
        print("\nSecond response (with saved filters):")
        print(f"  saved_row_filters: {data.get('saved_row_filters')}")

        # Verify saved filters are returned
        assert data["saved_row_filters"] is not None
        assert len(data["saved_row_filters"]) == 1
        filter_data = data["saved_row_filters"][0]
        assert filter_data["column_name"] == "Amount"
        assert filter_data["operator"] == "greater_than"
        assert filter_data["value"] == "100"
        assert filter_data["case_sensitive"] is False

        print("\n✅ Test passed! Saved row filters are correctly returned in API response.")

    finally:
        session.close()


if __name__ == "__main__":
    test_saved_filters_in_api_response()
