"""
Pytest configuration and shared fixtures for all tests.

Provides:
- Gateway fixtures
- Mock event bus
- Database fixtures
- API client
- Event loop management
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
from typing import AsyncGenerator

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from backend.config import Settings
from backend.main import create_app
from src.gateway import Gateway
from core.event_bus import EventBus
from core.task_manager import TaskManager


# ============================================================================
# Event Loop Configuration
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture
def temp_db():
    """Provide temporary SQLite database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    yield db_path
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
async def db_engine(temp_db):
    """Provide SQLAlchemy async engine for test database."""
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{temp_db}",
        echo=False,
        connect_args={"check_same_thread": False},
    )
    yield engine
    await engine.dispose()


@pytest.fixture
async def test_db_session(db_engine):
    """Provide test database session."""
    async_session = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with async_session() as session:
        yield session


# ============================================================================
# Configuration Fixtures
# ============================================================================

@pytest.fixture
def test_settings():
    """Provide test settings."""
    return Settings(
        DATABASE_URL="sqlite+aiosqlite:///./test_data.db",
        ENVIRONMENT="testing",
        DEBUG=True,
    )


# ============================================================================
# Event Bus Fixtures
# ============================================================================

@pytest.fixture
def mock_event_bus():
    """Provide fresh event bus instance."""
    return EventBus()


@pytest.fixture
def mock_bus_with_subscribers(mock_event_bus):
    """Provide event bus with subscribers."""
    events_captured = []

    async def capture_event(data):
        events_captured.append(data)

    mock_event_bus.subscribe("can.tx", capture_event)
    mock_event_bus.subscribe("ble.rx", capture_event)
    mock_event_bus.subscribe("attack.event", capture_event)

    return mock_event_bus, events_captured


# ============================================================================
# Gateway Fixtures - CORRECTED
# ============================================================================

@pytest.fixture
def gateway():
    """
    Provide configured gateway instance.
    
    This is NOT an async fixture - returns object directly.
    """
    gw = Gateway()
    yield gw
    # Cleanup if running
    if gw.running:
        asyncio.run(gw.stop())


@pytest.fixture
def running_gateway():
    """
    Provide started gateway instance.
    
    This is NOT an async fixture - starts gateway synchronously.
    """
    gw = Gateway()
    # Start gateway synchronously
    asyncio.run(gw.start())
    yield gw
    # Stop gateway synchronously
    asyncio.run(gw.stop())


# ============================================================================
# API Fixtures
# ============================================================================

@pytest.fixture
def app():
    """Provide FastAPI application instance."""
    return create_app()


@pytest.fixture
def client(app):
    """Provide TestClient for API testing."""
    return TestClient(app)


@pytest.fixture
def api_headers():
    """Provide standard API headers."""
    return {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


# ============================================================================
# Task Manager Fixtures
# ============================================================================

@pytest.fixture
def clean_task_manager():
    """Provide clean task manager instance."""
    tm = TaskManager()
    yield tm
    asyncio.run(tm.shutdown_all())


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )