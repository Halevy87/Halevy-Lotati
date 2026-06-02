import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Use a dedicated test database on the local Postgres (override via TEST_DATABASE_URL).
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg2://halevy:halevy@localhost:5544/halevy_test",
)

from app.core import db as db_module  # noqa: E402

test_engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)

# Point the app's engine/session at the test DB before models/app import metadata usage.
db_module.engine = test_engine
db_module.SessionLocal = TestingSessionLocal

from app.core.db import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.enums import UserRole  # noqa: E402
from app.models.user import User  # noqa: E402


@pytest.fixture(autouse=True)
def _schema():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    def _override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def dev_user(db):
    user = User(
        email="ron@halevi-luttati.example",
        full_name="רון הלוי",
        role=UserRole.partner,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
