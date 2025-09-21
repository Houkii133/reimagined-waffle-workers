from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel

from app.main import app
from app.db.session import AsyncSessionLocal, get_session, sync_engine


@pytest.fixture(scope="session", autouse=True)
def create_db() -> None:
    # Ensure each test session starts from a clean schema so that metadata
    # changes on the models are reflected immediately. SQLite will happily keep
    # the old table definition around otherwise, leading to "no such column"
    # errors when the models gain new attributes.
    SQLModel.metadata.drop_all(bind=sync_engine)
    SQLModel.metadata.create_all(bind=sync_engine)


@pytest.fixture
async def session_override():
    async with AsyncSessionLocal() as session:
        yield session


@pytest.fixture
def client(session_override) -> TestClient:
    async def _get_session_override():
        async with AsyncSessionLocal() as session:
            yield session

    app.dependency_overrides[get_session] = _get_session_override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
