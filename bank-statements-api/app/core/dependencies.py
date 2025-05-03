from contextlib import contextmanager
from typing import Iterator

from sqlalchemy.orm import Session

from app.adapters.repositories.transaction import SQLAlchemyTransactionRepository
from app.core.database import SessionLocal
from app.services.transaction import TransactionService


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
        """Get the database session."""
        if self._db is None:
            self._db = self._db_factory()
        return self._db
    
    def cleanup(self):
        """Clean up resources."""
        if self._db is not None:
            self._db.close()
            self._db = None


class InternalDependencies:
    """Container for internal dependencies like services, repositories, etc."""
    
    def __init__(self, transaction_service: TransactionService):
        self.transaction_service = transaction_service


def get_db_session() -> Session:
    """Create a new database session."""
    return SessionLocal()


def build_external_dependencies() -> ExternalDependencies:
    """Build external dependencies for the application."""
    return ExternalDependencies(db_factory=get_db_session)


def build_internal_dependencies(external: ExternalDependencies) -> InternalDependencies:
    """Build internal dependencies using external dependencies."""
    transaction_repo = SQLAlchemyTransactionRepository(external.db)
    transaction_service = TransactionService(transaction_repo)
    return InternalDependencies(transaction_service=transaction_service)


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
