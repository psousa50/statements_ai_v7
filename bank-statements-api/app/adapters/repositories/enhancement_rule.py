from typing import Any, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, false, func, or_, select, text
from sqlalchemy.orm import Session, joinedload

from app.domain.models.category import Category
from app.domain.models.enhancement_rule import EnhancementRule, EnhancementRuleSource, MatchType
from app.domain.models.enhancement_rule_pattern import EnhancementRulePattern
from app.domain.models.transaction import Transaction
from app.ports.repositories.enhancement_rule import EnhancementRuleRepository


def _first_pattern_subquery():
    return (
        select(func.min(EnhancementRulePattern.normalized_description))
        .where(EnhancementRulePattern.rule_id == EnhancementRule.id)
        .scalar_subquery()
    )


def _description_search_filter(search: str):
    return EnhancementRule.id.in_(
        select(EnhancementRulePattern.rule_id).where(EnhancementRulePattern.normalized_description.ilike(f"%{search}%"))
    )


def _match_type_filter(match_type: MatchType):
    return EnhancementRule.id.in_(select(EnhancementRulePattern.rule_id).where(EnhancementRulePattern.match_type == match_type))


def build_pattern_match_filter(transaction_description_column, patterns: List[EnhancementRulePattern]):
    if not patterns:
        return false()
    conditions = []
    for pattern in patterns:
        if pattern.match_type == MatchType.EXACT:
            conditions.append(transaction_description_column == pattern.normalized_description)
        elif pattern.match_type == MatchType.PREFIX:
            conditions.append(transaction_description_column.like(f"{pattern.normalized_description}%"))
        elif pattern.match_type == MatchType.INFIX:
            conditions.append(transaction_description_column.like(f"%{pattern.normalized_description}%"))
    return or_(*conditions)


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
        secondary_sort_field: Optional[str] = None,
        secondary_sort_direction: Optional[str] = None,
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
                secondary_sort_field,
                secondary_sort_direction,
            )

        if sort_field == "latest_match":
            return self._get_all_with_latest_match_sorting(
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
                secondary_sort_field,
                secondary_sort_direction,
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

        query = self._apply_common_filters(
            query,
            description_search=description_search,
            category_ids=category_ids,
            counterparty_account_ids=counterparty_account_ids,
            match_type=match_type,
            source=source,
            rule_status_filter=rule_status_filter,
        )

        if sort_field in ["normalized_description_pattern", "normalized_description"]:
            sort_column = _first_pattern_subquery()
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

    def _apply_common_filters(
        self,
        query,
        description_search: Optional[str] = None,
        category_ids: Optional[List[UUID]] = None,
        counterparty_account_ids: Optional[List[UUID]] = None,
        match_type: Optional[MatchType] = None,
        source: Optional[EnhancementRuleSource] = None,
        rule_status_filter: Optional[str] = None,
    ):
        if description_search:
            query = query.filter(_description_search_filter(description_search))

        if category_ids:
            query = query.filter(EnhancementRule.category_id.in_(category_ids))

        if counterparty_account_ids:
            query = query.filter(EnhancementRule.counterparty_account_id.in_(counterparty_account_ids))

        if match_type:
            query = query.filter(_match_type_filter(match_type))

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

        return query

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
        secondary_sort_field: Optional[str] = None,
        secondary_sort_direction: Optional[str] = None,
    ) -> List[EnhancementRule]:
        is_unconfigured_filter = rule_status_filter == "unconfigured"

        rule_counts = self._get_rule_counts_with_sql(
            user_id=user_id,
            limit=limit,
            offset=offset,
            description_search=description_search,
            category_ids=category_ids,
            counterparty_account_ids=counterparty_account_ids,
            match_type=match_type,
            source=source,
            rule_status_filter=rule_status_filter,
            sort_direction=sort_direction,
            count_uncategorized_only=is_unconfigured_filter,
        )

        if not rule_counts:
            return []

        rule_ids = [rc[0] for rc in rule_counts]
        count_map = {rc[0]: rc[1] for rc in rule_counts}
        date_map = {rc[0]: rc[2] for rc in rule_counts}

        rules = (
            self.db.query(EnhancementRule)
            .options(
                joinedload(EnhancementRule.category).joinedload(Category.parent),
                joinedload(EnhancementRule.counterparty_account),
                joinedload(EnhancementRule.ai_suggested_category).joinedload(Category.parent),
                joinedload(EnhancementRule.ai_suggested_counterparty),
            )
            .filter(EnhancementRule.id.in_(rule_ids))
            .all()
        )

        rule_by_id = {r.id: r for r in rules}
        ordered_rules = []
        for rule_id in rule_ids:
            if rule_id in rule_by_id:
                rule = rule_by_id[rule_id]
                rule.transaction_count = count_map.get(rule_id, 0)
                rule.latest_match_date = date_map.get(rule_id)
                ordered_rules.append(rule)

        return ordered_rules

    def _get_rule_counts_with_sql(
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
        count_uncategorized_only: bool = False,
    ) -> List[Tuple[UUID, int, Optional[Any]]]:
        match_condition = or_(
            and_(
                EnhancementRulePattern.match_type == MatchType.EXACT,
                Transaction.normalized_description == EnhancementRulePattern.normalized_description,
            ),
            and_(
                EnhancementRulePattern.match_type == MatchType.PREFIX,
                Transaction.normalized_description.like(func.concat(EnhancementRulePattern.normalized_description, "%")),
            ),
            and_(
                EnhancementRulePattern.match_type == MatchType.INFIX,
                Transaction.normalized_description.like(func.concat("%", EnhancementRulePattern.normalized_description, "%")),
            ),
        )

        pattern_match_subquery = (
            select(
                EnhancementRulePattern.rule_id.label("rule_id"),
                Transaction.id.label("transaction_id"),
                Transaction.date.label("transaction_date"),
                Transaction.category_id.label("transaction_category_id"),
            )
            .join(
                Transaction,
                and_(
                    Transaction.user_id == user_id,
                    match_condition,
                ),
            )
            .subquery()
        )

        join_conditions = [pattern_match_subquery.c.rule_id == EnhancementRule.id]
        if count_uncategorized_only:
            join_conditions.append(pattern_match_subquery.c.transaction_category_id.is_(None))

        query = (
            self.db.query(
                EnhancementRule.id,
                func.count(pattern_match_subquery.c.transaction_id).label("transaction_count"),
                func.max(pattern_match_subquery.c.transaction_date).label("latest_match_date"),
            )
            .outerjoin(pattern_match_subquery, and_(*join_conditions))
            .filter(EnhancementRule.user_id == user_id)
            .group_by(EnhancementRule.id)
        )

        query = self._apply_common_filters(
            query,
            description_search=description_search,
            category_ids=category_ids,
            counterparty_account_ids=counterparty_account_ids,
            match_type=match_type,
            source=source,
            rule_status_filter=rule_status_filter,
        )

        if sort_direction == "asc":
            query = query.order_by(text("transaction_count ASC"))
        else:
            query = query.order_by(text("transaction_count DESC"))

        query = query.offset(offset).limit(limit)

        return query.all()

    def _get_all_with_latest_match_sorting(
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
        secondary_sort_field: Optional[str] = None,
        secondary_sort_direction: Optional[str] = None,
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

        query = self._apply_common_filters(
            query,
            description_search=description_search,
            category_ids=category_ids,
            counterparty_account_ids=counterparty_account_ids,
            match_type=match_type,
            source=source,
            rule_status_filter=rule_status_filter,
        )

        all_rules = query.all()

        from datetime import date as date_type

        from app.adapters.repositories.transaction import SQLAlchemyTransactionRepository

        transaction_repo = SQLAlchemyTransactionRepository(self.db)
        min_date = date_type(1900, 1, 1)

        dates = transaction_repo.get_latest_matching_dates_batch(all_rules)
        counts = transaction_repo.count_matching_rules_batch(all_rules, uncategorized_only=False)

        rules_with_data = []
        for rule in all_rules:
            latest_date = dates.get(rule.id)
            count = counts.get(rule.id, 0)
            rules_with_data.append((rule, latest_date or min_date, latest_date, count))

        def first_pattern_text(rule: EnhancementRule) -> str:
            if not rule.patterns:
                return ""
            return min(p.normalized_description for p in rule.patterns).lower()

        def get_secondary_value(item):
            rule, sort_date, latest_date, count = item
            if secondary_sort_field == "usage":
                return count
            elif secondary_sort_field == "latest_match":
                return sort_date
            elif secondary_sort_field == "created_at":
                return rule.created_at
            elif secondary_sort_field == "normalized_description_pattern":
                return first_pattern_text(rule)
            return rule.created_at

        secondary_reverse = secondary_sort_direction != "asc" if secondary_sort_direction else True

        if sort_direction == "asc":
            if secondary_sort_field:
                rules_with_data.sort(key=lambda x: x[1], reverse=False)
                groups = {}
                for item in rules_with_data:
                    key = item[1]
                    if key not in groups:
                        groups[key] = []
                    groups[key].append(item)
                rules_with_data = []
                for key in sorted(groups.keys()):
                    group = groups[key]
                    group.sort(key=get_secondary_value, reverse=secondary_reverse)
                    rules_with_data.extend(group)
            else:
                rules_with_data.sort(key=lambda x: x[1])
        else:
            if secondary_sort_field:
                rules_with_data.sort(key=lambda x: x[1], reverse=True)
                groups = {}
                for item in rules_with_data:
                    key = item[1]
                    if key not in groups:
                        groups[key] = []
                    groups[key].append(item)
                rules_with_data = []
                for key in sorted(groups.keys(), reverse=True):
                    group = groups[key]
                    group.sort(key=get_secondary_value, reverse=secondary_reverse)
                    rules_with_data.extend(group)
            else:
                rules_with_data.sort(key=lambda x: x[1], reverse=True)

        start_idx = offset
        end_idx = offset + limit
        paginated_rules = rules_with_data[start_idx:end_idx]

        for rule, _, latest_date, count in paginated_rules:
            rule.latest_match_date = latest_date
            rule.transaction_count = count

        return [rule for rule, _, _, _ in paginated_rules]

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
        query = self._apply_common_filters(
            query,
            description_search=description_search,
            category_ids=category_ids,
            counterparty_account_ids=counterparty_account_ids,
            match_type=match_type,
            source=source,
            rule_status_filter=rule_status_filter,
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
            .join(EnhancementRulePattern, EnhancementRulePattern.rule_id == EnhancementRule.id)
            .filter(
                EnhancementRulePattern.normalized_description == normalized_description,
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
            .join(EnhancementRulePattern, EnhancementRulePattern.rule_id == EnhancementRule.id)
            .filter(
                EnhancementRule.user_id == user_id,
                or_(
                    and_(
                        EnhancementRulePattern.match_type == MatchType.EXACT,
                        EnhancementRulePattern.normalized_description == normalized_description,
                    ),
                    and_(
                        EnhancementRulePattern.match_type == MatchType.PREFIX,
                        func.lower(normalized_description).like(
                            func.lower(EnhancementRulePattern.normalized_description) + "%"
                        ),
                    ),
                    and_(
                        EnhancementRulePattern.match_type == MatchType.INFIX,
                        func.lower(normalized_description).like(
                            "%" + func.lower(EnhancementRulePattern.normalized_description) + "%"
                        ),
                    ),
                ),
            )
            .order_by(
                EnhancementRulePattern.match_type.asc(),
                EnhancementRule.created_at.asc(),
            )
            .distinct()
            .all()
        )

    def get_description_to_rule_map(self, user_id: UUID) -> dict:
        rows = (
            self.db.query(EnhancementRulePattern.normalized_description, EnhancementRule.id)
            .join(EnhancementRule, EnhancementRule.id == EnhancementRulePattern.rule_id)
            .filter(EnhancementRule.user_id == user_id)
            .all()
        )
        return {description: rule_id for description, rule_id in rows}

    def find_matching_rules_batch(self, normalized_descriptions: List[str], user_id: UUID) -> List[EnhancementRule]:
        if not normalized_descriptions:
            return []

        conditions = []
        for description in normalized_descriptions:
            conditions.append(
                or_(
                    and_(
                        EnhancementRulePattern.match_type == MatchType.EXACT,
                        func.lower(EnhancementRulePattern.normalized_description) == func.lower(description),
                    ),
                    and_(
                        EnhancementRulePattern.match_type == MatchType.PREFIX,
                        func.lower(description).like(func.lower(EnhancementRulePattern.normalized_description) + "%"),
                    ),
                    and_(
                        EnhancementRulePattern.match_type == MatchType.INFIX,
                        func.lower(description).like("%" + func.lower(EnhancementRulePattern.normalized_description) + "%"),
                    ),
                )
            )

        rows = (
            self.db.query(EnhancementRule)
            .join(EnhancementRulePattern, EnhancementRulePattern.rule_id == EnhancementRule.id)
            .filter(EnhancementRule.user_id == user_id, or_(*conditions))
            .order_by(
                EnhancementRulePattern.match_type.asc(),
                EnhancementRule.created_at.asc(),
            )
            .all()
        )

        seen: set[UUID] = set()
        unique_rules: List[EnhancementRule] = []
        for rule in rows:
            if rule.id in seen:
                continue
            seen.add(rule.id)
            unique_rules.append(rule)
        return unique_rules
