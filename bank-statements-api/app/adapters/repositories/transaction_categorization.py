from typing import Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, func, case
from sqlalchemy.orm import Session, joinedload

from app.domain.models.category import Category
from app.domain.models.transaction import Transaction
from app.domain.models.transaction_categorization import CategorizationSource, TransactionCategorization
from app.ports.repositories.transaction_categorization import TransactionCategorizationRepository


class SQLAlchemyTransactionCategorizationRepository(TransactionCategorizationRepository):
    """
    SQLAlchemy implementation of the TransactionCategorizationRepository.
    Adapter in the Hexagonal Architecture pattern.
    """

    def __init__(self, db_session: Session):
        self.db_session = db_session

    def get_categories_by_normalized_descriptions(
        self, normalized_descriptions: List[str], batch_size: int = 100
    ) -> Dict[str, UUID]:
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
            rules = (
                self.db_session.query(TransactionCategorization)
                .filter(TransactionCategorization.normalized_description.in_(batch))
                .all()
            )

            # Build result dictionary for this batch
            for rule in rules:
                result[rule.normalized_description] = rule.category_id

        return result

    def create_rule(
        self,
        normalized_description: str,
        category_id: UUID,
        source: CategorizationSource,
    ) -> TransactionCategorization:
        """Create a new categorization rule"""
        rule = TransactionCategorization(
            normalized_description=normalized_description,
            category_id=category_id,
            source=source,
        )
        self.db_session.add(rule)
        self.db_session.commit()
        self.db_session.refresh(rule)
        return rule

    def get_rule_by_normalized_description(self, normalized_description: str) -> Optional[TransactionCategorization]:
        """Get a categorization rule by normalized description"""
        return (
            self.db_session.query(TransactionCategorization)
            .filter(TransactionCategorization.normalized_description == normalized_description)
            .first()
        )

    def get_statistics(self) -> Dict[str, int]:
        """Get repository statistics for monitoring and analytics"""
        total_rules = self.db_session.query(TransactionCategorization).count()

        manual_rules = (
            self.db_session.query(TransactionCategorization)
            .filter(TransactionCategorization.source == CategorizationSource.MANUAL)
            .count()
        )

        ai_rules = (
            self.db_session.query(TransactionCategorization)
            .filter(TransactionCategorization.source == CategorizationSource.AI)
            .count()
        )

        return {
            "total_rules": total_rules,
            "manual_rules": manual_rules,
            "ai_rules": ai_rules,
        }

    def get_rules_paginated(
        self,
        page: int = 1,
        page_size: int = 20,
        description_search: Optional[str] = None,
        category_ids: Optional[List[str]] = None,
        source: Optional[CategorizationSource] = None,
    ) -> Tuple[List[TransactionCategorization], int]:
        """Get paginated categorization rules with filtering."""
        # Create a subquery to get transaction counts for each rule
        transaction_count_subquery = (
            self.db_session.query(
                TransactionCategorization.id.label('rule_id'),
                func.count(Transaction.id).label('transaction_count')
            )
            .outerjoin(Transaction, Transaction.normalized_description == TransactionCategorization.normalized_description)
            .group_by(TransactionCategorization.id)
            .subquery()
        )

        # Main query with joins
        query = (
            self.db_session.query(
                TransactionCategorization,
                func.coalesce(transaction_count_subquery.c.transaction_count, 0).label('transaction_count')
            )
            .outerjoin(transaction_count_subquery, TransactionCategorization.id == transaction_count_subquery.c.rule_id)
            .options(joinedload(TransactionCategorization.category))
        )

        # Apply filters
        if description_search:
            query = query.filter(TransactionCategorization.normalized_description.ilike(f"%{description_search}%"))

        if category_ids:
            # Convert string UUIDs to UUID objects
            uuid_category_ids = [UUID(cid) for cid in category_ids]
            query = query.filter(TransactionCategorization.category_id.in_(uuid_category_ids))

        if source:
            query = query.filter(TransactionCategorization.source == source)

        # Get total count before pagination
        total_count = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        results = query.order_by(TransactionCategorization.created_at.desc()).offset(offset).limit(page_size).all()

        # Extract rules and add transaction counts
        rules = []
        for rule, tx_count in results:
            # Add transaction_count as an attribute to the rule object
            rule.transaction_count = tx_count
            rules.append(rule)

        return rules, total_count

    def get_rule_by_id(self, rule_id: UUID) -> Optional[TransactionCategorization]:
        """Get a categorization rule by ID"""
        return (
            self.db_session.query(TransactionCategorization)
            .options(joinedload(TransactionCategorization.category))
            .filter(TransactionCategorization.id == rule_id)
            .first()
        )

    def update_rule(
        self,
        rule_id: UUID,
        normalized_description: str,
        category_id: UUID,
        source: CategorizationSource,
    ) -> Optional[TransactionCategorization]:
        """Update an existing categorization rule"""
        rule = self.get_rule_by_id(rule_id)
        if not rule:
            return None

        rule.normalized_description = normalized_description
        rule.category_id = category_id
        rule.source = source
        
        self.db_session.commit()
        self.db_session.refresh(rule)
        return rule

    def delete_rule(self, rule_id: UUID) -> bool:
        """Delete a categorization rule"""
        rule = self.get_rule_by_id(rule_id)
        if not rule:
            return False

        self.db_session.delete(rule)
        self.db_session.commit()
        return True

    def get_enhanced_statistics(self) -> Dict:
        """Get enhanced statistics with category usage and transaction counts"""
        # Basic statistics
        basic_stats = self.get_statistics()

        # Count transactions categorized by rules
        total_transactions_categorized = (
            self.db_session.query(func.count(Transaction.id))
            .join(TransactionCategorization, Transaction.normalized_description == TransactionCategorization.normalized_description)
            .scalar()
        )

        transactions_with_manual_rules = (
            self.db_session.query(func.count(Transaction.id))
            .join(TransactionCategorization, Transaction.normalized_description == TransactionCategorization.normalized_description)
            .filter(TransactionCategorization.source == CategorizationSource.MANUAL)
            .scalar()
        )

        transactions_with_ai_rules = (
            self.db_session.query(func.count(Transaction.id))
            .join(TransactionCategorization, Transaction.normalized_description == TransactionCategorization.normalized_description)
            .filter(TransactionCategorization.source == CategorizationSource.AI)
            .scalar()
        )

        # Category usage statistics
        category_usage = (
            self.db_session.query(
                TransactionCategorization.category_id,
                Category.name.label("category_name"),
                func.count(TransactionCategorization.id).label("rule_count"),
                func.count(Transaction.id).label("transaction_count"),
                func.sum(
                    case(
                        (TransactionCategorization.source == CategorizationSource.MANUAL, 1),
                        else_=0
                    )
                ).label("manual_rules"),
                func.sum(
                    case(
                        (TransactionCategorization.source == CategorizationSource.AI, 1),
                        else_=0
                    )
                ).label("ai_rules"),
            )
            .join(Category, TransactionCategorization.category_id == Category.id)
            .outerjoin(Transaction, Transaction.normalized_description == TransactionCategorization.normalized_description)
            .group_by(TransactionCategorization.category_id, Category.name)
            .order_by(func.count(Transaction.id).desc())
            .all()
        )

        # Top rules by usage
        top_rules = (
            self.db_session.query(
                TransactionCategorization.id,
                TransactionCategorization.normalized_description,
                Category.name.label("category_name"),
                TransactionCategorization.source,
                func.count(Transaction.id).label("transaction_count"),
            )
            .join(Category, TransactionCategorization.category_id == Category.id)
            .outerjoin(Transaction, Transaction.normalized_description == TransactionCategorization.normalized_description)
            .group_by(
                TransactionCategorization.id,
                TransactionCategorization.normalized_description,
                Category.name,
                TransactionCategorization.source,
            )
            .order_by(func.count(Transaction.id).desc())
            .limit(10)
            .all()
        )

        # Unused rules
        unused_rules = (
            self.db_session.query(
                TransactionCategorization.id,
                TransactionCategorization.normalized_description,
                Category.name.label("category_name"),
                TransactionCategorization.source,
                TransactionCategorization.created_at,
            )
            .join(Category, TransactionCategorization.category_id == Category.id)
            .outerjoin(Transaction, Transaction.normalized_description == TransactionCategorization.normalized_description)
            .group_by(
                TransactionCategorization.id,
                TransactionCategorization.normalized_description,
                Category.name,
                TransactionCategorization.source,
                TransactionCategorization.created_at,
            )
            .having(func.count(Transaction.id) == 0)
            .order_by(TransactionCategorization.created_at.desc())
            .limit(20)
            .all()
        )

        return {
            "summary": {
                "total_rules": basic_stats["total_rules"],
                "manual_rules": basic_stats["manual_rules"],
                "ai_rules": basic_stats["ai_rules"],
                "total_transactions_categorized": total_transactions_categorized or 0,
                "transactions_with_manual_rules": transactions_with_manual_rules or 0,
                "transactions_with_ai_rules": transactions_with_ai_rules or 0,
            },
            "category_usage": [
                {
                    "category_id": str(usage.category_id),
                    "category_name": usage.category_name,
                    "rule_count": usage.rule_count,
                    "transaction_count": usage.transaction_count or 0,
                    "manual_rules": usage.manual_rules or 0,
                    "ai_rules": usage.ai_rules or 0,
                }
                for usage in category_usage
            ],
            "top_rules_by_usage": [
                {
                    "rule_id": str(rule.id),
                    "normalized_description": rule.normalized_description,
                    "category_name": rule.category_name,
                    "transaction_count": rule.transaction_count or 0,
                    "source": rule.source.value,
                }
                for rule in top_rules
            ],
            "unused_rules": [
                {
                    "rule_id": str(rule.id),
                    "normalized_description": rule.normalized_description,
                    "category_name": rule.category_name,
                    "source": rule.source.value,
                    "created_at": rule.created_at.isoformat(),
                }
                for rule in unused_rules
            ],
        }
