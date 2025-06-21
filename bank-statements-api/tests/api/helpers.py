from typing import Callable, Iterator
from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.adapters.repositories.background_job import SQLAlchemyBackgroundJobRepository
from app.adapters.repositories.transaction_categorization import SQLAlchemyTransactionCategorizationRepository
from app.app import register_app_routes
from app.core.dependencies import InternalDependencies
from app.services.account import AccountService
from app.services.background.background_job_service import BackgroundJobService
from app.services.category import CategoryService
from app.services.initial_balance_service import InitialBalanceService
from app.services.rule_based_categorization import RuleBasedCategorizationService
from app.services.rule_based_counterparty import RuleBasedCounterpartyService
from app.services.statement_processing.statement_analyzer import StatementAnalyzerService
from app.services.statement_processing.statement_persistence import StatementPersistenceService
from app.services.statement_processing.statement_upload import StatementUploadService
from app.services.transaction import TransactionService
from app.services.transaction_categorization.transaction_categorization import TransactionCategorizationService
from app.services.transaction_categorization_management import TransactionCategorizationManagementService
from app.services.transaction_counterparty_rule_management import TransactionCounterpartyRuleManagementService
from app.services.transaction_counterparty_service import TransactionCounterpartyService
from app.services.transaction_processing_orchestrator import TransactionProcessingOrchestrator


def mocked_dependencies(
    transaction_service: TransactionService = None,
    category_service: CategoryService = None,
    account_service: AccountService = None,
    statement_analyzer_service: StatementAnalyzerService = None,
    statement_persistence_service: StatementPersistenceService = None,
    statement_upload_service: StatementUploadService = None,
    transaction_categorization_service: TransactionCategorizationService = None,
    transaction_counterparty_service: TransactionCounterpartyService = None,
    transaction_categorization_management_service: TransactionCategorizationManagementService = None,
    transaction_counterparty_rule_management_service: TransactionCounterpartyRuleManagementService = None,
    rule_based_categorization_service: RuleBasedCategorizationService = None,
    rule_based_counterparty_service: RuleBasedCounterpartyService = None,
    background_job_service: BackgroundJobService = None,
    background_job_repository: SQLAlchemyBackgroundJobRepository = None,
    transaction_processing_orchestrator: TransactionProcessingOrchestrator = None,
    transaction_categorization_repository: SQLAlchemyTransactionCategorizationRepository = None,
    initial_balance_service: InitialBalanceService = None,
) -> InternalDependencies:
    # Create mocked transaction service with transaction_repository attribute
    if transaction_service is None:
        transaction_service = MagicMock(spec=TransactionService)
        transaction_service.transaction_repository = MagicMock()
    if initial_balance_service is None:
        initial_balance_service = MagicMock(spec=InitialBalanceService)

    return InternalDependencies(
        transaction_service=transaction_service,
        category_service=category_service or MagicMock(spec=CategoryService),
        account_service=account_service or MagicMock(spec=AccountService),
        initial_balance_service=initial_balance_service,
        statement_analyzer_service=statement_analyzer_service or MagicMock(spec=StatementAnalyzerService),
        statement_persistence_service=statement_persistence_service or MagicMock(spec=StatementPersistenceService),
        statement_upload_service=statement_upload_service or MagicMock(spec=StatementUploadService),
        transaction_categorization_service=transaction_categorization_service
        or MagicMock(spec=TransactionCategorizationService),
        transaction_counterparty_service=transaction_counterparty_service or MagicMock(spec=TransactionCounterpartyService),
        transaction_categorization_management_service=transaction_categorization_management_service
        or MagicMock(spec=TransactionCategorizationManagementService),
        transaction_counterparty_rule_management_service=transaction_counterparty_rule_management_service
        or MagicMock(spec=TransactionCounterpartyRuleManagementService),
        rule_based_categorization_service=rule_based_categorization_service or MagicMock(spec=RuleBasedCategorizationService),
        rule_based_counterparty_service=rule_based_counterparty_service or MagicMock(spec=RuleBasedCounterpartyService),
        background_job_service=background_job_service or MagicMock(spec=BackgroundJobService),
        background_job_repository=background_job_repository or MagicMock(spec=SQLAlchemyBackgroundJobRepository),
        transaction_processing_orchestrator=transaction_processing_orchestrator
        or MagicMock(spec=TransactionProcessingOrchestrator),
        transaction_categorization_repository=transaction_categorization_repository
        or MagicMock(spec=SQLAlchemyTransactionCategorizationRepository),
    )


def provide_mocked_dependencies(
    internal_dependencies: InternalDependencies,
) -> Callable[[], Iterator[InternalDependencies]]:
    def _provider() -> Iterator[InternalDependencies]:
        yield internal_dependencies

    return _provider


def build_client(
    internal_dependencies: InternalDependencies = mocked_dependencies(),
) -> TestClient:
    app = FastAPI()
    register_app_routes(app, provide_mocked_dependencies(internal_dependencies))
    client = TestClient(app)
    return client
