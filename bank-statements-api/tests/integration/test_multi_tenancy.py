from datetime import date
from decimal import Decimal
from uuid import uuid4

from app.adapters.repositories.account import SQLAlchemyAccountRepository
from app.adapters.repositories.category import SQLAlchemyCategoryRepository
from app.adapters.repositories.description_group import SQLAlchemyDescriptionGroupRepository
from app.adapters.repositories.enhancement_rule import SQLAlchemyEnhancementRuleRepository
from app.adapters.repositories.statement import SqlAlchemyStatementRepository
from app.adapters.repositories.transaction import SQLAlchemyTransactionRepository
from app.domain.models.description_group import DescriptionGroup
from app.domain.models.enhancement_rule import EnhancementRule
from app.domain.models.statement import Statement
from app.domain.models.transaction import Transaction


class TestAccountMultiTenancy:
    def test_user_can_only_see_own_accounts(self, db_session, user_a, user_b, account_for_user_a, account_for_user_b):
        repo = SQLAlchemyAccountRepository(db_session)

        user_a_accounts = repo.get_all(user_a.id)
        user_b_accounts = repo.get_all(user_b.id)

        assert len(user_a_accounts) == 1
        assert user_a_accounts[0].id == account_for_user_a.id
        assert len(user_b_accounts) == 1
        assert user_b_accounts[0].id == account_for_user_b.id

    def test_user_cannot_get_other_users_account_by_id(
        self, db_session, user_a, user_b, account_for_user_a, account_for_user_b
    ):
        repo = SQLAlchemyAccountRepository(db_session)

        result = repo.get_by_id(account_for_user_b.id, user_a.id)
        assert result is None

        result = repo.get_by_id(account_for_user_a.id, user_b.id)
        assert result is None

    def test_user_can_get_own_account_by_id(self, db_session, user_a, account_for_user_a):
        repo = SQLAlchemyAccountRepository(db_session)

        result = repo.get_by_id(account_for_user_a.id, user_a.id)
        assert result is not None
        assert result.id == account_for_user_a.id


class TestCategoryMultiTenancy:
    def test_user_can_only_see_own_categories(self, db_session, user_a, user_b, category_for_user_a, category_for_user_b):
        repo = SQLAlchemyCategoryRepository(db_session)

        user_a_categories = repo.get_all(user_a.id)
        user_b_categories = repo.get_all(user_b.id)

        assert len(user_a_categories) == 1
        assert user_a_categories[0].id == category_for_user_a.id
        assert len(user_b_categories) == 1
        assert user_b_categories[0].id == category_for_user_b.id

    def test_user_cannot_get_other_users_category_by_id(
        self, db_session, user_a, user_b, category_for_user_a, category_for_user_b
    ):
        repo = SQLAlchemyCategoryRepository(db_session)

        result = repo.get_by_id(category_for_user_b.id, user_a.id)
        assert result is None

        result = repo.get_by_id(category_for_user_a.id, user_b.id)
        assert result is None


class TestTransactionMultiTenancy:
    def test_user_can_only_see_transactions_from_own_accounts(
        self, db_session, user_a, user_b, account_for_user_a, account_for_user_b
    ):
        stmt_a = Statement(
            id=uuid4(),
            filename="user_a.csv",
            file_type="CSV",
            content=b"test",
            account_id=account_for_user_a.id,
        )
        stmt_b = Statement(
            id=uuid4(),
            filename="user_b.csv",
            file_type="CSV",
            content=b"test",
            account_id=account_for_user_b.id,
        )
        db_session.add(stmt_a)
        db_session.add(stmt_b)
        db_session.flush()

        tx_a = Transaction(
            id=uuid4(),
            date=date(2024, 1, 1),
            description="User A Transaction",
            normalized_description="user a transaction",
            amount=Decimal("100.00"),
            account_id=account_for_user_a.id,
            statement_id=stmt_a.id,
            row_index=0,
        )
        tx_b = Transaction(
            id=uuid4(),
            date=date(2024, 1, 1),
            description="User B Transaction",
            normalized_description="user b transaction",
            amount=Decimal("200.00"),
            account_id=account_for_user_b.id,
            statement_id=stmt_b.id,
            row_index=0,
        )
        db_session.add(tx_a)
        db_session.add(tx_b)
        db_session.flush()

        repo = SQLAlchemyTransactionRepository(db_session)

        user_a_txs = repo.get_all(user_a.id)
        user_b_txs = repo.get_all(user_b.id)

        assert len(user_a_txs) == 1
        assert user_a_txs[0].id == tx_a.id
        assert len(user_b_txs) == 1
        assert user_b_txs[0].id == tx_b.id

    def test_user_cannot_get_other_users_transaction_by_id(
        self, db_session, user_a, user_b, account_for_user_a, account_for_user_b
    ):
        stmt_a = Statement(
            id=uuid4(),
            filename="user_a.csv",
            file_type="CSV",
            content=b"test",
            account_id=account_for_user_a.id,
        )
        db_session.add(stmt_a)
        db_session.flush()

        tx_a = Transaction(
            id=uuid4(),
            date=date(2024, 1, 1),
            description="User A Transaction",
            normalized_description="user a transaction",
            amount=Decimal("100.00"),
            account_id=account_for_user_a.id,
            statement_id=stmt_a.id,
            row_index=0,
        )
        db_session.add(tx_a)
        db_session.flush()

        repo = SQLAlchemyTransactionRepository(db_session)

        result = repo.get_by_id(tx_a.id, user_b.id)
        assert result is None

        result = repo.get_by_id(tx_a.id, user_a.id)
        assert result is not None
        assert result.id == tx_a.id


