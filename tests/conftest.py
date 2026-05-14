"""Fixture condivise per tutti i test."""
import os
os.environ.setdefault("ADMIN_USERNAME", "testadmin")
os.environ.setdefault("ADMIN_PASSWORD_HASH", "$2b$12$BwIPtxdrYcN8aoNi/JB9WuXAFAaTyV1RErTwRKrD73iG.no6pMKMq")  # "pizza"
os.environ.setdefault("SECRET_KEY", "chiave-di-test-non-usare-in-produzione")
os.environ["RATELIMIT_ENABLED"] = "0"  # disabilita il rate limiter durante i test

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlmodel.pool import StaticPool

from app.main import app
from app.db import get_session


@pytest.fixture(name="session")
def session_fixture():
    """Sessione su DB SQLite in-memory isolata per ogni test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """TestClient con il DB in-memory iniettato."""
    def get_session_override():
        yield session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app, raise_server_exceptions=True)
    yield client
    app.dependency_overrides.clear()
