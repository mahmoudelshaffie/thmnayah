"""
Test configuration and fixtures

This module provides pytest fixtures and configuration for running
integration tests for the CMS category management system.
"""

import pytest
import asyncio
import uuid
from typing import AsyncGenerator, Generator, Dict, Any
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.models.category import Category
from tests.utils import get_auth_headers, cleanup_test_categories


# Test database setup
TEST_DATABASE_URL = "sqlite:///./test.db"

# Create test engine with in-memory SQLite
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={
        "check_same_thread": False,
        "isolation_level": None  # For better async support
    },
    poolclass=StaticPool,
    echo=False  # Set to True for SQL debugging
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """
    Create a test database session.
    
    Creates all tables before each test and drops them after.
    This ensures a clean state for each test.
    """
    # Create all tables
    Base.metadata.create_all(bind=test_engine)
    
    # Create test session
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
async def async_client(db: Session) -> AsyncGenerator[AsyncClient, None]:
    """
    Create an async test client with database dependency override.
    
    Args:
        db: Test database session
        
    Yields:
        AsyncClient configured for testing
    """
    
    def override_get_db():
        """Override the database dependency to use test database."""
        try:
            yield db
        finally:
            pass  # Session cleanup handled by db fixture
    
    # Override dependency
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client
    
    # Clean up dependency override
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def auth_headers() -> Dict[str, str]:
    """
    Generate authentication headers for testing.
    
    Returns:
        Dictionary with mock authentication headers
    """
    return get_auth_headers()


@pytest.fixture(scope="function")
def test_user_id() -> uuid.UUID:
    """
    Generate a test user ID for consistent testing.
    
    Returns:
        UUID for test user
    """
    return uuid.uuid4()


@pytest.fixture(scope="function")
def mock_user_data(test_user_id: uuid.UUID) -> Dict[str, Any]:
    """
    Create mock user data for testing.
    
    Args:
        test_user_id: Test user ID
        
    Returns:
        Mock user data dictionary
    """
    return {
        "id": test_user_id,
        "email": "test@example.com",
        "name": "Test User",
        "is_active": True,
        "roles": ["user"]
    }


@pytest.fixture(scope="function", autouse=True)
def clean_database(db: Session):
    """
    Automatically clean the database before each test.
    
    Args:
        db: Test database session
    """
    cleanup_test_categories(db)
    yield
    cleanup_test_categories(db)


class DatabaseTestCase:
    """
    Base test case class for database tests.
    
    Provides common setup and utilities for database-related tests.
    """
    
    @pytest.fixture(autouse=True)
    def setup_method(self, db: Session):
        """Set up test method with database session."""
        self.db = db


class APITestCase:
    """
    Base test case class for API tests.
    
    Provides common setup and utilities for API integration tests.
    """
    
    @pytest.fixture(autouse=True)
    def setup_method(self, async_client: AsyncClient, auth_headers: Dict[str, str]):
        """Set up test method with API client and auth headers."""
        self.client = async_client
        self.auth_headers = auth_headers


# Test data fixtures
@pytest.fixture
def sample_category_data() -> Dict[str, Any]:
    """
    Sample category data for testing.
    
    Returns:
        Dictionary with sample category fields
    """
    return {
        "name": {
            "en": "Technology",
            "ar": "'D*CFHDH,J'",
            "fr": "Technologie",
            "es": "Tecnología"
        },
        "description": {
            "en": "Technology and programming category",
            "ar": "A&) 'D*CFHDH,J' H'D(1E,)",
            "fr": "Catégorie technologie et programmation"
        },
        "category_type": "TOPIC",
        "is_active": True,
        "visibility": "PUBLIC",
        "icon_url": "/icons/technology.svg",
        "banner_url": "/banners/technology-banner.jpg",
        "color_scheme": "#2ECC71",
        "sort_order": 1,
        "seo_title": {
            "en": "Technology - Learn Programming and More",
            "ar": "'D*CFHDH,J' - *9DE 'D(1E,) H#C+1"
        },
        "seo_description": {
            "en": "Explore technology courses, programming tutorials, and digital innovation content",
            "ar": "'3*C4A /H1'* 'D*CFHDH,J' H41H-'* 'D(1E,) HE-*HI 'D'(*C'1 'D1BEJ"
        },
        "seo_keywords": ["technology", "programming", "innovation", "digital", "coding"],
        "metadata": {
            "featured": True,
            "priority": "high",
            "target_audience": ["students", "professionals"]
        }
    }


@pytest.fixture
def minimal_category_data() -> Dict[str, Any]:
    """
    Minimal category data for testing required fields only.
    
    Returns:
        Dictionary with minimal required category fields
    """
    return {
        "name": {"en": "Simple Category", "ar": "A&) (3J7)"},
        "category_type": "TOPIC"
    }


