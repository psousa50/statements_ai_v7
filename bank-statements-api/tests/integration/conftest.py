import os
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.domain.models.account import Account
from app.domain.models.category import Category
from app.domain.models.refresh_token import RefreshToken  # noqa: F401
from app.domain.models.uploaded_file import FileAnalysisMetadata, UploadedFile  # noqa: F401
from app.domain.models.user import User

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:15432/bank_statements_test",
)


@pytest.fixture(scope="session")
def engine():
    return create_engine(TEST_DATABASE_URL)


@pytest.fixture(scope="session")
def tables(engine):
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session(engine, tables):
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def user_a(db_session):
    user = User(
        id=uuid4(),
        email="user_a@example.com",
        name="User A",
        oauth_provider="google",
        oauth_id="google-user-a",
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def user_b(db_session):
    user = User(
        id=uuid4(),
        email="user_b@example.com",
        name="User B",
        oauth_provider="google",
        oauth_id="google-user-b",
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def account_for_user_a(db_session, user_a):
    account = Account(
        id=uuid4(),
        name="User A Account",
        user_id=user_a.id,
    )
    db_session.add(account)
    db_session.flush()
    return account


@pytest.fixture
def account_for_user_b(db_session, user_b):
    account = Account(
        id=uuid4(),
        name="User B Account",
        user_id=user_b.id,
    )
    db_session.add(account)
    db_session.flush()
    return account


@pytest.fixture
def category_for_user_a(db_session, user_a):
    category = Category(
        id=uuid4(),
        name="User A Category",
        user_id=user_a.id,
    )
    db_session.add(category)
    db_session.flush()
    return category


@pytest.fixture
def category_for_user_b(db_session, user_b):
    category = Category(
        id=uuid4(),
        name="User B Category",
        user_id=user_b.id,
    )
    db_session.add(category)
    db_session.flush()
    return category
