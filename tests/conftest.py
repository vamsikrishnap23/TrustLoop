import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import get_db, Base

# Test database setup
TEST_DATABASE_URL = "sqlite:///./test_trustloop.db"

@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine."""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    yield engine
    # Cleanup: remove test database file after all tests
    if os.path.exists("./test_trustloop.db"):
        os.remove("./test_trustloop.db")

@pytest.fixture(scope="session")
def test_session_factory(test_engine):
    """Create test session factory."""
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="function")
def test_db(test_engine, test_session_factory):
    """Create test database session for each test."""
    # Create tables
    Base.metadata.create_all(bind=test_engine)
    
    # Create session
    session = test_session_factory()
    
    def override_get_db():
        try:
            yield session
        finally:
            pass  # Don't close here, we'll close after test
    
    # Override dependency
    app.dependency_overrides[get_db] = override_get_db
    
    yield session
    
    # Cleanup
    session.close()
    Base.metadata.drop_all(bind=test_engine)
    app.dependency_overrides.clear()

@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)
