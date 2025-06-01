from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.models.transaction_categorization import CategorizationSource, TransactionCategorization
from app.ports.repositories.transaction_categorization import TransactionCategorizationRepository


class SQLAlchemyTransactionCategorizationRepository(TransactionCategorizationRepository):
    """
    SQLAlchemy implementation of the TransactionCategorizationRepository.
    Adapter in the Hexagonal Architecture pattern.
    """

    def __init__(self, db_session: Session):
        self.db_session = db_session

    def get_categories_by_normalized_descriptions(self, normalized_descriptions: List[str], batch_size: int = 100) -> Dict[str, UUID]:
        """Get category mappings for normalized descriptions."""
        if not normalized_descriptions:
            return {}

        # Remove duplicates while preserving order for consistent processing
        unique_descriptions = list(dict.fromkeys(normalized_descriptions))
        result = {}

        # Process in batches for better performance with large datasets
        for i in range(0, len(unique_descriptions), batch_size):
            batch = unique_descriptions[i : i + batch_size]

            # Query for matching rules in this batch
            rules = self.db_session.query(TransactionCategorization).filter(TransactionCategorization.normalized_description.in_(batch)).all()

            # Build result dictionary for this batch
            for rule in rules:
                result[rule.normalized_description] = rule.category_id

        return result

    def create_rule(self, normalized_description: str, category_id: UUID, source: CategorizationSource) -> TransactionCategorization:
        """Create a new categorization rule"""
        rule = TransactionCategorization(normalized_description=normalized_description, category_id=category_id, source=source)
        self.db_session.add(rule)
        self.db_session.commit()
        self.db_session.refresh(rule)
        return rule

    def get_rule_by_normalized_description(self, normalized_description: str) -> Optional[TransactionCategorization]:
        """Get a categorization rule by normalized description"""
        return self.db_session.query(TransactionCategorization).filter(TransactionCategorization.normalized_description == normalized_description).first()

    def get_statistics(self) -> Dict[str, int]:
        """Get repository statistics for monitoring and analytics"""
        total_rules = self.db_session.query(TransactionCategorization).count()

        manual_rules = self.db_session.query(TransactionCategorization).filter(TransactionCategorization.source == CategorizationSource.MANUAL).count()

        ai_rules = self.db_session.query(TransactionCategorization).filter(TransactionCategorization.source == CategorizationSource.AI).count()

        return {
            "total_rules": total_rules,
            "manual_rules": manual_rules,
            "ai_rules": ai_rules,
        }
