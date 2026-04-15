import asyncio
import os
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
import pandas as pd

# Ensure project root is in path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.api.main import app, state
from src.db.models import Base, User
from src.db.config import get_async_session
from src.generator.synthetic_env import AdvancedAirlineSimulator

# Use a real file for the test database to ensure persistence across connections
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_aviation_fixture.db"

@pytest_asyncio.fixture(scope="session")
async def setup_test_db():
    """Ensure the test DB is clean before and after the session."""
    db_file = "./test_aviation_fixture.db"
    if os.path.exists(db_file):
        os.remove(db_file)
    yield
    if os.path.exists(db_file):
        os.remove(db_file)

@pytest_asyncio.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture
async def test_session(test_engine, monkeypatch):
    session_maker = async_sessionmaker(test_engine, expire_on_commit=False)
    
    # Monkeypatch the global session maker in src.db.config
    import src.db.config
    monkeypatch.setattr(src.db.config, "async_session_maker", session_maker)
    
    async with session_maker() as session:
        yield session
        await session.rollback()

@pytest_asyncio.fixture
async def seed_state():
    """Seed the global AppState with a small scenario for testing."""
    sim = AdvancedAirlineSimulator(seed=42)
    state.df = sim.generate_full_scenario(days=1).head(50)
    # Ensure all required columns are present
    from src.api.main import _normalize_scenario
    state.df = _normalize_scenario(state.df)

@pytest_asyncio.fixture
async def client(test_session, seed_state):
    def override_get_async_session():
        return test_session

    app.dependency_overrides[get_async_session] = override_get_async_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

@pytest_asyncio.fixture
async def test_user(test_session):
    from fastapi_users.password import PasswordHelper
    password_helper = PasswordHelper()
    
    # Use unique email for each test invocation to avoid IntegrityError if rollback delayed
    email = f"test_{os.urandom(4).hex()}@example.com"
    user = User(
        email=email,
        hashed_password=password_helper.hash("password123"),
        is_active=True,
        is_verified=True,
        role="admin"
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    return user

@pytest_asyncio.fixture
async def auth_token(client, test_user):
    response = await client.post(
        "/api/auth/jwt/login",
        data={"username": test_user.email, "password": "password123"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]
