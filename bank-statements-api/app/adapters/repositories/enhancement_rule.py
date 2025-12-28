from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session, joinedload

from app.domain.models.category import Category
from app.domain.models.enhancement_rule import EnhancementRule, EnhancementRuleSource, MatchType
from app.ports.repositories.enhancement_rule import EnhancementRuleRepository


class SQLAlchemyEnhancementRuleRepository(EnhancementRuleRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_all(
        self,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
        description_search: Optional[str] = None,
        category_ids: Optional[List[UUID]] = None,
        counterparty_account_ids: Optional[List[UUID]] = None,
        match_type: Optional[MatchType] = None,
        source: Optional[EnhancementRuleSource] = None,
        rule_status_filter: Optional[str] = None,
        sort_field: str = "created_at",
        sort_direction: str = "desc",
    ) -> List[EnhancementRule]:
        if sort_field == "usage":
            return self._get_all_with_usage_sorting(
                user_id,
                limit,
                offset,
                description_search,
                category_ids,
                counterparty_account_ids,
                match_type,
                source,
                rule_status_filter,
                sort_direction,
            )

        query = (
            self.db.query(EnhancementRule)
            .options(
                joinedload(EnhancementRule.category).joinedload(Category.parent),
                joinedload(EnhancementRule.counterparty_account),
                joinedload(EnhancementRule.ai_suggested_category).joinedload(Category.parent),
                joinedload(EnhancementRule.ai_suggested_counterparty),
            )
            .filter(EnhancementRule.user_id == user_id)
        )

        if description_search:
            query = query.filter(EnhancementRule.normalized_description_pattern.ilike(f"%{description_search}%"))

        if category_ids:
            query = query.filter(EnhancementRule.category_id.in_(category_ids))

        if counterparty_account_ids:
            query = query.filter(EnhancementRule.counterparty_account_id.in_(counterparty_account_ids))

        if match_type:
            query = query.filter(EnhancementRule.match_type == match_type)

        if source:
            query = query.filter(EnhancementRule.source == source)

        if rule_status_filter == "unconfigured":
            query = query.filter(and_(EnhancementRule.category_id.is_(None), EnhancementRule.counterparty_account_id.is_(None)))
        elif rule_status_filter == "pending":
            query = query.filter(
                or_(
                    and_(
                        EnhancementRule.ai_suggested_category_id.isnot(None),
                        or_(
                            EnhancementRule.category_id.is_(None),
                            EnhancementRule.category_id != EnhancementRule.ai_suggested_category_id,
                        ),
                    ),
                    and_(
                        EnhancementRule.ai_suggested_counterparty_id.isnot(None),
                        or_(
                            EnhancementRule.counterparty_account_id.is_(None),
                            EnhancementRule.counterparty_account_id != EnhancementRule.ai_suggested_counterparty_id,
                        ),
                    ),
                )
            )
        elif rule_status_filter == "applied":
            query = query.filter(
                or_(
                    and_(
                        EnhancementRule.ai_suggested_category_id.isnot(None),
                        EnhancementRule.category_id == EnhancementRule.ai_suggested_category_id,
                    ),
                    and_(
                        EnhancementRule.ai_suggested_counterparty_id.isnot(None),
                        EnhancementRule.counterparty_account_id == EnhancementRule.ai_suggested_counterparty_id,
                    ),
                )
            )

        if sort_field in ["normalized_description_pattern", "normalized_description"]:
            sort_column = EnhancementRule.normalized_description_pattern
        elif sort_field == "category":
            sort_column = EnhancementRule.category_id
        elif sort_field == "counterparty":
            sort_column = EnhancementRule.counterparty_account_id
        elif sort_field == "source":
            sort_column = EnhancementRule.source
        else:
            sort_column = EnhancementRule.created_at

        if sort_direction == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

        return query.offset(offset).limit(limit).all()

    def _get_all_with_usage_sorting(
        self,
        user_id: UUID,
        limit: int,
        offset: int,
        description_search: Optional[str] = None,
        category_ids: Optional[List[UUID]] = None,
        counterparty_account_ids: Optional[List[UUID]] = None,
        match_type: Optional[MatchType] = None,
        source: Optional[EnhancementRuleSource] = None,
        rule_status_filter: Optional[str] = None,
        sort_direction: str = "desc",
    ) -> List[EnhancementRule]:
        query = (
            self.db.query(EnhancementRule)
            .options(
                joinedload(EnhancementRule.category).joinedload(Category.parent),
                joinedload(EnhancementRule.counterparty_account),
                joinedload(EnhancementRule.ai_suggested_category).joinedload(Category.parent),
                joinedload(EnhancementRule.ai_suggested_counterparty),
            )
            .filter(EnhancementRule.user_id == user_id)
        )

        if description_search:
            query = query.filter(EnhancementRule.normalized_description_pattern.ilike(f"%{description_search}%"))

        if category_ids:
            query = query.filter(EnhancementRule.category_id.in_(category_ids))

        if counterparty_account_ids:
            query = query.filter(EnhancementRule.counterparty_account_id.in_(counterparty_account_ids))

        if match_type:
            query = query.filter(EnhancementRule.match_type == match_type)

        if source:
            query = query.filter(EnhancementRule.source == source)

        if rule_status_filter == "unconfigured":
            query = query.filter(and_(EnhancementRule.category_id.is_(None), EnhancementRule.counterparty_account_id.is_(None)))
        elif rule_status_filter == "pending":
            query = query.filter(
                or_(
                    and_(
                        EnhancementRule.ai_suggested_category_id.isnot(None),
                        or_(
                            EnhancementRule.category_id.is_(None),
                            EnhancementRule.category_id != EnhancementRule.ai_suggested_category_id,
                        ),
                    ),
                    and_(
                        EnhancementRule.ai_suggested_counterparty_id.isnot(None),
                        or_(
                            EnhancementRule.counterparty_account_id.is_(None),
                            EnhancementRule.counterparty_account_id != EnhancementRule.ai_suggested_counterparty_id,
                        ),
                    ),
                )
            )
        elif rule_status_filter == "applied":
            query = query.filter(
                or_(
                    and_(
                        EnhancementRule.ai_suggested_category_id.isnot(None),
                        EnhancementRule.category_id == EnhancementRule.ai_suggested_category_id,
                    ),
                    and_(
                        EnhancementRule.ai_suggested_counterparty_id.isnot(None),
                        EnhancementRule.counterparty_account_id == EnhancementRule.ai_suggested_counterparty_id,
                    ),
                )
            )

        all_rules = query.all()

        rules_with_counts = []
        for rule in all_rules:
            try:
                from app.adapters.repositories.transaction import SQLAlchemyTransactionRepository

                transaction_repo = SQLAlchemyTransactionRepository(self.db)
                count = transaction_repo.count_matching_rule(rule)
            except Exception:
                count = 0

            rules_with_counts.append((rule, count))

        if sort_direction == "asc":
            rules_with_counts.sort(key=lambda x: x[1])
        else:
            rules_with_counts.sort(key=lambda x: x[1], reverse=True)

        start_idx = offset
        end_idx = offset + limit
        paginated_rules = rules_with_counts[start_idx:end_idx]

        return [rule for rule, count in paginated_rules]

    def count(
        self,
        user_id: UUID,
        description_search: Optional[str] = None,
        category_ids: Optional[List[UUID]] = None,
        counterparty_account_ids: Optional[List[UUID]] = None,
        match_type: Optional[MatchType] = None,
        source: Optional[EnhancementRuleSource] = None,
        rule_status_filter: Optional[str] = None,
    ) -> int:
        query = self.db.query(func.count(EnhancementRule.id)).filter(EnhancementRule.user_id == user_id)

        if description_search:
            query = query.filter(EnhancementRule.normalized_description_pattern.ilike(f"%{description_search}%"))

        if category_ids:
            query = query.filter(EnhancementRule.category_id.in_(category_ids))

        if counterparty_account_ids:
            query = query.filter(EnhancementRule.counterparty_account_id.in_(counterparty_account_ids))

        if match_type:
            query = query.filter(EnhancementRule.match_type == match_type)

        if source:
            query = query.filter(EnhancementRule.source == source)

        if rule_status_filter == "unconfigured":
            query = query.filter(and_(EnhancementRule.category_id.is_(None), EnhancementRule.counterparty_account_id.is_(None)))
        elif rule_status_filter == "pending":
            query = query.filter(
                or_(
                    and_(
                        EnhancementRule.ai_suggested_category_id.isnot(None),
                        or_(
                            EnhancementRule.category_id.is_(None),
                            EnhancementRule.category_id != EnhancementRule.ai_suggested_category_id,
                        ),
                    ),
                    and_(
                        EnhancementRule.ai_suggested_counterparty_id.isnot(None),
                        or_(
                            EnhancementRule.counterparty_account_id.is_(None),
                            EnhancementRule.counterparty_account_id != EnhancementRule.ai_suggested_counterparty_id,
                        ),
                    ),
                )
            )
        elif rule_status_filter == "applied":
            query = query.filter(
                or_(
                    and_(
                        EnhancementRule.ai_suggested_category_id.isnot(None),
                        EnhancementRule.category_id == EnhancementRule.ai_suggested_category_id,
                    ),
                    and_(
                        EnhancementRule.ai_suggested_counterparty_id.isnot(None),
                        EnhancementRule.counterparty_account_id == EnhancementRule.ai_suggested_counterparty_id,
                    ),
                )
            )

        return query.scalar()

    def save(self, rule: EnhancementRule) -> EnhancementRule:
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def find_by_id(self, rule_id: UUID, user_id: UUID) -> Optional[EnhancementRule]:
        return (
            self.db.query(EnhancementRule)
            .options(
                joinedload(EnhancementRule.category).joinedload(Category.parent),
                joinedload(EnhancementRule.counterparty_account),
                joinedload(EnhancementRule.ai_suggested_category).joinedload(Category.parent),
                joinedload(EnhancementRule.ai_suggested_counterparty),
            )
            .filter(EnhancementRule.id == rule_id, EnhancementRule.user_id == user_id)
            .first()
        )

    def find_by_normalized_description(self, normalized_description: str, user_id: UUID) -> Optional[EnhancementRule]:
        return (
            self.db.query(EnhancementRule)
            .filter(
                EnhancementRule.normalized_description_pattern == normalized_description,
                EnhancementRule.user_id == user_id,
            )
            .first()
        )

    def delete(self, rule: EnhancementRule) -> None:
        self.db.delete(rule)
        self.db.commit()

    def find_matching_rules(self, normalized_description: str, user_id: UUID) -> List[EnhancementRule]:
        return (
            self.db.query(EnhancementRule)
            .filter(
                EnhancementRule.user_id == user_id,
                or_(
                    and_(
                        EnhancementRule.match_type == MatchType.EXACT,
                        EnhancementRule.normalized_description_pattern == normalized_description,
                    ),
                    and_(
                        EnhancementRule.match_type == MatchType.PREFIX,
                        func.lower(normalized_description).like(
                            func.lower(EnhancementRule.normalized_description_pattern) + "%"
                        ),
                    ),
                    and_(
                        EnhancementRule.match_type == MatchType.INFIX,
                        func.lower(normalized_description).like(
                            "%" + func.lower(EnhancementRule.normalized_description_pattern) + "%"
                        ),
                    ),
                ),
            )
            .order_by(
                EnhancementRule.match_type.asc(),
                EnhancementRule.created_at.asc(),
            )
            .all()
        )

    def find_matching_rules_batch(self, normalized_descriptions: List[str], user_id: UUID) -> List[EnhancementRule]:
        if not normalized_descriptions:
            return []

        conditions = []
        for description in normalized_descriptions:
            conditions.append(
                or_(
                    and_(
                        EnhancementRule.match_type == MatchType.EXACT,
                        func.lower(EnhancementRule.normalized_description_pattern) == func.lower(description),
                    ),
                    and_(
                        EnhancementRule.match_type == MatchType.PREFIX,
                        func.lower(description).like(func.lower(EnhancementRule.normalized_description_pattern) + "%"),
                    ),
                    and_(
                        EnhancementRule.match_type == MatchType.INFIX,
                        func.lower(description).like("%" + func.lower(EnhancementRule.normalized_description_pattern) + "%"),
                    ),
                )
            )

        return (
            self.db.query(EnhancementRule)
            .filter(EnhancementRule.user_id == user_id, or_(*conditions))
            .order_by(
                EnhancementRule.match_type.asc(),
                EnhancementRule.created_at.asc(),
            )
            .all()
        )