class TestStatementMultiTenancy:
    def test_user_can_only_see_statements_from_own_accounts(
        self, db_session, user_a, user_b, account_for_user_a, account_for_user_b
    ):
        stmt_a = Statement(
            id=uuid4(),
            filename="user_a.csv",
            file_type="CSV",
            content=b"test",
            account_id=account_for_user_a.id,
        )
        stmt_b = Statement(
            id=uuid4(),
            filename="user_b.csv",
            file_type="CSV",
            content=b"test",
            account_id=account_for_user_b.id,
        )
        db_session.add(stmt_a)
        db_session.add(stmt_b)
        db_session.flush()

        repo = SqlAlchemyStatementRepository(db_session)

        user_a_stmts = repo.find_all(user_a.id)
        user_b_stmts = repo.find_all(user_b.id)

        assert len(user_a_stmts) == 1
        assert user_a_stmts[0].id == stmt_a.id
        assert len(user_b_stmts) == 1
        assert user_b_stmts[0].id == stmt_b.id

    def test_user_cannot_get_other_users_statement_by_id(
        self, db_session, user_a, user_b, account_for_user_a, account_for_user_b
    ):
        stmt_a = Statement(
            id=uuid4(),
            filename="user_a.csv",
            file_type="CSV",
            content=b"test",
            account_id=account_for_user_a.id,
        )
        db_session.add(stmt_a)
        db_session.flush()

        repo = SqlAlchemyStatementRepository(db_session)

        result = repo.find_by_id(stmt_a.id, user_b.id)
        assert result is None

        result = repo.find_by_id(stmt_a.id, user_a.id)
        assert result is not None
        assert result.id == stmt_a.id


class TestEnhancementRuleMultiTenancy:
    def test_user_can_only_see_own_enhancement_rules(self, db_session, user_a, user_b):
        from app.domain.models.enhancement_rule import EnhancementRuleSource, MatchType

        rule_a = EnhancementRule(
            id=uuid4(),
            normalized_description_pattern="test rule a",
            match_type=MatchType.EXACT,
            source=EnhancementRuleSource.MANUAL,
            user_id=user_a.id,
        )
        rule_b = EnhancementRule(
            id=uuid4(),
            normalized_description_pattern="test rule b",
            match_type=MatchType.EXACT,
            source=EnhancementRuleSource.MANUAL,
            user_id=user_b.id,
        )
        db_session.add(rule_a)
        db_session.add(rule_b)
        db_session.flush()

        repo = SQLAlchemyEnhancementRuleRepository(db_session)

        user_a_rules = repo.get_all(user_id=user_a.id)
        user_b_rules = repo.get_all(user_id=user_b.id)

        assert len(user_a_rules) == 1
        assert user_a_rules[0].id == rule_a.id
        assert len(user_b_rules) == 1
        assert user_b_rules[0].id == rule_b.id

    def test_user_cannot_get_other_users_rule_by_id(self, db_session, user_a, user_b):
        from app.domain.models.enhancement_rule import EnhancementRuleSource, MatchType

        rule_a = EnhancementRule(
            id=uuid4(),
            normalized_description_pattern="test rule a",
            match_type=MatchType.EXACT,
            source=EnhancementRuleSource.MANUAL,
            user_id=user_a.id,
        )
        db_session.add(rule_a)
        db_session.flush()

        repo = SQLAlchemyEnhancementRuleRepository(db_session)

        result = repo.find_by_id(rule_a.id, user_b.id)
        assert result is None

        result = repo.find_by_id(rule_a.id, user_a.id)
        assert result is not None
        assert result.id == rule_a.id


class TestDescriptionGroupMultiTenancy:
    def test_user_can_only_see_own_description_groups(self, db_session, user_a, user_b):
        group_a = DescriptionGroup(
            id=uuid4(),
            name="Group A",
            user_id=user_a.id,
        )
        group_b = DescriptionGroup(
            id=uuid4(),
            name="Group B",
            user_id=user_b.id,
        )
        db_session.add(group_a)
        db_session.add(group_b)
        db_session.flush()

        repo = SQLAlchemyDescriptionGroupRepository(db_session)

        user_a_groups = repo.get_all(user_a.id)
        user_b_groups = repo.get_all(user_b.id)

        assert len(user_a_groups) == 1
        assert user_a_groups[0].id == group_a.id
        assert len(user_b_groups) == 1
        assert user_b_groups[0].id == group_b.id

    def test_user_cannot_get_other_users_group_by_id(self, db_session, user_a, user_b):
        group_a = DescriptionGroup(
            id=uuid4(),
            name="Group A",
            user_id=user_a.id,
        )
        db_session.add(group_a)
        db_session.flush()

        repo = SQLAlchemyDescriptionGroupRepository(db_session)

        result = repo.get_by_id(group_a.id, user_b.id)
        assert result is None

        result = repo.get_by_id(group_a.id, user_a.id)
        assert result is not None
        assert result.id == group_a.id
