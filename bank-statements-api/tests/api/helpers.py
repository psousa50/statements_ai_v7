from typing import Callable, Iterator
from unittest.mock import MagicMock
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.adapters.repositories.account import SQLAlchemyAccountRepository
from app.adapters.repositories.background_job import SQLAlchemyBackgroundJobRepository
from app.adapters.repositories.category import SQLAlchemyCategoryRepository
from app.adapters.repositories.enhancement_rule import SQLAlchemyEnhancementRuleRepository
from app.adapters.repositories.filter_preset import SQLAlchemyFilterPresetRepository
from app.adapters.repositories.saved_filter import SQLAlchemySavedFilterRepository
from app.adapters.repositories.statement import SqlAlchemyStatementRepository
from app.adapters.repositories.transaction import SQLAlchemyTransactionRepository
from app.api.routes.auth import require_current_user
from app.app import register_app_routes
from app.core.dependencies import InternalDependencies
from app.domain.models.user import User
from app.services.account import AccountService
from app.services.ai import LLMRuleCategorizer, LLMRuleCounterparty
from app.services.ai.llm_category_generator import LLMCategoryGenerator
from app.services.background.background_job_service import BackgroundJobService
from app.services.category import CategoryService
from app.services.description_group import DescriptionGroupService
from app.services.enhancement_rule_management import EnhancementRuleManagementService
from app.services.initial_balance_service import InitialBalanceService
from app.services.recurring_expense_analyzer import RecurringExpenseAnalyzer
from app.services.statement import StatementService
from app.services.statement_processing.statement_analyzer import StatementAnalyzerService
from app.services.statement_processing.statement_upload import StatementUploadService
from app.services.transaction import TransactionService
from app.services.transaction_enhancement import TransactionEnhancer

TEST_USER_ID = uuid4()


def get_test_user() -> User:
    return User(
        id=TEST_USER_ID,
        email="test@example.com",
        name="Test User",
        oauth_provider="google",
        oauth_id="test-oauth-id",
    )


def mocked_dependencies(
    transaction_service: TransactionService = None,
    category_service: CategoryService = None,
    account_service: AccountService = None,
    statement_analyzer_service: StatementAnalyzerService = None,
    statement_upload_service: StatementUploadService = None,
    enhancement_rule_management_service: EnhancementRuleManagementService = None,
    background_job_service: BackgroundJobService = None,
    background_job_repository: SQLAlchemyBackgroundJobRepository = None,
    initial_balance_service: InitialBalanceService = None,
    statement_service: StatementService = None,
    statement_repo: SqlAlchemyStatementRepository = None,
    transaction_repo: SQLAlchemyTransactionRepository = None,
    enhancement_rule_repository: SQLAlchemyEnhancementRuleRepository = None,
    transaction_enhancer: TransactionEnhancer = None,
    category_repository: SQLAlchemyCategoryRepository = None,
    account_repository: SQLAlchemyAccountRepository = None,
    recurring_expense_analyzer: RecurringExpenseAnalyzer = None,
    description_group_service: DescriptionGroupService = None,
    saved_filter_repository: SQLAlchemySavedFilterRepository = None,
    filter_preset_repository: SQLAlchemyFilterPresetRepository = None,
    llm_rule_categorizer: LLMRuleCategorizer = None,
    llm_rule_counterparty: LLMRuleCounterparty = None,
    llm_category_generator: LLMCategoryGenerator = None,
) -> InternalDependencies:
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
        statement_service=statement_service or MagicMock(spec=StatementService),
        statement_analyzer_service=statement_analyzer_service or MagicMock(spec=StatementAnalyzerService),
        statement_upload_service=statement_upload_service or MagicMock(spec=StatementUploadService),
        enhancement_rule_management_service=enhancement_rule_management_service
        or MagicMock(spec=EnhancementRuleManagementService),
        background_job_service=background_job_service or MagicMock(spec=BackgroundJobService),
        background_job_repository=background_job_repository or MagicMock(spec=SQLAlchemyBackgroundJobRepository),
        statement_repo=statement_repo or MagicMock(spec=SqlAlchemyStatementRepository),
        transaction_repo=transaction_repo or MagicMock(spec=SQLAlchemyTransactionRepository),
        enhancement_rule_repository=enhancement_rule_repository or MagicMock(spec=SQLAlchemyEnhancementRuleRepository),
        transaction_enhancer=transaction_enhancer or MagicMock(spec=TransactionEnhancer),
        category_repository=category_repository or MagicMock(spec=SQLAlchemyCategoryRepository),
        account_repository=account_repository or MagicMock(spec=SQLAlchemyAccountRepository),
        recurring_expense_analyzer=recurring_expense_analyzer or MagicMock(spec=RecurringExpenseAnalyzer),
        description_group_service=description_group_service or MagicMock(spec=DescriptionGroupService),
        saved_filter_repository=saved_filter_repository or MagicMock(spec=SQLAlchemySavedFilterRepository),
        filter_preset_repository=filter_preset_repository or MagicMock(spec=SQLAlchemyFilterPresetRepository),
        llm_rule_categorizer=llm_rule_categorizer or MagicMock(spec=LLMRuleCategorizer),
        llm_rule_counterparty=llm_rule_counterparty or MagicMock(spec=LLMRuleCounterparty),
        llm_category_generator=llm_category_generator or MagicMock(spec=LLMCategoryGenerator),
    )


def provide_mocked_dependencies(
    internal_dependencies: InternalDependencies,
) -> Callable[[], Iterator[InternalDependencies]]:
    def _provider() -> Iterator[InternalDependencies]:
        yield internal_dependencies

    return _provider


def build_client(
    internal_dependencies: InternalDependencies = None,
    test_user: User = None,
) -> TestClient:
    if internal_dependencies is None:
        internal_dependencies = mocked_dependencies()
    if test_user is None:
        test_user = get_test_user()

    app = FastAPI()
    register_app_routes(
        app,
        provide_mocked_dependencies(internal_dependencies),
    )
    app.dependency_overrides[require_current_user] = lambda: test_user
    client = TestClient(app)
    return client
