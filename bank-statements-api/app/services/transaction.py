from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from app.api.schemas import TransactionCreateRequest, TransactionListResponse
from app.common.text_normalization import normalize_description
from app.domain.dto.statement_processing import TransactionDTO
from app.domain.models.enhancement_rule import EnhancementRule, EnhancementRuleSource, MatchType
from app.domain.models.transaction import CategorizationStatus, SourceType, Transaction
from app.ports.repositories.enhancement_rule import EnhancementRuleRepository
from app.ports.repositories.initial_balance import InitialBalanceRepository
from app.ports.repositories.transaction import TransactionRepository
from app.services.transaction_enhancement import TransactionEnhancer


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
    ):
        self.transaction_repository = transaction_repository
        self.initial_balance_repository = initial_balance_repository
        self.enhancement_rule_repository = enhancement_rule_repository
        self.transaction_enhancer = transaction_enhancer

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

        rule = EnhancementRule(
            id=uuid4(),
            user_id=user_id,
            normalized_description_pattern=normalized_description,
            match_type=MatchType.EXACT,
            category_id=None,
            counterparty_account_id=None,
            source=EnhancementRuleSource.AUTO,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        self.enhancement_rule_repository.save(rule)

    def get_transaction(self, transaction_id: UUID, user_id: UUID) -> Optional[Transaction]:
        return self.transaction_repository.get_by_id(transaction_id, user_id)

    def get_all_transactions(self, user_id: UUID) -> List[Transaction]:
        return self.transaction_repository.get_all(user_id)

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
        exclude_transfers: Optional[bool] = None,
        exclude_uncategorized: Optional[bool] = None,
        transaction_type: Optional[str] = None,
        transaction_ids: Optional[List[UUID]] = None,
    ) -> TransactionListResponse:
        (
            transactions,
            total,
            total_amount,
        ) = self.transaction_repository.get_paginated(
            user_id=user_id,
            page=page,
            page_size=page_size,
            category_ids=category_ids,
            status=status,
            min_amount=min_amount,
            max_amount=max_amount,
            description_search=description_search,
            account_id=account_id,
            start_date=start_date,
            end_date=end_date,
            sort_field=sort_field,
            sort_direction=sort_direction,
            exclude_transfers=exclude_transfers,
            exclude_uncategorized=exclude_uncategorized,
            transaction_type=transaction_type,
            transaction_ids=transaction_ids,
        )

        if include_running_balance and account_id is not None:
            self._add_running_balance_to_transactions(transactions, account_id)

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
        """Add running balance to transactions for a specific account"""
        if not transactions:
            return

        # Get the latest date from the current page of transactions
        latest_date = max(t.date for t in transactions)

        # Get all transactions up to the latest date for accurate running balance
        all_transactions = self.transaction_repository.get_all_by_account_and_date_range(
            account_id=account_id, end_date=latest_date
        )

        # Get the earliest transaction date
        earliest_date = min(t.date for t in all_transactions)

        # Get the latest initial balance before the earliest transaction date
        latest_balance = self.initial_balance_repository.get_latest_by_account_id_and_date(
            account_id=account_id, before_date=earliest_date
        )

        # For the first transactions of an account, start from 0 if no initial balance exists
        starting_balance = Decimal("0.00")
        if latest_balance and latest_balance.balance_date <= earliest_date:
            starting_balance = latest_balance.balance_amount

        # Sort all transactions by date and then by created_at (for consistent ordering of same-date transactions)
        sorted_transactions = sorted(
            all_transactions,
            key=lambda x: (x.date, x.created_at),
        )

        # Calculate running balance for all transactions
        balances = {}  # Keep track of running balance for each transaction
        current_balance = starting_balance
        for transaction in sorted_transactions:
            current_balance += transaction.amount
            balances[transaction.id] = current_balance

        # Update running balance only for transactions in the current page
        for transaction in transactions:
            transaction.running_balance = balances.get(transaction.id)

        # Note: We don't re-sort here to preserve the user's sorting preferences
        # The transactions are already sorted according to the user's sort_field and sort_direction

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
        exclude_transfers: Optional[bool] = None,
        exclude_uncategorized: Optional[bool] = None,
        transaction_type: Optional[str] = None,
    ) -> Dict[Optional[UUID], Dict[str, Decimal]]:
        return self.transaction_repository.get_category_totals(
            user_id=user_id,
            category_ids=category_ids,
            status=status,
            min_amount=min_amount,
            max_amount=max_amount,
            description_search=description_search,
            account_id=account_id,
            start_date=start_date,
            end_date=end_date,
            exclude_transfers=exclude_transfers,
            exclude_uncategorized=exclude_uncategorized,
            transaction_type=transaction_type,
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
        exclude_transfers: Optional[bool] = None,
        exclude_uncategorized: Optional[bool] = None,
        transaction_type: Optional[str] = None,
    ) -> List[Dict]:
        return self.transaction_repository.get_category_time_series(
            user_id=user_id,
            category_id=category_id,
            period=period,
            category_ids=category_ids,
            status=status,
            min_amount=min_amount,
            max_amount=max_amount,
            description_search=description_search,
            account_id=account_id,
            start_date=start_date,
            end_date=end_date,
            exclude_transfers=exclude_transfers,
            exclude_uncategorized=exclude_uncategorized,
            transaction_type=transaction_type,
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
        exclude_transfers: Optional[bool] = None,
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
            exclude_transfers=exclude_transfers,
            rule=rule,
        )

    def count_by_normalized_description(
        self,
        user_id: UUID,
        normalized_description: str,
        account_id: Optional[UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        exclude_transfers: Optional[bool] = None,
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
            exclude_transfers=exclude_transfers,
            rule=rule,
        )

    def count_by_category_id(
        self,
        user_id: UUID,
        category_id: UUID,
        account_id: Optional[UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        exclude_transfers: Optional[bool] = None,
    ) -> int:
        return self.transaction_repository.count_by_category_id(
            user_id=user_id,
            category_id=category_id,
            account_id=account_id,
            start_date=start_date,
            end_date=end_date,
            exclude_transfers=exclude_transfers,
        )

    def bulk_update_by_category_id(
        self,
        user_id: UUID,
        from_category_id: UUID,
        to_category_id: Optional[UUID],
        account_id: Optional[UUID] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        exclude_transfers: Optional[bool] = None,
    ) -> int:
        return self.transaction_repository.bulk_update_by_category_id(
            user_id=user_id,
            from_category_id=from_category_id,
            to_category_id=to_category_id,
            account_id=account_id,
            start_date=start_date,
            end_date=end_date,
            exclude_transfers=exclude_transfers,
        )

    def save_transactions_from_dtos(
        self,
        transaction_dtos: List[TransactionDTO],
    ) -> TransactionPersistenceResult:
        """
        Save multiple transactions from DTOs with duplicate detection.
        Handles DTO→Entity conversion and duplicate detection logic.
        """
        transactions_to_save = []
        duplicates_found = 0
        processed_tx_ids = set()

        for dto in transaction_dtos:
            if self._is_duplicate_transaction(dto, processed_tx_ids):
                duplicates_found += 1
                continue

            transaction_entity = self._convert_dto_to_entity(dto)
            transactions_to_save.append(transaction_entity)

        if transactions_to_save:
            self.transaction_repository.create_many(transactions_to_save)

        return TransactionPersistenceResult(
            transactions_saved=len(transactions_to_save),
            duplicates_found=duplicates_found,
        )

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
