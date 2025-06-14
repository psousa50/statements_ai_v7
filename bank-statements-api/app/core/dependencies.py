import logging
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy.orm import Session

from app.adapters.repositories.background_job import SQLAlchemyBackgroundJobRepository
from app.adapters.repositories.category import SQLAlchemyCategoryRepository
from app.adapters.repositories.source import SQLAlchemySourceRepository
from app.adapters.repositories.transaction import SQLAlchemyTransactionRepository
from app.adapters.repositories.transaction_categorization import SQLAlchemyTransactionCategorizationRepository
from app.adapters.repositories.uploaded_file import SQLAlchemyFileAnalysisMetadataRepository, SQLAlchemyUploadedFileRepository
from app.ai.gemini_ai import GeminiAI
from app.ai.llm_client import LLMClient
from app.core.database import SessionLocal
from app.services.background.background_job_service import BackgroundJobService
from app.services.category import CategoryService
from app.services.rule_based_categorization import RuleBasedCategorizationService
from app.services.schema_detection.heuristic_schema_detector import HeuristicSchemaDetector
from app.services.source import SourceService
from app.services.statement_processing.file_type_detector import StatementFileTypeDetector
from app.services.statement_processing.statement_analyzer import StatementAnalyzerService
from app.services.statement_processing.statement_parser import StatementParser
from app.services.statement_processing.statement_persistence import StatementPersistenceService
from app.services.statement_processing.statement_upload import StatementUploadService
from app.services.statement_processing.transaction_normalizer import TransactionNormalizer
from app.services.transaction import TransactionService
from app.services.transaction_categorization.llm_transaction_categorizer import LLMTransactionCategorizer
from app.services.transaction_categorization.transaction_categorization import TransactionCategorizationService
from app.services.transaction_categorization_management import TransactionCategorizationManagementService
from app.services.transaction_processing_orchestrator import TransactionProcessingOrchestrator

logger = logging.getLogger(__name__)


class ExternalDependencies:
    def __init__(self, db: Optional[Session] = None, llm_client: Optional[LLMClient] = None):
        self.db: Session = db if db is not None else SessionLocal()
        self.llm_client: LLMClient = llm_client if llm_client is not None else GeminiAI()

    def cleanup(self):
        self.db.close()


class InternalDependencies:
    def __init__(
        self,
        transaction_service: TransactionService,
        category_service: CategoryService,
        source_service: SourceService,
        statement_analyzer_service: StatementAnalyzerService,
        statement_persistence_service: StatementPersistenceService,
        statement_upload_service: StatementUploadService,
        transaction_categorization_service: TransactionCategorizationService,
        transaction_categorization_management_service: TransactionCategorizationManagementService,
        rule_based_categorization_service: RuleBasedCategorizationService,
        background_job_service: BackgroundJobService,
        background_job_repository: SQLAlchemyBackgroundJobRepository,
        transaction_processing_orchestrator: TransactionProcessingOrchestrator,
        transaction_categorization_repository: SQLAlchemyTransactionCategorizationRepository,
    ):
        self.transaction_service = transaction_service
        self.category_service = category_service
        self.source_service = source_service
        self.statement_analyzer_service = statement_analyzer_service
        self.statement_persistence_service = statement_persistence_service
        self.statement_upload_service = statement_upload_service
        self.transaction_categorization_service = transaction_categorization_service
        self.transaction_categorization_management_service = transaction_categorization_management_service
        self.rule_based_categorization_service = rule_based_categorization_service
        self.background_job_service = background_job_service
        self.background_job_repository = background_job_repository
        self.transaction_processing_orchestrator = transaction_processing_orchestrator
        self.transaction_categorization_repository = transaction_categorization_repository


def build_external_dependencies() -> ExternalDependencies:
    return ExternalDependencies()


