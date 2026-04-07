import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, create_engine

from app.config import Settings
from app.database import get_session
from app.main import app

settings = Settings()

# Use the real Postgres database for tests (D-47)
# Tests use transaction rollback for isolation
test_engine = create_engine(
    settings.database_url,
    poolclass=StaticPool,
)


@pytest.fixture(name="session")
def session_fixture():
    """Provide a transactional session that rolls back after each test."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """FastAPI test client with session override."""

    def get_session_override():
        yield session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
