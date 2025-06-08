import io

import pandas as pd
import pytest

from app.services.schema_detection.heuristic_schema_detector import HeuristicSchemaDetector


def unindent(content: str) -> str:
    return "\n".join([line.strip() for line in content.split("\n")])


class TestHeuristicSchemaDetector:
    @pytest.fixture
    def detector(self):
        return HeuristicSchemaDetector()

    def test_heuristic_schema_detector(self, detector):
        content = """
            Date,Description,Amount
            2023-01-01,Coffee Shop,10.50
            2023-01-02,Grocery Store,45.20
            2023-01-03,Gas Station,35.75
        """
        content = unindent(content)
        data = pd.read_csv(io.StringIO(content))
        conversion_model = detector.detect_schema(data)

        assert conversion_model.header_row_index == 0
        assert conversion_model.data_start_row_index == 1
        assert conversion_model.column_mapping == {
            "date": "Date",
            "description": "Description",
            "amount": "Amount",
        }

    def test_heuristic_schema_detector_complex_case_1(self, detector):
        content = """
            Account: 12345678,John Doe,January 2023,1/1
            Data,Descricao,Valor,Saldo
            2023-01-01,Coffee Shop,10.50,1000.00
            2023-01-02,Grocery Store,45.20,954.80
            2023-01-03,Gas Station,35.75,919.05
        """
        content = unindent(content)
        data = pd.read_csv(io.StringIO(content))
        conversion_model = detector.detect_schema(data)

        assert conversion_model.header_row_index == 1
        assert conversion_model.data_start_row_index == 2
        assert conversion_model.column_mapping == {
            "date": "Data",
            "description": "Descricao",
            "amount": "Valor",
        }

    def test_heuristic_schema_detector_complex_case_2(self, detector):
        content = """
            Data,Valor,Descricao
            2023-01-01,100.00,Deposit
            2023-01-02,-50.00,Withdrawal
            2023-01-03,25.50,Refund
        """
        content = unindent(content)
        data = pd.read_csv(io.StringIO(content))
        conversion_model = detector.detect_schema(data)

        assert conversion_model.header_row_index == 0
        assert conversion_model.data_start_row_index == 1
        assert conversion_model.column_mapping == {
            "date": "Data",
            "description": "Descricao",
            "amount": "Valor",
        }

    def test_heuristic_schema_detector_complex_case_3(self, detector):
        content = """
            HISTÓRICO DE CONTA NÚMERO 45621121287,,,,
            Moeda:,EUR,,,
            ,,,,
            Tipo:,Todos,,,
            Data de:,01/12/2024,,,
            Data até:,10/05/2025,,,
            ,,,,
            Data Lanc.,Data Valor,Descrição,Valor,Saldo
            2023-01-01,2023-01-02,Deposit,100.00,1000.00
            2023-01-02,2023-01-03,Withdrawal,-50.00,950.00
            2023-01-03,2023-01-04,Refund,25.50,975.50
        """
        content = unindent(content)

        data = pd.read_csv(io.StringIO(content))
        conversion_model = detector.detect_schema(data)

        assert conversion_model.header_row_index == 7
        assert conversion_model.data_start_row_index == 8
        assert conversion_model.column_mapping == {
            "date": "Data Lanc.",
            "description": "Descrição",
            "amount": "Valor",
        }
