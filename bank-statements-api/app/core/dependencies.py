import logging
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy.orm import Session

from app.adapters.repositories.account import SQLAlchemyAccountRepository
from app.adapters.repositories.background_job import SQLAlchemyBackgroundJobRepository
from app.adapters.repositories.category import SQLAlchemyCategoryRepository
from app.adapters.repositories.enhancement_rule import SQLAlchemyEnhancementRuleRepository
from app.adapters.repositories.initial_balance import SQLAlchemyInitialBalanceRepository
from app.adapters.repositories.statement import SqlAlchemyStatementRepository
from app.adapters.repositories.transaction import SQLAlchemyTransactionRepository
from app.adapters.repositories.uploaded_file import SQLAlchemyFileAnalysisMetadataRepository, SQLAlchemyUploadedFileRepository
from app.ai.gemini_ai import GeminiAI
from app.ai.llm_client import LLMClient
from app.core.database import SessionLocal
from app.services.account import AccountService
from app.services.background.background_job_service import BackgroundJobService
from app.services.category import CategoryService
from app.services.enhancement_rule_management import EnhancementRuleManagementService
from app.services.initial_balance_service import InitialBalanceService
from app.services.statement import StatementService
from app.services.schema_detection.heuristic_schema_detector import HeuristicSchemaDetector
from app.services.statement_processing.file_type_detector import StatementFileTypeDetector
from app.services.statement_processing.statement_analyzer import StatementAnalyzerService
from app.services.statement_processing.statement_parser import StatementParser
from app.services.statement_processing.statement_upload import StatementUploadService
from app.services.statement_processing.transaction_normalizer import TransactionNormalizer
from app.services.statement_processing.row_filter_service import RowFilterService
from app.services.transaction import TransactionService
from app.services.transaction_enhancement import TransactionEnhancer
from app.services.transaction_rule_enhancement import TransactionRuleEnhancementService

logger = logging.getLogger(__name__)


class ExternalDependencies:
    def __init__(
        self,
        db: Optional[Session] = None,
        llm_client: Optional[LLMClient] = None,
    ):
        self.db: Session = db if db is not None else SessionLocal()
        self.llm_client: LLMClient = llm_client if llm_client is not None else GeminiAI()

    def cleanup(self):
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
        finally:
            self.db.close()


class InternalDependencies:
    def __init__(
        self,
        transaction_service: TransactionService,
        category_service: CategoryService,
        account_service: AccountService,
        initial_balance_service: InitialBalanceService,
        statement_service: StatementService,
        statement_analyzer_service: StatementAnalyzerService,
        statement_upload_service: StatementUploadService,
        enhancement_rule_management_service: EnhancementRuleManagementService,
        background_job_service: BackgroundJobService,
        background_job_repository: SQLAlchemyBackgroundJobRepository,
        statement_repo: SqlAlchemyStatementRepository,
        transaction_repo: SQLAlchemyTransactionRepository,
    ):
        self.transaction_service = transaction_service
        self.category_service = category_service
        self.account_service = account_service
        self.initial_balance_service = initial_balance_service
        self.statement_service = statement_service
        self.statement_analyzer_service = statement_analyzer_service
        self.statement_upload_service = statement_upload_service
        self.enhancement_rule_management_service = enhancement_rule_management_service
        self.background_job_service = background_job_service
        self.background_job_repository = background_job_repository
        self.statement_repo = statement_repo
        self.transaction_repo = transaction_repo


def build_external_dependencies() -> ExternalDependencies:
    return ExternalDependencies()


def build_internal_dependencies(
    external: ExternalDependencies,
) -> InternalDependencies:
    transaction_repo = SQLAlchemyTransactionRepository(external.db)
    category_repo = SQLAlchemyCategoryRepository(external.db)
    account_repo = SQLAlchemyAccountRepository(external.db)
    initial_balance_repo = SQLAlchemyInitialBalanceRepository(external.db)
    uploaded_file_repo = SQLAlchemyUploadedFileRepository(external.db)
    file_analysis_metadata_repo = SQLAlchemyFileAnalysisMetadataRepository(external.db)
    statement_repo = SqlAlchemyStatementRepository(external.db)
    enhancement_rule_repo = SQLAlchemyEnhancementRuleRepository(external.db)
    background_job_repo = SQLAlchemyBackgroundJobRepository(external.db)

    file_type_detector = StatementFileTypeDetector()
    statement_parser = StatementParser()
    # schema_detector = LLMSchemaDetector(external.llm_client)
    schema_detector = HeuristicSchemaDetector()
    transaction_normalizer = TransactionNormalizer()
    category_service = CategoryService(category_repo)
    account_service = AccountService(account_repo)
    initial_balance_service = InitialBalanceService(initial_balance_repo)
    statement_service = StatementService(statement_repo, transaction_repo)
    transaction_service = TransactionService(
        transaction_repo,
        initial_balance_repo,
        enhancement_rule_repo,
    )

    transaction_enhancer = TransactionEnhancer()

    background_job_service = BackgroundJobService(background_job_repo)

    transaction_rule_enhancement_service = TransactionRuleEnhancementService(
        transaction_enhancer=transaction_enhancer,
        enhancement_rule_repository=enhancement_rule_repo,
    )

    enhancement_rule_management_service = EnhancementRuleManagementService(
        enhancement_rule_repository=enhancement_rule_repo,
        category_repository=category_repo,
        account_repository=account_repo,
        transaction_repository=transaction_repo,
    )

    # Row filter service for filtering statement rows
    row_filter_service = RowFilterService()

    statement_analyzer_service = StatementAnalyzerService(
        file_type_detector=file_type_detector,
        statement_parser=statement_parser,
        schema_detector=schema_detector,
        transaction_normalizer=transaction_normalizer,
        uploaded_file_repo=uploaded_file_repo,
        file_analysis_metadata_repo=file_analysis_metadata_repo,
        transaction_repo=transaction_repo,
        row_filter_service=row_filter_service,
    )

    statement_upload_service = StatementUploadService(
        statement_parser=statement_parser,
        transaction_normalizer=transaction_normalizer,
        uploaded_file_repo=uploaded_file_repo,
        file_analysis_metadata_repo=file_analysis_metadata_repo,
        transaction_rule_enhancement_service=transaction_rule_enhancement_service,
        statement_repo=statement_repo,
        transaction_repo=transaction_repo,
        background_job_service=background_job_service,
        row_filter_service=row_filter_service,
    )

    return InternalDependencies(
        transaction_service=transaction_service,
        category_service=category_service,
        account_service=account_service,
        initial_balance_service=initial_balance_service,
        statement_service=statement_service,
        statement_analyzer_service=statement_analyzer_service,
        statement_upload_service=statement_upload_service,
        enhancement_rule_management_service=enhancement_rule_management_service,
        background_job_service=background_job_service,
        background_job_repository=background_job_repo,
        statement_repo=statement_repo,
        transaction_repo=transaction_repo,
    )


@contextmanager
def get_dependencies() -> (
    Generator[
        tuple[ExternalDependencies, InternalDependencies],
        None,
        None,
    ]
):
    external = build_external_dependencies()
    internal = build_internal_dependencies(external)
    try:
        yield external, internal
    finally:
        external.cleanup()


def provide_dependencies() -> Generator[InternalDependencies, None, None]:
    with get_dependencies() as (_, internal):
        yield internal


def get_internal_dependencies() -> Generator[InternalDependencies, None, None]:
    """FastAPI dependency function for getting internal dependencies."""
    with get_dependencies() as (_, internal):
        yield internal
