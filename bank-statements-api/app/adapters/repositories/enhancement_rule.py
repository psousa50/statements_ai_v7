from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_, case, select
from sqlalchemy.sql import text

from app.domain.models.enhancement_rule import EnhancementRule, MatchType, EnhancementRuleSource
from app.domain.models.transaction import Transaction
from app.ports.repositories.enhancement_rule import EnhancementRuleRepository


class SQLAlchemyEnhancementRuleRepository(EnhancementRuleRepository):
    """SQLAlchemy implementation of EnhancementRuleRepository"""

    def __init__(self, db: Session):
        self.db = db

    def get_all(
        self,
        limit: int = 50,
        offset: int = 0,
        description_search: Optional[str] = None,
        category_ids: Optional[List[UUID]] = None,
        counterparty_account_ids: Optional[List[UUID]] = None,
        match_type: Optional[MatchType] = None,
        source: Optional[EnhancementRuleSource] = None,
        sort_field: str = "created_at",
        sort_direction: str = "desc",
    ) -> List[EnhancementRule]:
        """Get enhancement rules with filtering and pagination"""
        
        # If sorting by usage, we need a more complex query with subquery for transaction counts
        if sort_field == "usage":
            return self._get_all_with_usage_sorting(
                limit, offset, description_search, category_ids, 
                counterparty_account_ids, match_type, source, sort_direction
            )
        
        # Standard query for other sorting fields
        query = self.db.query(EnhancementRule)
        
        # Apply filters
        if description_search:
            query = query.filter(
                EnhancementRule.normalized_description_pattern.ilike(f"%{description_search}%")
            )
        
        if category_ids:
            query = query.filter(EnhancementRule.category_id.in_(category_ids))
        
        if counterparty_account_ids:
            query = query.filter(EnhancementRule.counterparty_account_id.in_(counterparty_account_ids))
        
        if match_type:
            query = query.filter(EnhancementRule.match_type == match_type)
        
        if source:
            query = query.filter(EnhancementRule.source == source)
        
        # Apply sorting
        if sort_field in ["normalized_description_pattern", "normalized_description"]:
            sort_column = EnhancementRule.normalized_description_pattern
        elif sort_field == "category":
            sort_column = EnhancementRule.category_id
        elif sort_field == "counterparty":
            sort_column = EnhancementRule.counterparty_account_id
        elif sort_field == "source":
            sort_column = EnhancementRule.source
        else:  # default to created_at
            sort_column = EnhancementRule.created_at
        
        if sort_direction == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())
        
        # Apply pagination
        return query.offset(offset).limit(limit).all()
    
    def _get_all_with_usage_sorting(
        self,
        limit: int,
        offset: int,
        description_search: Optional[str] = None,
        category_ids: Optional[List[UUID]] = None,
        counterparty_account_ids: Optional[List[UUID]] = None,
        match_type: Optional[MatchType] = None,
        source: Optional[EnhancementRuleSource] = None,
        sort_direction: str = "desc",
    ) -> List[EnhancementRule]:
        """Get enhancement rules sorted by usage count"""
        
        # Since sorting by usage requires counting transactions for each rule,
        # we need to get all rules first, calculate their usage counts, sort them,
        # and then apply pagination. This is less efficient but necessary for proper sorting.
        
        # First, get all rules with filters applied (but without pagination)
        query = self.db.query(EnhancementRule)
        
        # Apply filters (same as regular query)
        if description_search:
            query = query.filter(
                EnhancementRule.normalized_description_pattern.ilike(f"%{description_search}%")
            )
        
        if category_ids:
            query = query.filter(EnhancementRule.category_id.in_(category_ids))
        
        if counterparty_account_ids:
            query = query.filter(EnhancementRule.counterparty_account_id.in_(counterparty_account_ids))
        
        if match_type:
            query = query.filter(EnhancementRule.match_type == match_type)
        
        if source:
            query = query.filter(EnhancementRule.source == source)
        
        # Get all rules matching the filters
        all_rules = query.all()
        
        # Calculate usage count for each rule and create tuples for sorting
        rules_with_counts = []
        for rule in all_rules:
            try:
                # Use the existing count_matching_rule method from transaction repository
                # We need to import and get the transaction repository here
                from app.adapters.repositories.transaction import SQLAlchemyTransactionRepository
                transaction_repo = SQLAlchemyTransactionRepository(self.db)
                count = transaction_repo.count_matching_rule(rule)
            except Exception:
                # Fallback to 0 if counting fails
                count = 0
            
            rules_with_counts.append((rule, count))
        
        # Sort by usage count
        if sort_direction == "asc":
            rules_with_counts.sort(key=lambda x: x[1])  # Sort by count ascending
        else:
            rules_with_counts.sort(key=lambda x: x[1], reverse=True)  # Sort by count descending
        
        # Apply pagination
        start_idx = offset
        end_idx = offset + limit
        paginated_rules = rules_with_counts[start_idx:end_idx]
        
        # Return just the rules (without counts)
        return [rule for rule, count in paginated_rules]

    def count(
        self,
        description_search: Optional[str] = None,
        category_ids: Optional[List[UUID]] = None,
        counterparty_account_ids: Optional[List[UUID]] = None,
        match_type: Optional[MatchType] = None,
        source: Optional[EnhancementRuleSource] = None,
    ) -> int:
        """Count enhancement rules with filters"""
        query = self.db.query(func.count(EnhancementRule.id))
        
        # Apply same filters as get_all
        if description_search:
            query = query.filter(
                EnhancementRule.normalized_description_pattern.ilike(f"%{description_search}%")
            )
        
        if category_ids:
            query = query.filter(EnhancementRule.category_id.in_(category_ids))
        
        if counterparty_account_ids:
            query = query.filter(EnhancementRule.counterparty_account_id.in_(counterparty_account_ids))
        
        if match_type:
            query = query.filter(EnhancementRule.match_type == match_type)
        
        if source:
            query = query.filter(EnhancementRule.source == source)
        
        return query.scalar()

    def save(self, rule: EnhancementRule) -> EnhancementRule:
        """Save an enhancement rule"""
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def find_by_id(self, rule_id: UUID) -> Optional[EnhancementRule]:
        """Find enhancement rule by ID"""
        return self.db.query(EnhancementRule).filter(EnhancementRule.id == rule_id).first()

    def find_by_normalized_description(self, normalized_description: str) -> Optional[EnhancementRule]:
        """Find enhancement rule by exact normalized description pattern"""
        return (
            self.db.query(EnhancementRule)
            .filter(EnhancementRule.normalized_description_pattern == normalized_description)
            .first()
        )

    def delete(self, rule: EnhancementRule) -> None:
        """Delete an enhancement rule"""
        self.db.delete(rule)
        self.db.commit()

    def find_matching_rules(self, normalized_description: str) -> List[EnhancementRule]:
        """Find enhancement rules that could match a normalized description"""
        # This returns potential matches - actual matching logic is in the EnhancementRule.matches_transaction method
        return (
            self.db.query(EnhancementRule)
            .filter(
                or_(
                    # For exact matches, the pattern must match exactly
                    and_(
                        EnhancementRule.match_type == MatchType.EXACT,
                        EnhancementRule.normalized_description_pattern == normalized_description
                    ),
                    # For prefix matches, the description must start with the pattern
                    and_(
                        EnhancementRule.match_type == MatchType.PREFIX,
                        func.lower(normalized_description).like(
                            func.lower(EnhancementRule.normalized_description_pattern) + '%'
                        )
                    ),
                    # For infix matches, the description must contain the pattern
                    and_(
                        EnhancementRule.match_type == MatchType.INFIX,
                        func.lower(normalized_description).like(
                            '%' + func.lower(EnhancementRule.normalized_description_pattern) + '%'
                        )
                    )
                )
            )
            .order_by(
                # Order by match type precedence: exact, prefix, infix
                EnhancementRule.match_type.asc(),
                EnhancementRule.created_at.asc()
            )
            .all()
        )