from datetime import date
from decimal import Decimal
from uuid import uuid4

from app.adapters.repositories.tag import SQLAlchemyTagRepository
from app.adapters.repositories.transaction import SQLAlchemyTransactionRepository
from app.domain.models.statement import Statement
from app.domain.models.tag import Tag
from app.domain.models.transaction import Transaction


class TestTagRepository:
    def test_create_tag_and_list(self, db_session, user_a):
        repo = SQLAlchemyTagRepository(db_session)

        repo.create(Tag(name="holiday", user_id=user_a.id))
        repo.create(Tag(name="refund", user_id=user_a.id))

        tags = repo.get_all(user_a.id)
        assert len(tags) == 2
        names = [t.name for t in tags]
        assert "holiday" in names
        assert "refund" in names

    def test_tag_transaction_association(self, db_session, user_a, account_for_user_a):
        tag_repo = SQLAlchemyTagRepository(db_session)
        tx_repo = SQLAlchemyTransactionRepository(db_session)

        stmt = Statement(
            id=uuid4(),
            filename="test.csv",
            file_type="CSV",
            content=b"test",
            account_id=account_for_user_a.id,
        )
        db_session.add(stmt)
        db_session.flush()

        tx = Transaction(
            id=uuid4(),
            user_id=user_a.id,
            date=date(2024, 1, 15),
            description="Test",
            normalized_description="test",
            amount=Decimal("50.00"),
            account_id=account_for_user_a.id,
            statement_id=stmt.id,
            row_index=0,
        )
        db_session.add(tx)
        db_session.flush()

        tag = tag_repo.create(Tag(name="tagged", user_id=user_a.id))
        tag_repo.add_to_transaction(tx.id, tag.id)

        db_session.expire_all()
        loaded_tx = tx_repo.get_by_id(tx.id, user_a.id)
        assert len(loaded_tx.tags) == 1
        assert loaded_tx.tags[0].name == "tagged"

    def test_filter_transactions_by_tag(self, db_session, user_a, account_for_user_a):
        tag_repo = SQLAlchemyTagRepository(db_session)
        tx_repo = SQLAlchemyTransactionRepository(db_session)

        stmt = Statement(
            id=uuid4(),
            filename="test.csv",
            file_type="CSV",
            content=b"test",
            account_id=account_for_user_a.id,
        )
        db_session.add(stmt)
        db_session.flush()

        tagged_tx = Transaction(
            id=uuid4(),
            user_id=user_a.id,
            date=date(2024, 2, 1),
            description="Tagged",
            normalized_description="tagged",
            amount=Decimal("10.00"),
            account_id=account_for_user_a.id,
            statement_id=stmt.id,
            row_index=0,
        )
        untagged_tx = Transaction(
            id=uuid4(),
            user_id=user_a.id,
            date=date(2024, 2, 2),
            description="Untagged",
            normalized_description="untagged",
            amount=Decimal("20.00"),
            account_id=account_for_user_a.id,
            statement_id=stmt.id,
            row_index=1,
        )
        db_session.add_all([tagged_tx, untagged_tx])
        db_session.flush()

        tag = tag_repo.create(Tag(name="important", user_id=user_a.id))
        tag_repo.add_to_transaction(tagged_tx.id, tag.id)

        results, count, _ = tx_repo.get_paginated(user_id=user_a.id, page=1, page_size=50, tag_ids=[tag.id])

        assert count == 1
        assert results[0].id == tagged_tx.id

    def test_multi_tenancy(self, db_session, user_a, user_b):
        repo = SQLAlchemyTagRepository(db_session)

        tag_a = repo.create(Tag(name="personal", user_id=user_a.id))
        repo.create(Tag(name="work", user_id=user_b.id))

        assert len(repo.get_all(user_a.id)) == 1
        assert len(repo.get_all(user_b.id)) == 1
        assert repo.get_by_id(tag_a.id, user_b.id) is None
