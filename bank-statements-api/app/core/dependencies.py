from contextlib import contextmanager
from typing import Iterator

from sqlalchemy.orm import Session

from app.adapters.repositories.category import SQLAlchemyCategoryRepository
from app.adapters.repositories.transaction import SQLAlchemyTransactionRepository
from app.adapters.repositories.uploaded_file import SQLAlchemyUploadedFileRepository, SQLAlchemyFileAnalysisMetadataRepository
from app.core.database import SessionLocal
from app.services.category import CategoryService
from app.services.transaction import TransactionService
from app.services.statement_processing.file_type_detector import StatementFileTypeDetector
from app.services.statement_processing.statement_parser import StatementParser
from app.services.statement_processing.schema_detector import SchemaDetector
from app.services.statement_processing.transaction_normalizer import TransactionNormalizer
from app.services.statement_processing.statement_analyzer import StatementAnalyzerService
from app.services.statement_processing.statement_persistence import StatementPersistenceService


class ExternalDependencies:
    """Container for external dependencies like database connections, external APIs, etc."""

    def __init__(self, db_factory):
        """
        Initialize with a database session factory.

        Args:
            db_factory: A callable that returns a database session
        """
        self._db_factory = db_factory
        self._db = None

    @property
    def db(self) -> Session:
        # Always return a new session
        return self._db_factory()

    def cleanup(self):
        """Clean up resources."""
        if self._db is not None:
            self._db.close()
            self._db = None


class InternalDependencies:
    """Container for internal dependencies like services, repositories, etc."""

    def __init__(
        self, 
        transaction_service: TransactionService, 
        category_service: CategoryService,
        statement_analyzer_service: StatementAnalyzerService,
        statement_persistence_service: StatementPersistenceService
    ):
        self.transaction_service = transaction_service
        self.category_service = category_service
        self.statement_analyzer_service = statement_analyzer_service
        self.statement_persistence_service = statement_persistence_service


def get_db_session() -> Session:
    """Create a new database session."""
    return SessionLocal()


def build_external_dependencies() -> ExternalDependencies:
    """Build external dependencies for the application."""
    return ExternalDependencies(db_factory=get_db_session)


def build_internal_dependencies(external: ExternalDependencies) -> InternalDependencies:
    """Build internal dependencies using external dependencies."""
    # Create repositories
    transaction_repo = SQLAlchemyTransactionRepository(external.db)
    category_repo = SQLAlchemyCategoryRepository(external.db)
    uploaded_file_repo = SQLAlchemyUploadedFileRepository(external.db)
    file_analysis_metadata_repo = SQLAlchemyFileAnalysisMetadataRepository(external.db)

    # Create statement processing components
    file_type_detector = StatementFileTypeDetector()
    statement_parser = StatementParser()
    schema_detector = SchemaDetector()
    transaction_normalizer = TransactionNormalizer()

    # Create services
    category_service = CategoryService(category_repo)
    transaction_service = TransactionService(transaction_repo)
    
    statement_analyzer_service = StatementAnalyzerService(
        file_type_detector=file_type_detector,
        statement_parser=statement_parser,
        schema_detector=schema_detector,
        transaction_normalizer=transaction_normalizer,
        uploaded_file_repo=uploaded_file_repo,
        file_analysis_metadata_repo=file_analysis_metadata_repo
    )
    
    statement_persistence_service = StatementPersistenceService(
        statement_parser=statement_parser,
        transaction_normalizer=transaction_normalizer,
        transaction_repo=transaction_repo,
        uploaded_file_repo=uploaded_file_repo,
        file_analysis_metadata_repo=file_analysis_metadata_repo
    )

    return InternalDependencies(
        transaction_service=transaction_service, 
        category_service=category_service,
        statement_analyzer_service=statement_analyzer_service,
        statement_persistence_service=statement_persistence_service
    )


@contextmanager
def get_dependencies() -> Iterator[tuple[ExternalDependencies, InternalDependencies]]:
    """
    Context manager for getting dependencies.

    This ensures proper cleanup of resources when they're no longer needed.

    Yields:
        A tuple of (external_dependencies, internal_dependencies)
    """
    external = build_external_dependencies()
    internal = build_internal_dependencies(external)
    try:
        yield external, internal
    finally:
        external.cleanup()


def provide_dependencies() -> Iterator[InternalDependencies]:
    with get_dependencies() as (_external, internal):
        yield internal
