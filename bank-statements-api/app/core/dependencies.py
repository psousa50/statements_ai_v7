from contextlib import contextmanager
from typing import Generator

from sqlalchemy.orm import Session

from app.adapters.categorizers.simple_transaction_categorizer import SimpleTransactionCategorizer
from app.adapters.repositories.category import SQLAlchemyCategoryRepository
from app.adapters.repositories.source import SQLAlchemySourceRepository
from app.adapters.repositories.transaction import SQLAlchemyTransactionRepository
from app.adapters.repositories.uploaded_file import SQLAlchemyFileAnalysisMetadataRepository, SQLAlchemyUploadedFileRepository
from app.ai.gemini_ai import GeminiAI
from app.ai.llm_client import LLMClient
from app.core.database import SessionLocal
from app.services.category import CategoryService
from app.services.source import SourceService
from app.services.statement_processing.file_type_detector import StatementFileTypeDetector
from app.services.schema_detection.heuristic_schema_detector import HeuristicSchemaDetector
from app.services.statement_processing.statement_analyzer import StatementAnalyzerService
from app.services.statement_processing.statement_parser import StatementParser
from app.services.statement_processing.statement_persistence import StatementPersistenceService
from app.services.statement_processing.transaction_normalizer import TransactionNormalizer
from app.services.transaction import TransactionService
from app.services.transaction_categorization import TransactionCategorizationService


class ExternalDependencies:
    def __init__(self, db: Session = SessionLocal(), llm_client: LLMClient = GeminiAI()):
        self.db = db
        self.llm_client = llm_client

    def cleanup(self):
        if self.db is not None:
            self.db.close()
            self.db = None


class InternalDependencies:
    def __init__(
        self,
        transaction_service: TransactionService,
        category_service: CategoryService,
        source_service: SourceService,
        statement_analyzer_service: StatementAnalyzerService,
        statement_persistence_service: StatementPersistenceService,
        transaction_categorization_service: TransactionCategorizationService,
    ):
        self.transaction_service = transaction_service
        self.category_service = category_service
        self.source_service = source_service
        self.statement_analyzer_service = statement_analyzer_service
        self.statement_persistence_service = statement_persistence_service
        self.transaction_categorization_service = transaction_categorization_service


def build_external_dependencies() -> ExternalDependencies:
    return ExternalDependencies()


def build_internal_dependencies(external: ExternalDependencies) -> InternalDependencies:
    transaction_repo = SQLAlchemyTransactionRepository(external.db)
    category_repo = SQLAlchemyCategoryRepository(external.db)
    source_repo = SQLAlchemySourceRepository(external.db)
    uploaded_file_repo = SQLAlchemyUploadedFileRepository(external.db)
    file_analysis_metadata_repo = SQLAlchemyFileAnalysisMetadataRepository(external.db)

    file_type_detector = StatementFileTypeDetector()
    statement_parser = StatementParser()
    # schema_detector = LLMSchemaDetector(external.llm_client)
    schema_detector = HeuristicSchemaDetector()
    transaction_normalizer = TransactionNormalizer()
    category_service = CategoryService(category_repo)
    source_service = SourceService(source_repo)
    transaction_service = TransactionService(transaction_repo)

    transaction_categorizer = SimpleTransactionCategorizer(category_repo)
    transaction_categorization_service = TransactionCategorizationService(
        transaction_repository=transaction_repo,
        transaction_categorizer=transaction_categorizer,
    )

    statement_analyzer_service = StatementAnalyzerService(
        file_type_detector=file_type_detector,
        statement_parser=statement_parser,
        schema_detector=schema_detector,
        transaction_normalizer=transaction_normalizer,
        uploaded_file_repo=uploaded_file_repo,
        file_analysis_metadata_repo=file_analysis_metadata_repo,
    )

    statement_persistence_service = StatementPersistenceService(
        statement_parser=statement_parser,
        transaction_normalizer=transaction_normalizer,
        transaction_repo=transaction_repo,
        uploaded_file_repo=uploaded_file_repo,
        file_analysis_metadata_repo=file_analysis_metadata_repo,
    )

    return InternalDependencies(
        transaction_service=transaction_service,
        category_service=category_service,
        source_service=source_service,
        statement_analyzer_service=statement_analyzer_service,
        statement_persistence_service=statement_persistence_service,
        transaction_categorization_service=transaction_categorization_service,
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
    with get_dependencies() as (_external, internal):
        yield internal
