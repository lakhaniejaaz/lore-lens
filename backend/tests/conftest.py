import os

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://lore_lens_user:lore_lens_password@localhost:5432/lore_lens_db",
)
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")
os.environ.setdefault("ENVIRONMENT", "local")

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
if not TEST_DATABASE_URL:
    raise RuntimeError(
        "TEST_DATABASE_URL environment variable must be set to run the test suite, "
        "e.g. postgresql+psycopg://lore_lens_user:lore_lens_password@localhost:5432/lore_lens_test_db"
    )

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.session import get_db
from app.main import app

test_engine = create_engine(TEST_DATABASE_URL)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


@pytest.fixture
def db_session():
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()
        with test_engine.connect() as conn:
            conn.execute(text("TRUNCATE TABLE users RESTART IDENTITY CASCADE"))
            conn.commit()


@pytest.fixture
def client(db_session):
    def _get_db_override():
        yield db_session

    app.dependency_overrides[get_db] = _get_db_override
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def valid_payload():
    return {
        "first_name": "Ada",
        "last_name": "Lovelace",
        "username": "ada_lovelace",
        "email": "ada@example.com",
        "password": "correct-horse",
    }
