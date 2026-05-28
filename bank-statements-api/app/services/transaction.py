from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from app.api.schemas import TransactionCreateRequest, TransactionListResponse
from app.common.text_normalization import normalize_description
from app.domain.dto.statement_processing import TransactionDTO
from app.domain.models.category import CategoryKind, CategoryPriority
from app.domain.models.enhancement_rule import EnhancementRule, EnhancementRuleSource, MatchType
from app.domain.models.transaction import CategorizationStatus, SourceType, Transaction
from app.ports.repositories.category import CategoryRepository
from app.ports.repositories.enhancement_rule import EnhancementRuleRepository
from app.ports.repositories.initial_balance import InitialBalanceRepository
from app.ports.repositories.transaction import TransactionRepository
from app.services.transaction_enhancement import TransactionEnhancer


class ConflictError(Exception):
    pass


TransactionSplitConflictError = ConflictError


class TransactionPersistenceResult:
    def __init__(self, transactions_saved: int, duplicates_found: int):
        self.transactions_saved = transactions_saved
        self.duplicates_found = duplicates_found


class TransactionService:
    """
    Application service for transaction operations.
    Contains business logic and uses the repository port.
    """

    def __init__(
        self,
        transaction_repository: TransactionRepository,
        initial_balance_repository: InitialBalanceRepository,
        enhancement_rule_repository: EnhancementRuleRepository,
        transaction_enhancer: TransactionEnhancer,
        category_repository: Optional[CategoryRepository] = None,
    ):
        self.transaction_repository = transaction_repository
        self.initial_balance_repository = initial_balance_repository
        self.enhancement_rule_repository = enhancement_rule_repository
        self.transaction_enhancer = transaction_enhancer
        self.category_repository = category_repository

    def _expand_category_ids(self, category_ids: Optional[List[UUID]], user_id: UUID) -> Optional[List[UUID]]:
        if not category_ids or not self.category_repository:
            return category_ids
        return self.category_repository.get_all_descendant_ids(category_ids, user_id)

    def create_transaction(
        self,
        user_id: UUID,
        transaction_data: TransactionCreateRequest,
        after_transaction_id: Optional[UUID] = None,
    ) -> Transaction:
        enhanced_data = transaction_data

        if transaction_data.category_id is None:
            normalized_description = normalize_description(transaction_data.description)

            matching_rules = self.enhancement_rule_repository.find_matching_rules_batch([normalized_description], user_id)

            if matching_rules:
                temp_transaction = Transaction(
                    id=uuid4(),
                    date=transaction_data.date,
                    description=transaction_data.description,
                    normalized_description=normalized_description,
                    amount=transaction_data.amount,
                    account_id=transaction_data.account_id,
                    statement_id=None,
                    source_type=SourceType.MANUAL,
                    categorization_status=CategorizationStatus.UNCATEGORIZED,
                )

                matching_rule = None
                for rule in matching_rules:
                    if rule.matches_transaction(temp_transaction):
                        matching_rule = rule
                        break

                if matching_rule:
                    enhanced_data = TransactionCreateRequest(
                        date=transaction_data.date,
                        description=transaction_data.description,
                        amount=transaction_data.amount,
                        account_id=transaction_data.account_id,
                        category_id=matching_rule.category_id,
                        counterparty_account_id=matching_rule.counterparty_account_id,
                        after_transaction_id=transaction_data.after_transaction_id,
                    )
                else:
                    self._create_unmatched_rule(user_id, normalized_description)
            else:
                self._create_unmatched_rule(user_id, normalized_description)

        return self.transaction_repository.create_transaction(
            user_id=user_id,
            transaction_data=enhanced_data,
            after_transaction_id=after_transaction_id,
        )

    def _create_unmatched_rule(self, user_id: UUID, normalized_description: str) -> None:
        existing_rule = self.enhancement_rule_repository.find_by_normalized_description(normalized_description, user_id)

        if existing_rule:
            return

        from app.domain.models.enhancement_rule_pattern import EnhancementRulePattern

        rule = EnhancementRule(
            id=uuid4(),
            user_id=user_id,
            category_id=None,
            counterparty_account_id=None,
            source=EnhancementRuleSource.AUTO,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        rule.patterns = [
            EnhancementRulePattern(
                normalized_description=normalized_description,
                match_type=MatchType.EXACT,
                sort_order=0,
            )
        ]

        self.enhancement_rule_repository.save(rule)

    def get_transaction(self, transaction_id: UUID, user_id: UUID) -> Optional[Transaction]:
        transaction = self.transaction_repository.get_by_id(transaction_id, user_id)
        if transaction is not None:
            transaction.is_split_parent = self.transaction_repository.has_split_children(transaction.id, user_id)
        return transaction

    def get_all_transactions(self, user_id: UUID) -> List[Transaction]:
        return self.transaction_repository.get_all(user_id)

    def toggle_exclude_from_analytics(
        self,
        transaction_id: UUID,
        user_id: UUID,
        exclude_from_analytics: bool,
    ) -> Optional[Transaction]:
        transaction = self.transaction_repository.get_by_id(transaction_id, user_id)
        if not transaction:
            return None

        transaction.exclude_from_analytics = exclude_from_analytics
        return self.transaction_repository.update(transaction)

    def get_transactions_paginated(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
        category_ids: Optional[List[UUID]] = None,
        status: Optional[CategorizationStatus] = None,
        min_amount: Optional[Decimal] = None,
        max_amount: Optional[Decimal] = None,
        description_search: Optional[str] = None,
        account_id: Optional[UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        include_running_balance: bool = False,
        sort_field: Optional[str] = None,
        sort_direction: Optional[str] = None,
        exclude_uncategorized: Optional[bool] = None,
        transaction_type: Optional[str] = None,
        transaction_ids: Optional[List[UUID]] = None,
        tag_ids: Optional[List[UUID]] = None,
        exclude_from_analytics: Optional[bool] = None,
        kinds: Optional[List[CategoryKind]] = None,
        priorities: Optional[List[CategoryPriority]] = None,
    ) -> TransactionListResponse:
        expanded_category_ids = self._expand_category_ids(category_ids, user_id)
        kwargs = dict(
            user_id=user_id,
            page=page,
            page_size=page_size,
            category_ids=expanded_category_ids,
            status=status,
            min_amount=min_amount,
            max_amount=max_amount,
            description_search=description_search,
            account_id=account_id,
            start_date=start_date,
            end_date=end_date,
            sort_field=sort_field,
            sort_direction=sort_direction,
            exclude_uncategorized=exclude_uncategorized,
            transaction_type=transaction_type,
            transaction_ids=transaction_ids,
            tag_ids=tag_ids,
            exclude_from_analytics=exclude_from_analytics,
            kinds=kinds,
            priorities=priorities,
        )
        (
            transactions,
            total,
            total_amount,
        ) = self.transaction_repository.get_paginated(**kwargs)

        if include_running_balance and account_id is not None:
            self._add_running_balance_to_transactions(transactions, account_id)

        if transactions:
            split_parent_ids = self.transaction_repository.get_split_parent_ids([t.id for t in transactions])
            for t in transactions:
                t.is_split_parent = t.id in split_parent_ids

        total_pages = (total + page_size - 1) // page_size if total > 0 else 1

        return TransactionListResponse(
            transactions=transactions,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            total_amount=total_amount,
        )

    def get_transactions_matching_rule_paginated(
        self,
        user_id: UUID,
        enhancement_rule_id: UUID,
        page: int = 1,
        page_size: int = 20,
        sort_field: Optional[str] = None,
        sort_direction: Optional[str] = None,
        include_running_balance: bool = False,
        uncategorized_only: bool = False,
    ) -> TransactionListResponse:
        rule = self.enhancement_rule_repository.find_by_id(enhancement_rule_id, user_id)
        if not rule:
            raise ValueError(f"Enhancement rule with ID {enhancement_rule_id} not found")

        (
            transactions,
            total,
            total_amount,
        ) = self.transaction_repository.get_transactions_matching_rule_paginated(
            user_id=user_id,
            rule=rule,
            page=page,
            page_size=page_size,
            sort_field=sort_field,
            sort_direction=sort_direction,
            uncategorized_only=uncategorized_only,
        )

        if include_running_balance:
            pass

        total_pages = (total + page_size - 1) // page_size if total > 0 else 1

        response = TransactionListResponse(
            transactions=transactions,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            total_amount=total_amount,
        )

        response.enhancement_rule = rule

        return response

    def _add_running_balance_to_transactions(
        self,
        transactions: List[Transaction],
        account_id: UUID,
    ):
        if not transactions:
            return

        latest_balance = self.initial_balance_repository.get_latest_by_account_id(account_id)
        starting_balance = latest_balance.balance_amount if latest_balance else Decimal("0.00")

        transaction_ids = [t.id for t in transactions]
        balances = self.transaction_repository.get_running_balances(
            account_id=account_id,
            transaction_ids=transaction_ids,
            initial_balance=starting_balance,
        )

        for transaction in transactions:
            transaction.running_balance = balances.get(transaction.id)

    def get_category_totals(
        self,
        user_id: UUID,
        category_ids: Optional[List[UUID]] = None,
        status: Optional[CategorizationStatus] = None,
        min_amount: Optional[Decimal] = None,
        max_amount: Optional[Decimal] = None,
        description_search: Optional[str] = None,
        account_id: Optional[UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        exclude_uncategorized: Optional[bool] = None,
        transaction_type: Optional[str] = None,
        kinds: Optional[List[CategoryKind]] = None,
    ) -> Dict[Optional[UUID], Dict[str, Decimal]]:
        expanded_category_ids = self._expand_category_ids(category_ids, user_id)
        return self.transaction_repository.get_category_totals(
            user_id=user_id,
            category_ids=expanded_category_ids,
            status=status,
            min_amount=min_amount,
            max_amount=max_amount,
            description_search=description_search,
            account_id=account_id,
            start_date=start_date,
            end_date=end_date,
            exclude_uncategorized=exclude_uncategorized,
            transaction_type=transaction_type,
            exclude_from_analytics=True,
            kinds=kinds,
        )

    def get_category_time_series(
        self,
        user_id: UUID,
        category_id: Optional[UUID] = None,
        period: str = "month",
        category_ids: Optional[List[UUID]] = None,
        status: Optional[CategorizationStatus] = None,
        min_amount: Optional[Decimal] = None,
        max_amount: Optional[Decimal] = None,
        description_search: Optional[str] = None,
        account_id: Optional[UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        exclude_uncategorized: Optional[bool] = None,
        transaction_type: Optional[str] = None,
        kinds: Optional[List[CategoryKind]] = None,
    ) -> List[Dict]:
        expanded_category_ids = self._expand_category_ids(category_ids, user_id)
        return self.transaction_repository.get_category_time_series(
            user_id=user_id,
            category_id=category_id,
            period=period,
            category_ids=expanded_category_ids,
            status=status,
            min_amount=min_amount,
            max_amount=max_amount,
            description_search=description_search,
            account_id=account_id,
            start_date=start_date,
            end_date=end_date,
            exclude_uncategorized=exclude_uncategorized,
            transaction_type=transaction_type,
            exclude_from_analytics=True,
            kinds=kinds,
        )

    def get_income_spending_time_series(
        self,
        user_id: UUID,
        period: str = "month",
        account_id: Optional[UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        exclude_uncategorized: Optional[bool] = None,
        kinds: Optional[List[CategoryKind]] = None,
    ) -> List[Dict]:
        return self.transaction_repository.get_income_spending_time_series(
            user_id=user_id,
            period=period,
            account_id=account_id,
            start_date=start_date,
            end_date=end_date,
            exclude_uncategorized=exclude_uncategorized,
            exclude_from_analytics=True,
            kinds=kinds,
        )

    def update_transaction(
        self,
        user_id: UUID,
        transaction_id: UUID,
        transaction_date: date,
        description: str,
        amount: Decimal,
        account_id: UUID,
        category_id: Optional[UUID] = None,
        counterparty_account_id: Optional[UUID] = None,
    ) -> Optional[Transaction]:
        transaction = self.transaction_repository.get_by_id(transaction_id, user_id)
        if transaction:
            transaction.date = transaction_date
            transaction.description = description
            transaction.normalized_description = normalize_description(description)
            transaction.amount = amount
            transaction.category_id = category_id
            transaction.categorization_status = (
                CategorizationStatus.MANUAL if category_id else CategorizationStatus.UNCATEGORIZED
            )
            transaction.account_id = account_id  # type: ignore
            transaction.counterparty_account_id = counterparty_account_id  # type: ignore
            return self.transaction_repository.update(transaction)
        return None

    def get_split_children(self, transaction_id: UUID, user_id: UUID) -> List[Transaction]:
        return self.transaction_repository.get_split_children(transaction_id, user_id)

    def unsplit_transaction(self, transaction_id: UUID, user_id: UUID) -> Optional[Transaction]:
        parent = self.transaction_repository.get_by_id(transaction_id, user_id)
        if parent is None:
            return None

        if not self.transaction_repository.has_split_children(parent.id, user_id):
            raise TransactionSplitConflictError("Transaction is not a split parent")

        parent.exclude_from_analytics = False
        return self.transaction_repository.unsplit_transaction(parent)

    def split_transaction(
        self,
        transaction_id: UUID,
        user_id: UUID,
        parts: List[Dict],
    ) -> Optional[List[Transaction]]:
        parent = self.transaction_repository.get_by_id(transaction_id, user_id)
        if parent is None:
            return None

        if parent.parent_transaction_id is not None:
            raise TransactionSplitConflictError("Cannot split a child transaction")

        # If already split, delete existing children to allow re-splitting

        if len(parts) < 2:
            raise ValueError("At least two parts are required")

        parts_amounts = [Decimal(str(p["amount"])) for p in parts]
        total = sum(parts_amounts)
        tolerance = Decimal("0.01")

        if abs(total - parent.amount) > tolerance:
            raise ValueError("Parts do not sum to parent amount")

        if total != parent.amount:
            parts_amounts[-1] = parent.amount - sum(parts_amounts[:-1])

        children = []
        for i, (part, amount) in enumerate(zip(parts, parts_amounts)):
            child = Transaction(
                id=uuid4(),
                user_id=parent.user_id,
                date=parent.date,
                description=part.get("description") or parent.description,
                normalized_description=normalize_description(part.get("description") or parent.description),
                amount=amount,
                account_id=parent.account_id,
                statement_id=parent.statement_id,
                source_type=parent.source_type,
                categorization_status=(
                    CategorizationStatus.MANUAL if part.get("category_id") else CategorizationStatus.UNCATEGORIZED
                ),
                sort_index=i,
                row_index=i,
                parent_transaction_id=parent.id,
                category_id=part.get("category_id"),
            )
            children.append(child)

        parent.category_id = None
        parent.categorization_status = CategorizationStatus.UNCATEGORIZED
        parent.exclude_from_analytics = True

        self.transaction_repository.split_transaction(parent, children)

        return children

    def auto_split_with_rule(self, transaction: Transaction, rule: EnhancementRule) -> Optional[List[Transaction]]:
        if not rule.split_lines:
            return None
        if transaction.parent_transaction_id is not None:
            return None

        parts = self._build_split_parts_from_rule(rule, transaction.amount)
        if parts is None:
            return None

        return self.split_transaction(transaction.id, transaction.user_id, parts)

    def _build_split_parts_from_rule(self, rule: EnhancementRule, parent_amount: Decimal) -> Optional[List[Dict]]:
        sign = Decimal(-1) if parent_amount < 0 else Decimal(1)
        total_abs = abs(parent_amount)

        fixed_sum = Decimal(0)
        remainder_line = None
        ordered_lines = sorted(rule.split_lines, key=lambda line: line.sort_order)

        parts: List[Dict] = []
        for line in ordered_lines:
            if line.is_remainder:
                remainder_line = line
                parts.append({"_remainder": True, "category_id": line.category_id, "description": line.label})
                continue
            fixed_sum += Decimal(line.amount)
            parts.append(
                {
                    "amount": (Decimal(line.amount) * sign).quantize(Decimal("0.01")),
                    "category_id": line.category_id,
                    "description": line.label,
                }
            )

        if remainder_line is None:
            return None

        remainder_abs = total_abs - fixed_sum
        if remainder_abs <= 0:
            return None

        for part in parts:
            if part.get("_remainder"):
                part.pop("_remainder")
                part["amount"] = (remainder_abs * sign).quantize(Decimal("0.01"))

        return parts

    def apply_split_templates_for_statement(self, user_id: UUID, statement_id: UUID) -> int:
        new_transactions = self.transaction_repository.get_by_statement_id(statement_id)
        new_transactions = [t for t in new_transactions if t.user_id == user_id and t.parent_transaction_id is None]
        if not new_transactions:
            return 0

        return self._apply_split_templates_to(new_transactions, user_id)

    def _apply_split_templates_to(self, transactions: List[Transaction], user_id: UUID) -> int:
        normalized_descriptions = list({t.normalized_description for t in transactions})
        rules = self.enhancement_rule_repository.find_matching_rules_batch(normalized_descriptions, user_id)
        rules_with_template = [r for r in rules if r.split_lines]
        if not rules_with_template:
            return 0

        ordered_rules = sorted(rules_with_template, key=_rule_specificity_key_for_split)

        split_count = 0
        for transaction in transactions:
            matched_rule = next(
                (rule for rule in ordered_rules if rule.matches_transaction(transaction)),
                None,
            )
            if matched_rule is None:
                continue
            children = self.auto_split_with_rule(transaction, matched_rule)
            if children:
                split_count += 1
        return split_count

    def delete_transaction(self, transaction_id: UUID, user_id: UUID) -> bool:
        return self.transaction_repository.delete(transaction_id, user_id)

    def categorize_transaction(
        self,
        user_id: UUID,
        transaction_id: UUID,
        category_id: Optional[UUID],
    ) -> Optional[Transaction]:
        transaction = self.transaction_repository.get_by_id(transaction_id, user_id)
        if not transaction:
            return None

        transaction.category_id = category_id
        transaction.categorization_status = CategorizationStatus.MANUAL if category_id else CategorizationStatus.UNCATEGORIZED

        return self.transaction_repository.update(transaction)

    def mark_categorization_failure(self, transaction_id: UUID, user_id: UUID) -> Optional[Transaction]:
        transaction = self.transaction_repository.get_by_id(transaction_id, user_id)
        if not transaction:
            return None

        transaction.categorization_status = CategorizationStatus.FAILURE

        return self.transaction_repository.update(transaction)

    def bulk_update_category_by_normalized_description(
        self,
        user_id: UUID,
        normalized_description: str,
        category_id: Optional[UUID],
        account_id: Optional[UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        enhancement_rule_id: Optional[UUID] = None,
    ) -> int:
        rule = None
        if enhancement_rule_id:
            rule = self.enhancement_rule_repository.find_by_id(enhancement_rule_id, user_id)
            if not rule:
                raise ValueError(f"Enhancement rule with ID {enhancement_rule_id} not found")

        return self.transaction_repository.bulk_update_category_by_normalized_description(
            user_id=user_id,
            normalized_description=normalized_description,
            category_id=category_id,
            account_id=account_id,
            start_date=start_date,
            end_date=end_date,
            rule=rule,
        )

    def bulk_categorize_by_ids(
        self,
        user_id: UUID,
        transaction_ids: List[UUID],
        category_id: Optional[UUID],
    ) -> int:
        owned_ids = self.transaction_repository.filter_owned_ids(transaction_ids, user_id)
        if not owned_ids:
            return 0

        return self.transaction_repository.bulk_update_category_by_ids(
            transaction_ids=owned_ids,
            category_id=category_id,
            user_id=user_id,
        )

    def count_by_normalized_description(
        self,
        user_id: UUID,
        normalized_description: str,
        account_id: Optional[UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        enhancement_rule_id: Optional[UUID] = None,
    ) -> int:
        rule = None
        if enhancement_rule_id:
            rule = self.enhancement_rule_repository.find_by_id(enhancement_rule_id, user_id)
            if not rule:
                raise ValueError(f"Enhancement rule with ID {enhancement_rule_id} not found")

        return self.transaction_repository.count_by_normalized_description(
            user_id=user_id,
            normalized_description=normalized_description,
            account_id=account_id,
            start_date=start_date,
            end_date=end_date,
            rule=rule,
        )

    def count_by_category_id(
        self,
        user_id: UUID,
        category_id: UUID,
        account_id: Optional[UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> int:
        return self.transaction_repository.count_by_category_id(
            user_id=user_id,
            category_id=category_id,
            account_id=account_id,
            start_date=start_date,
            end_date=end_date,
        )

    def bulk_update_by_category_id(
        self,
        user_id: UUID,
        from_category_id: UUID,
        to_category_id: Optional[UUID],
        account_id: Optional[UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> int:
        return self.transaction_repository.bulk_update_by_category_id(
            user_id=user_id,
            from_category_id=from_category_id,
            to_category_id=to_category_id,
            account_id=account_id,
            start_date=start_date,
            end_date=end_date,
        )

    def save_transactions_from_dtos(
        self,
        transaction_dtos: List[TransactionDTO],
    ) -> TransactionPersistenceResult:
        """
        Save multiple transactions from DTOs with count-based duplicate detection.

        For each unique (date, amount, account_id) combination:
        - Count how many exist in the import
        - Count how many already exist in DB
        - Only import the difference (import_count - db_count)

        This correctly handles legitimate same-day/same-amount transactions.
        """
        if not transaction_dtos:
            return TransactionPersistenceResult(transactions_saved=0, duplicates_found=0)

        groups = self._group_dtos_by_signature(transaction_dtos)
        db_counts = self._get_db_counts_for_groups(groups)

        transactions_to_save = []
        duplicates_found = 0

        for key, dtos in groups.items():
            import_count = len(dtos)
            db_count = db_counts.get(key, 0)
            to_import = max(0, import_count - db_count)
            duplicates_found += import_count - to_import

            for dto in dtos[:to_import]:
                transaction_entity = self._convert_dto_to_entity(dto)
                transactions_to_save.append(transaction_entity)

        if transactions_to_save:
            self.transaction_repository.create_many(transactions_to_save)

        return TransactionPersistenceResult(
            transactions_saved=len(transactions_to_save),
            duplicates_found=duplicates_found,
        )

    def _group_dtos_by_signature(
        self,
        dtos: List[TransactionDTO],
    ) -> dict:
        from collections import defaultdict

        groups = defaultdict(list)
        for dto in dtos:
            if not dto.account_id:
                raise ValueError("Transaction DTO must have an account_id for deduplication")
            date_str = dto.date if isinstance(dto.date, str) else dto.date.strftime("%Y-%m-%d")
            account_id = str(dto.account_id) if isinstance(dto.account_id, UUID) else dto.account_id
            key = (date_str, float(dto.amount), account_id)
            groups[key].append(dto)
        return dict(groups)

    def _get_db_counts_for_groups(
        self,
        groups: dict,
    ) -> dict:
        counts = {}
        for key in groups.keys():
            date_str, amount, account_id_str = key
            count = self.transaction_repository.count_by_date_and_amount(
                date=date_str,
                amount=amount,
                account_id=UUID(account_id_str),
            )
            counts[key] = count
        return counts

    def _is_duplicate_transaction(
        self,
        dto: TransactionDTO,
        processed_tx_ids: set,
    ) -> bool:
        """Check if a transaction DTO is a duplicate"""
        account_uuid = None
        if dto.account_id:
            if isinstance(dto.account_id, UUID):
                account_uuid = dto.account_id
            else:
                account_uuid = UUID(dto.account_id)

        date_str = dto.date if isinstance(dto.date, str) else dto.date.strftime("%Y-%m-%d")

        matching_transactions = self.transaction_repository.find_matching_transactions(
            date=date_str,
            description=dto.description,
            amount=float(dto.amount),
            account_id=account_uuid,
        )

        for match in matching_transactions:
            if match.id not in processed_tx_ids:
                processed_tx_ids.add(match.id)
                return True

        return False

    def _convert_dto_to_entity(self, dto: TransactionDTO) -> Transaction:
        """Convert a TransactionDTO to a Transaction entity"""
        date_val = dto.date
        if isinstance(date_val, str):
            date_val = datetime.strptime(date_val, "%Y-%m-%d").date()

        source_type_enum = SourceType.UPLOAD
        if dto.source_type == "manual":
            source_type_enum = SourceType.MANUAL

        account_uuid = None
        if dto.account_id:
            if isinstance(dto.account_id, UUID):
                account_uuid = dto.account_id
            else:
                account_uuid = UUID(dto.account_id)

        statement_uuid = None
        if dto.statement_id:
            if isinstance(dto.statement_id, UUID):
                statement_uuid = dto.statement_id
            else:
                statement_uuid = UUID(dto.statement_id)

        category_uuid = None
        if dto.category_id:
            if isinstance(dto.category_id, UUID):
                category_uuid = dto.category_id
            else:
                category_uuid = UUID(dto.category_id)

        counterparty_uuid = None
        if dto.counterparty_account_id:
            if isinstance(dto.counterparty_account_id, UUID):
                counterparty_uuid = dto.counterparty_account_id
            else:
                counterparty_uuid = UUID(dto.counterparty_account_id)

        categorization_status = dto.categorization_status or CategorizationStatus.UNCATEGORIZED

        transaction = Transaction(
            id=uuid4(),
            user_id=dto.user_id,
            date=date_val,
            amount=Decimal(str(dto.amount)),
            description=dto.description,
            normalized_description=normalize_description(dto.description),
            statement_id=statement_uuid,
            row_index=dto.row_index,
            sort_index=dto.sort_index or 0,
            source_type=source_type_enum,
            manual_position_after=dto.manual_position_after,
            category_id=category_uuid,
            counterparty_account_id=counterparty_uuid,
            categorization_status=categorization_status,
            account_id=account_uuid,
        )

        return transaction


_MATCH_TYPE_PRIORITY_FOR_SPLIT = {MatchType.EXACT: 0, MatchType.PREFIX: 1, MatchType.INFIX: 2}


def _rule_specificity_key_for_split(rule: EnhancementRule):
    constraint_count = sum(
        1 for value in (rule.min_amount, rule.max_amount, rule.start_date, rule.end_date) if value is not None
    )
    best_match_priority = min(
        (_MATCH_TYPE_PRIORITY_FOR_SPLIT.get(p.match_type, 99) for p in rule.patterns),
        default=99,
    )
    return (
        -constraint_count,
        best_match_priority,
        rule.created_at or datetime.min,
    )
