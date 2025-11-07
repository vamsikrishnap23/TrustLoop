import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import get_db, Base

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)

@pytest.fixture(scope="function")
def setup_database():
    """Create and clean up test database for each test."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def auth_token(setup_database):
    """Create a user and return auth token."""
    # Register user
    client.post(
        "/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123"
        }
    )
    
    # Login and get token
    login_response = client.post(
        "/login",
        json={
            "username": "testuser",
            "password": "testpassword123"
        }
    )
    return login_response.json()["access_token"]

def test_create_help_request_success(auth_token):
    """Test successful help request creation."""
    response = client.post(
        "/requests",
        json={
            "title": "Need help with Python",
            "description": "I'm struggling with understanding decorators in Python. Can someone explain?"
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Need help with Python"
    assert data["description"] == "I'm struggling with understanding decorators in Python. Can someone explain?"
    assert data["created_by"] == 1  # First user should have ID 1
    assert "id" in data
    assert "created_at" in data
    assert "creator" in data
    assert data["creator"]["username"] == "testuser"
    assert data["creator"]["reputation"] == 0

def test_create_help_request_without_auth():
    """Test help request creation without authentication fails."""
    response = client.post(
        "/requests",
        json={
            "title": "Need help with Python",
            "description": "I'm struggling with understanding decorators in Python."
        }
    )
    assert response.status_code == 403  # Forbidden without auth

def test_create_help_request_invalid_token():
    """Test help request creation with invalid token fails."""
    response = client.post(
        "/requests",
        json={
            "title": "Need help with Python",
            "description": "I'm struggling with understanding decorators in Python."
        },
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401

def test_get_help_requests_empty(setup_database):
    """Test getting help requests when none exist."""
    response = client.get("/requests")
    assert response.status_code == 200
    assert response.json() == []

def test_get_help_requests_with_data(auth_token):
    """Test getting help requests returns list with data."""
    # Create a help request first
    client.post(
        "/requests",
        json={
            "title": "Need help with Python",
            "description": "I'm struggling with understanding decorators in Python."
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    # Create another help request
    client.post(
        "/requests",
        json={
            "title": "JavaScript async/await",
            "description": "How do I properly handle async operations in JavaScript?"
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    # Get all requests
    response = client.get("/requests")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    
    # Check first request
    assert data[0]["title"] == "Need help with Python"
    assert data[0]["creator"]["username"] == "testuser"
    assert data[0]["creator"]["reputation"] == 0
    
    # Check second request
    assert data[1]["title"] == "JavaScript async/await"
    assert data[1]["creator"]["username"] == "testuser"

def test_get_help_requests_multiple_users(setup_database):
    """Test getting help requests from multiple users."""
    # Create first user and request
    client.post(
        "/register",
        json={
            "username": "user1",
            "email": "user1@example.com",
            "password": "password123"
        }
    )
    
    login1_response = client.post(
        "/login",
        json={"username": "user1", "password": "password123"}
    )
    token1 = login1_response.json()["access_token"]
    
    client.post(
        "/requests",
        json={
            "title": "Help with React",
            "description": "Need help with React hooks"
        },
        headers={"Authorization": f"Bearer {token1}"}
    )
    
    # Create second user and request
    client.post(
        "/register",
        json={
            "username": "user2",
            "email": "user2@example.com",
            "password": "password123"
        }
    )
    
    login2_response = client.post(
        "/login",
        json={"username": "user2", "password": "password123"}
    )
    token2 = login2_response.json()["access_token"]
    
    client.post(
        "/requests",
        json={
            "title": "Help with Django",
            "description": "Need help with Django models"
        },
        headers={"Authorization": f"Bearer {token2}"}
    )
    
    # Get all requests
    response = client.get("/requests")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    
    # Verify different users created the requests
    usernames = [req["creator"]["username"] for req in data]
    assert "user1" in usernames
    assert "user2" in usernames

def test_help_request_validation(auth_token):
    """Test help request validation with missing fields."""
    # Test missing title
    response = client.post(
        "/requests",
        json={"description": "Missing title"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 422  # Validation error

    # Test missing description
    response = client.post(
        "/requests",
        json={"title": "Missing description"},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 422  # Validation error