@pytest.fixture
def multilingual_test_data() -> Dict[str, Dict[str, str]]:
    """
    Multilingual test data in various languages.
    
    Returns:
        Dictionary with multilingual content for different use cases
    """
    return {
        "technology": {
            "en": "Technology",
            "ar": "'D*CFHDH,J'",
            "fr": "Technologie",
            "es": "Tecnología",
            "de": "Technologie",
            "zh": "€/",
            "ja": "€S",
            "ru": ""5E=>;>388"
        },
        "science": {
            "en": "Science",
            "ar": "'D9DHE",
            "fr": "Science",
            "es": "Ciencia",
            "de": "Wissenschaft",
            "zh": "Ñf",
            "ja": "Ñf",
            "ru": "0C:0"
        },
        "education": {
            "en": "Education",
            "ar": "'D*9DJE",
            "fr": "Éducation",
            "es": "Educación",
            "de": "Bildung",
            "zh": "Y²",
            "ja": "Y²",
            "ru": "1@07>20=85"
        }
    }


@pytest.fixture
def invalid_test_data() -> Dict[str, Any]:
    """
    Invalid test data for negative testing scenarios.
    
    Returns:
        Dictionary with various invalid data scenarios
    """
    return {
        "empty_name": {
            "name": {},
            "category_type": "TOPIC"
        },
        "invalid_language_code": {
            "name": {"x": "Invalid", "ar": ":J1 5'D-"},
            "category_type": "TOPIC"
        },
        "empty_text": {
            "name": {"en": "", "ar": "A&)"},
            "category_type": "TOPIC"
        },
        "invalid_category_type": {
            "name": {"en": "Test"},
            "category_type": "INVALID_TYPE"
        },
        "invalid_color_scheme": {
            "name": {"en": "Test"},
            "category_type": "TOPIC",
            "color_scheme": "invalid-color"
        },
        "negative_sort_order": {
            "name": {"en": "Test"},
            "category_type": "TOPIC",
            "sort_order": -1
        },
        "too_many_keywords": {
            "name": {"en": "Test"},
            "category_type": "TOPIC",
            "seo_keywords": [f"keyword{i}" for i in range(25)]  # Exceeds 20 limit
        },
        "text_too_long": {
            "name": {"en": "A" * 1001, "ar": "F5 7HJD"},  # Exceeds 1000 limit
            "category_type": "TOPIC"
        }
    }


# Performance testing fixtures
@pytest.fixture
def performance_test_config() -> Dict[str, Any]:
    """
    Configuration for performance testing.
    
    Returns:
        Dictionary with performance test parameters
    """
    return {
        "max_response_time": 1.0,  # seconds
        "bulk_operation_limit": 50,
        "large_dataset_size": 100,
        "concurrent_requests": 10
    }


# Mock fixtures for external dependencies
@pytest.fixture
def mock_background_tasks():
    """Mock background tasks for testing task scheduling."""
    return []


@pytest.fixture
def mock_search_index():
    """Mock search indexing service for testing."""
    return {
        "index": lambda category_id: f"Indexed category {category_id}",
        "update": lambda category_id: f"Updated index for category {category_id}",
        "delete": lambda category_id: f"Deleted index for category {category_id}"
    }


@pytest.fixture
def mock_cache_service():
    """Mock cache service for testing."""
    return {
        "get": lambda key: None,
        "set": lambda key, value: f"Cached {key}",
        "delete": lambda key: f"Deleted cache key {key}",
        "clear": lambda pattern: f"Cleared cache pattern {pattern}"
    }


# Test environment configuration
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment configuration."""
    import os
    
    # Set test environment variables
    os.environ["ENVIRONMENT"] = "test"
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    os.environ["SECRET_KEY"] = "test-secret-key"
    os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
    
    yield
    
    # Clean up after all tests
    try:
        import os
        if os.path.exists("./test.db"):
            os.remove("./test.db")
    except Exception:
        pass


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Add integration marker to all tests in integration directory
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        
        # Add slow marker to performance tests
        if "performance" in item.name.lower():
            item.add_marker(pytest.mark.slow)
            item.add_marker(pytest.mark.performance)


# Skip markers for CI/local development
def pytest_runtest_setup(item):
    """Set up individual test runs with environment-specific skips."""
    import os
    
    # Skip slow tests in CI unless explicitly requested
    if "CI" in os.environ and item.get_closest_marker("slow"):
        if not os.environ.get("RUN_SLOW_TESTS"):
            pytest.skip("Slow tests skipped in CI environment")
    
    # Skip performance tests unless explicitly requested
    if item.get_closest_marker("performance"):
        if not os.environ.get("RUN_PERFORMANCE_TESTS"):
            pytest.skip("Performance tests skipped (set RUN_PERFORMANCE_TESTS=1 to run)")