def build_internal_dependencies(external: ExternalDependencies) -> InternalDependencies:
    transaction_repo = SQLAlchemyTransactionRepository(external.db)
    category_repo = SQLAlchemyCategoryRepository(external.db)
    source_repo = SQLAlchemySourceRepository(external.db)
    uploaded_file_repo = SQLAlchemyUploadedFileRepository(external.db)
    file_analysis_metadata_repo = SQLAlchemyFileAnalysisMetadataRepository(external.db)
    transaction_categorization_repo = SQLAlchemyTransactionCategorizationRepository(external.db)
    background_job_repo = SQLAlchemyBackgroundJobRepository(external.db)

    file_type_detector = StatementFileTypeDetector()
    statement_parser = StatementParser()
    # schema_detector = LLMSchemaDetector(external.llm_client)
    schema_detector = HeuristicSchemaDetector()
    transaction_normalizer = TransactionNormalizer()
    category_service = CategoryService(category_repo)
    source_service = SourceService(source_repo)
    transaction_service = TransactionService(transaction_repo)

    rule_based_categorization_service = RuleBasedCategorizationService(
        repository=transaction_categorization_repo, enable_cache=True
    )

    background_job_service = BackgroundJobService(background_job_repo)

    transaction_processing_orchestrator = TransactionProcessingOrchestrator(
        rule_based_categorization_service=rule_based_categorization_service,
        background_job_service=background_job_service,
        transaction_repository=transaction_repo,
    )

    # transaction_categorizer = SimpleTransactionCategorizer(category_repo)
    transaction_categorizer = LLMTransactionCategorizer(category_repo, external.llm_client)
    transaction_categorization_service = TransactionCategorizationService(
        transaction_repository=transaction_repo,
        transaction_categorizer=transaction_categorizer,
        transaction_categorization_repository=transaction_categorization_repo,
    )

    transaction_categorization_management_service = TransactionCategorizationManagementService(
        repository=transaction_categorization_repo,
    )

    statement_analyzer_service = StatementAnalyzerService(
        file_type_detector=file_type_detector,
        statement_parser=statement_parser,
        schema_detector=schema_detector,
        transaction_normalizer=transaction_normalizer,
        uploaded_file_repo=uploaded_file_repo,
        file_analysis_metadata_repo=file_analysis_metadata_repo,
        transaction_repo=transaction_repo,
    )

    statement_persistence_service = StatementPersistenceService(
        statement_parser=statement_parser,
        transaction_normalizer=transaction_normalizer,
        transaction_repo=transaction_repo,
        uploaded_file_repo=uploaded_file_repo,
        file_analysis_metadata_repo=file_analysis_metadata_repo,
    )

    statement_upload_service = StatementUploadService(
        statement_parser=statement_parser,
        transaction_normalizer=transaction_normalizer,
        uploaded_file_repo=uploaded_file_repo,
        file_analysis_metadata_repo=file_analysis_metadata_repo,
        transaction_processing_orchestrator=transaction_processing_orchestrator,
        statement_persistence_service=statement_persistence_service,
        background_job_service=background_job_service,
    )

    return InternalDependencies(
        transaction_service=transaction_service,
        category_service=category_service,
        source_service=source_service,
        statement_analyzer_service=statement_analyzer_service,
        statement_persistence_service=statement_persistence_service,
        statement_upload_service=statement_upload_service,
        transaction_categorization_service=transaction_categorization_service,
        transaction_categorization_management_service=transaction_categorization_management_service,
        rule_based_categorization_service=rule_based_categorization_service,
        background_job_service=background_job_service,
        background_job_repository=background_job_repo,
        transaction_processing_orchestrator=transaction_processing_orchestrator,
        transaction_categorization_repository=transaction_categorization_repo,
    )


@contextmanager
def get_dependencies() -> Generator[tuple[ExternalDependencies, InternalDependencies], None, None]:
    external = build_external_dependencies()
    internal = build_internal_dependencies(external)
    try:
        yield external, internal
    finally:
        external.cleanup()


def provide_dependencies() -> Generator[InternalDependencies, None, None]:
    with get_dependencies() as (_, internal):
        yield internal
