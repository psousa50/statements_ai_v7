from typing import Callable, Iterator
from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.app import register_app_routes
from app.core.dependencies import InternalDependencies
from app.services.category import CategoryService
from app.services.source import SourceService
from app.services.statement_processing.statement_analyzer import StatementAnalyzerService
from app.services.statement_processing.statement_persistence import StatementPersistenceService
from app.services.transaction import TransactionService
from app.services.transaction_categorization.transaction_categorization import TransactionCategorizationService


def mocked_dependencies(
    transaction_service: TransactionService = None,
    category_service: CategoryService = None,
    source_service: SourceService = None,
    statement_analyzer_service: StatementAnalyzerService = None,
    statement_persistence_service: StatementPersistenceService = None,
    transaction_categorization_service: TransactionCategorizationService = None,
) -> InternalDependencies:
    return InternalDependencies(
        transaction_service=transaction_service or MagicMock(spec=TransactionService),
        category_service=category_service or MagicMock(spec=CategoryService),
        source_service=source_service or MagicMock(spec=SourceService),
        statement_analyzer_service=statement_analyzer_service or MagicMock(spec=StatementAnalyzerService),
        statement_persistence_service=statement_persistence_service or MagicMock(spec=StatementPersistenceService),
        transaction_categorization_service=transaction_categorization_service or MagicMock(spec=TransactionCategorizationService),
    )


def provide_mocked_dependencies(internal_dependencies: InternalDependencies) -> Callable[[], Iterator[InternalDependencies]]:
    def _provider() -> Iterator[InternalDependencies]:
        yield internal_dependencies

    return _provider


def build_client(internal_dependencies: InternalDependencies = mocked_dependencies()) -> TestClient:
    app = FastAPI()
    register_app_routes(app, provide_mocked_dependencies(internal_dependencies))
    client = TestClient(app)
    return client
