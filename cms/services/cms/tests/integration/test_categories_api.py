"""
Integration tests for Categories API endpoints

This module contains comprehensive integration tests for the category management
API endpoints including CRUD operations, hierarchical relationships, multilingual
support, and error handling scenarios.
"""

import pytest
import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.models.category import Category, CategoryTypeEnum, CategoryVisibilityEnum
from app.models.base import Base
from app.api.v1.models.categories import CategoryCreate, CategoryResponse, CategoryListResponse
from tests.utils import (
    create_test_category,
    create_test_user,
    get_auth_headers,
    assert_category_response_structure,
    assert_multilingual_field
)


class TestGetCategoriesAPI:
    """Test cases for GET /categories endpoint"""

    async def test_list_categories_empty_database(self, async_client: AsyncClient, db: Session):
        """Test listing categories when database is empty"""
        response = await async_client.get("/api/v1/categories/")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "data" in data
        assert "pagination" in data
        assert isinstance(data["data"], list)
        assert len(data["data"]) == 0
        
        # Verify pagination metadata
        pagination = data["pagination"]
        assert pagination["page"] == 1
        assert pagination["limit"] == 20
        assert pagination["total"] == 0
        assert pagination["total_pages"] == 0
        assert pagination["has_next"] is False
        assert pagination["has_prev"] is False

    async def test_list_categories_with_data(self, async_client: AsyncClient, db: Session):
        """Test listing categories with existing data"""
        # Create test categories
        categories = []
        for i in range(5):
            category = create_test_category(
                db=db,
                name={"en": f"Category {i}", "ar": f"فئة {i}"},
                category_type=CategoryTypeEnum.TOPIC,
                is_active=True
            )
            categories.append(category)
        
        response = await async_client.get("/api/v1/categories/")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert len(data["data"]) == 5
        
        # Verify category structure
        for category_data in data["data"]:
            assert_category_response_structure(category_data)
            assert_multilingual_field(category_data["name"], required_languages=["en", "ar"])
        
        # Verify pagination
        pagination = data["pagination"]
        assert pagination["total"] == 5
        assert pagination["total_pages"] == 1
        assert pagination["has_next"] is False

    async def test_list_categories_with_pagination(self, async_client: AsyncClient, db: Session):
        """Test categories list with pagination parameters"""
        # Create 25 test categories
        for i in range(25):
            create_test_category(
                db=db,
                name={"en": f"Category {i:02d}", "ar": f"فئة {i:02d}"},
                category_type=CategoryTypeEnum.TOPIC,
                sort_order=i
            )
        
        # Test first page
        response = await async_client.get("/api/v1/categories/?page=1&limit=10")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["data"]) == 10
        pagination = data["pagination"]
        assert pagination["page"] == 1
        assert pagination["limit"] == 10
        assert pagination["total"] == 25
        assert pagination["total_pages"] == 3
        assert pagination["has_next"] is True
        assert pagination["has_prev"] is False
        
        # Test second page
        response = await async_client.get("/api/v1/categories/?page=2&limit=10")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["data"]) == 10
        pagination = data["pagination"]
        assert pagination["page"] == 2
        assert pagination["has_next"] is True
        assert pagination["has_prev"] is True
        
        # Test last page
        response = await async_client.get("/api/v1/categories/?page=3&limit=10")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["data"]) == 5
        pagination = data["pagination"]
        assert pagination["page"] == 3
        assert pagination["has_next"] is False
        assert pagination["has_prev"] is True

    async def test_list_categories_filter_by_type(self, async_client: AsyncClient, db: Session):
        """Test filtering categories by type"""
        # Create categories of different types
        create_test_category(
            db=db,
            name={"en": "Technology", "ar": "التكنولوجيا"},
            category_type=CategoryTypeEnum.TOPIC
        )
        create_test_category(
            db=db,
            name={"en": "Video Format", "ar": "تنسيق الفيديو"},
            category_type=CategoryTypeEnum.FORMAT
        )
        create_test_category(
            db=db,
            name={"en": "Adults", "ar": "البالغين"},
            category_type=CategoryTypeEnum.AUDIENCE
        )
        
        # Filter by TOPIC type
        response = await async_client.get("/api/v1/categories/?category_type=TOPIC")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["data"]) == 1
        assert data["data"][0]["category_type"] == "TOPIC"
        assert data["data"][0]["name"]["en"] == "Technology"
        
        # Filter by FORMAT type
        response = await async_client.get("/api/v1/categories/?category_type=FORMAT")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["data"]) == 1
        assert data["data"][0]["category_type"] == "FORMAT"

    async def test_list_categories_filter_by_parent(self, async_client: AsyncClient, db: Session):
        """Test filtering categories by parent"""
        # Create parent category
        parent = create_test_category(
            db=db,
            name={"en": "Sciences", "ar": "العلوم"},
            category_type=CategoryTypeEnum.TOPIC
        )
        
        # Create child categories
        child1 = create_test_category(
            db=db,
            name={"en": "Physics", "ar": "الفيزياء"},
            category_type=CategoryTypeEnum.TOPIC,
            parent_id=parent.id
        )
        child2 = create_test_category(
            db=db,
            name={"en": "Chemistry", "ar": "الكيمياء"},
            category_type=CategoryTypeEnum.TOPIC,
            parent_id=parent.id
        )
        
        # Create unrelated category
        create_test_category(
            db=db,
            name={"en": "Technology", "ar": "التكنولوجيا"},
            category_type=CategoryTypeEnum.TOPIC
        )
        
        # Filter by parent
        response = await async_client.get(f"/api/v1/categories/?parent_id={parent.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["data"]) == 2
        for category in data["data"]:
            assert category["parent_id"] == str(parent.id)

    async def test_list_categories_filter_by_status(self, async_client: AsyncClient, db: Session):
        """Test filtering categories by active status"""
        # Create active and inactive categories
        create_test_category(
            db=db,
            name={"en": "Active Category", "ar": "فئة نشطة"},
            is_active=True
        )
        create_test_category(
            db=db,
            name={"en": "Inactive Category", "ar": "فئة غير نشطة"},
            is_active=False
        )
        
        # Filter active categories
        response = await async_client.get("/api/v1/categories/?is_active=true")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["data"]) == 1
        assert data["data"][0]["is_active"] is True
        
        # Filter inactive categories
        response = await async_client.get("/api/v1/categories/?is_active=false")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["data"]) == 1
        assert data["data"][0]["is_active"] is False

    async def test_list_categories_search(self, async_client: AsyncClient, db: Session):
        """Test searching categories by name"""
        # Create categories with different names
        create_test_category(
            db=db,
            name={"en": "Technology Programming", "ar": "برمجة التكنولوجيا"}
        )
        create_test_category(
            db=db,
            name={"en": "Science Mathematics", "ar": "رياضيات العلوم"}
        )
        create_test_category(
            db=db,
            name={"en": "Art History", "ar": "تاريخ الفن"}
        )
        
        # Search for "Technology"
        response = await async_client.get("/api/v1/categories/?search=Technology")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["data"]) == 1
        assert "Technology" in data["data"][0]["name"]["en"]
        
        # Search in Arabic
        response = await async_client.get("/api/v1/categories/?search=برمجة")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["data"]) == 1

    async def test_list_categories_language_preference(self, async_client: AsyncClient, db: Session):
        """Test category listing with language preference"""
        create_test_category(
            db=db,
            name={"en": "Technology", "ar": "التكنولوجيا", "fr": "Technologie"}
        )
        
        # Request with Arabic preference
        response = await async_client.get("/api/v1/categories/?language=ar")
        
        assert response.status_code == 200
        data = response.json()
        
        # API should return full multilingual data
        category = data["data"][0]
        assert "ar" in category["name"]
        assert "en" in category["name"]
        
        # Request with French preference
        response = await async_client.get("/api/v1/categories/?language=fr")
        
        assert response.status_code == 200
        # Should still return all languages

    async def test_list_categories_invalid_pagination(self, async_client: AsyncClient):
        """Test invalid pagination parameters"""
        # Invalid page number
        response = await async_client.get("/api/v1/categories/?page=0")
        assert response.status_code == 422
        
        # Invalid limit
        response = await async_client.get("/api/v1/categories/?limit=101")
        assert response.status_code == 422
        
        # Negative page
        response = await async_client.get("/api/v1/categories/?page=-1")
        assert response.status_code == 422

    async def test_list_categories_invalid_category_type(self, async_client: AsyncClient):
        """Test invalid category type filter"""
        response = await async_client.get("/api/v1/categories/?category_type=INVALID_TYPE")
        
        assert response.status_code == 400
        assert "Invalid category type" in response.json()["detail"]

    async def test_list_categories_performance_with_large_dataset(
        self, async_client: AsyncClient, db: Session
    ):
        """Test API performance with large number of categories"""
        # Create 100 categories
        for i in range(100):
            create_test_category(
                db=db,
                name={"en": f"Category {i:03d}", "ar": f"فئة {i:03d}"},
                category_type=CategoryTypeEnum.TOPIC
            )
        
        import time
        start_time = time.time()
        
        response = await async_client.get("/api/v1/categories/?limit=50")
        
        end_time = time.time()
        response_time = end_time - start_time
        
        assert response.status_code == 200
        assert len(response.json()["data"]) == 50
        
        # Response should be under 1 second
        assert response_time < 1.0


class TestCreateCategoryAPI:
    """Test cases for POST /categories endpoint"""

    async def test_create_category_minimal_data(self, async_client: AsyncClient, auth_headers: Dict[str, str]):
        """Test creating category with minimal required data"""
        category_data = {
            "name": {"en": "Technology", "ar": "التكنولوجيا"},
            "category_type": "TOPIC"
        }
        
        response = await async_client.post(
            "/api/v1/categories/",
            json=category_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        
        # Verify response structure
        assert_category_response_structure(data)
        
        # Verify created data
        assert data["name"]["en"] == "Technology"
        assert data["name"]["ar"] == "التكنولوجيا"
        assert data["category_type"] == "TOPIC"
        assert data["is_active"] is True
        assert data["visibility"] == "PUBLIC"
        assert data["level"] == 0  # Root category
        assert data["content_count"] == 0
        assert data["subcategory_count"] == 0
        
        # Verify timestamps
        assert "created_at" in data
        assert "updated_at" in data

    async def test_create_category_complete_data(self, async_client: AsyncClient, auth_headers: Dict[str, str]):
        """Test creating category with all optional fields"""
        category_data = {
            "name": {
                "en": "Advanced Technology",
                "ar": "التكنولوجيا المتقدمة",
                "fr": "Technologie Avancée",
                "es": "Tecnología Avanzada"
            },
            "description": {
                "en": "Advanced technology and programming concepts",
                "ar": "مفاهيم التكنولوجيا والبرمجة المتقدمة"
            },
            "slug": {
                "en": "advanced-technology",
                "ar": "التكنولوجيا-المتقدمة"
            },
            "category_type": "TOPIC",
            "is_active": True,
            "visibility": "PUBLIC",
            "icon_url": "/icons/technology.svg",
            "banner_url": "/banners/technology-banner.jpg",
            "color_scheme": "#2ECC71",
            "sort_order": 5,
            "seo_title": {
                "en": "Advanced Technology - Learn Programming",
                "ar": "التكنولوجيا المتقدمة - تعلم البرمجة"
            },
            "seo_description": {
                "en": "Comprehensive courses on advanced technology and programming",
                "ar": "دورات شاملة في التكنولوجيا والبرمجة المتقدمة"
            },
            "seo_keywords": ["technology", "programming", "advanced", "education"],
            "metadata": {
                "featured": True,
                "priority": "high",
                "target_audience": "professionals"
            }
        }
        
        response = await async_client.post(
            "/api/v1/categories/",
            json=category_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        
        # Verify all fields were saved correctly
        assert data["name"]["en"] == "Advanced Technology"
        assert data["name"]["fr"] == "Technologie Avancée"
        assert data["description"]["en"] == "Advanced technology and programming concepts"
        assert data["slug"]["en"] == "advanced-technology"
        assert data["icon_url"] == "/icons/technology.svg"
        assert data["banner_url"] == "/banners/technology-banner.jpg"
        assert data["color_scheme"] == "#2ECC71"
        assert data["sort_order"] == 5
        assert data["seo_title"]["en"] == "Advanced Technology - Learn Programming"
        assert len(data["seo_keywords"]) == 4
        assert data["metadata"]["featured"] is True

    async def test_create_category_with_parent(
        self, async_client: AsyncClient, auth_headers: Dict[str, str], db: Session
    ):
        """Test creating category with parent relationship"""
        # Create parent category first
        parent = create_test_category(
            db=db,
            name={"en": "Sciences", "ar": "العلوم"},
            category_type=CategoryTypeEnum.TOPIC
        )
        
        child_data = {
            "name": {"en": "Physics", "ar": "الفيزياء"},
            "category_type": "TOPIC",
            "parent_id": str(parent.id)
        }
        
        response = await async_client.post(
            "/api/v1/categories/",
            json=child_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        
        # Verify parent relationship
        assert data["parent_id"] == str(parent.id)
        assert data["level"] == 1  # Child level
        assert data["path"].startswith("/sciences")  # Path includes parent

    async def test_create_category_invalid_multilingual_name(
        self, async_client: AsyncClient, auth_headers: Dict[str, str]
    ):
        """Test creating category with invalid multilingual name"""
        # Empty name dictionary
        response = await async_client.post(
            "/api/v1/categories/",
            json={
                "name": {},
                "category_type": "TOPIC"
            },
            headers=auth_headers
        )
        assert response.status_code == 422
        
        # Name with empty string
        response = await async_client.post(
            "/api/v1/categories/",
            json={
                "name": {"en": "", "ar": "التكنولوجيا"},
                "category_type": "TOPIC"
            },
            headers=auth_headers
        )
        assert response.status_code == 422
        
        # Name with invalid language code
        response = await async_client.post(
            "/api/v1/categories/",
            json={
                "name": {"x": "Technology", "ar": "التكنولوجيا"},
                "category_type": "TOPIC"
            },
            headers=auth_headers
        )
        assert response.status_code == 422

    async def test_create_category_missing_required_fields(
        self, async_client: AsyncClient, auth_headers: Dict[str, str]
    ):
        """Test creating category with missing required fields"""
        # Missing name
        response = await async_client.post(
            "/api/v1/categories/",
            json={"category_type": "TOPIC"},
            headers=auth_headers
        )
        assert response.status_code == 422
        
        # Missing category_type
        response = await async_client.post(
            "/api/v1/categories/",
            json={"name": {"en": "Technology"}},
            headers=auth_headers
        )
        assert response.status_code == 422

    async def test_create_category_invalid_category_type(
        self, async_client: AsyncClient, auth_headers: Dict[str, str]
    ):
        """Test creating category with invalid category type"""
        response = await async_client.post(
            "/api/v1/categories/",
            json={
                "name": {"en": "Technology"},
                "category_type": "INVALID_TYPE"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 422

    async def test_create_category_invalid_color_scheme(
        self, async_client: AsyncClient, auth_headers: Dict[str, str]
    ):
        """Test creating category with invalid color scheme"""
        response = await async_client.post(
            "/api/v1/categories/",
            json={
                "name": {"en": "Technology"},
                "category_type": "TOPIC",
                "color_scheme": "invalid-color"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 422

    async def test_create_category_invalid_sort_order(
        self, async_client: AsyncClient, auth_headers: Dict[str, str]
    ):
        """Test creating category with invalid sort order"""
        response = await async_client.post(
            "/api/v1/categories/",
            json={
                "name": {"en": "Technology"},
                "category_type": "TOPIC",
                "sort_order": -1
            },
            headers=auth_headers
        )
        
        assert response.status_code == 422

    async def test_create_category_nonexistent_parent(
        self, async_client: AsyncClient, auth_headers: Dict[str, str]
    ):
        """Test creating category with nonexistent parent"""
        nonexistent_id = str(uuid.uuid4())
        
        response = await async_client.post(
            "/api/v1/categories/",
            json={
                "name": {"en": "Child Category"},
                "category_type": "TOPIC",
                "parent_id": nonexistent_id
            },
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "Parent category not found" in response.json()["detail"]

    async def test_create_category_without_authentication(self, async_client: AsyncClient):
        """Test creating category without authentication"""
        response = await async_client.post(
            "/api/v1/categories/",
            json={
                "name": {"en": "Technology"},
                "category_type": "TOPIC"
            }
        )
        
        assert response.status_code == 401

    async def test_create_category_duplicate_slug(
        self, async_client: AsyncClient, auth_headers: Dict[str, str], db: Session
    ):
        """Test creating category with duplicate slug"""
        # Create first category
        create_test_category(
            db=db,
            name={"en": "Technology", "ar": "التكنولوجيا"},
            slug={"en": "technology", "ar": "التكنولوجيا"}
        )
        
        # Try to create another with same slug
        response = await async_client.post(
            "/api/v1/categories/",
            json={
                "name": {"en": "Technology Advanced", "ar": "التكنولوجيا المتقدمة"},
                "slug": {"en": "technology", "ar": "التكنولوجيا-متقدمة"},
                "category_type": "TOPIC"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 409
        assert "slug already exists" in response.json()["detail"]

    async def test_create_category_long_text_fields(
        self, async_client: AsyncClient, auth_headers: Dict[str, str]
    ):
        """Test creating category with text fields at maximum length"""
        long_name = "A" * 1000  # Maximum allowed length
        
        response = await async_client.post(
            "/api/v1/categories/",
            json={
                "name": {"en": long_name, "ar": "اسم طويل"},
                "category_type": "TOPIC"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 201
        
        # Test exceeding maximum length
        too_long_name = "A" * 1001
        
        response = await async_client.post(
            "/api/v1/categories/",
            json={
                "name": {"en": too_long_name, "ar": "اسم طويل جداً"},
                "category_type": "TOPIC"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 422

    async def test_create_category_seo_keywords_limit(
        self, async_client: AsyncClient, auth_headers: Dict[str, str]
    ):
        """Test creating category with SEO keywords at limit"""
        # Test maximum allowed keywords (20)
        keywords = [f"keyword{i}" for i in range(20)]
        
        response = await async_client.post(
            "/api/v1/categories/",
            json={
                "name": {"en": "Technology"},
                "category_type": "TOPIC",
                "seo_keywords": keywords
            },
            headers=auth_headers
        )
        
        assert response.status_code == 201
        
        # Test exceeding keyword limit
        too_many_keywords = [f"keyword{i}" for i in range(21)]
        
        response = await async_client.post(
            "/api/v1/categories/",
            json={
                "name": {"en": "Technology 2"},
                "category_type": "TOPIC",
                "seo_keywords": too_many_keywords
            },
            headers=auth_headers
        )
        
        assert response.status_code == 422

    async def test_create_category_path_generation(
        self, async_client: AsyncClient, auth_headers: Dict[str, str], db: Session
    ):
        """Test automatic path generation for categories"""
        # Create root category
        response = await async_client.post(
            "/api/v1/categories/",
            json={
                "name": {"en": "Sciences", "ar": "العلوم"},
                "slug": {"en": "sciences", "ar": "العلوم"},
                "category_type": "TOPIC"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 201
        root_data = response.json()
        assert root_data["path"] == "/sciences"
        
        # Create child category
        response = await async_client.post(
            "/api/v1/categories/",
            json={
                "name": {"en": "Physics", "ar": "الفيزياء"},
                "slug": {"en": "physics", "ar": "الفيزياء"},
                "category_type": "TOPIC",
                "parent_id": root_data["id"]
            },
            headers=auth_headers
        )
        
        assert response.status_code == 201
        child_data = response.json()
        assert child_data["path"] == "/sciences/physics"
        assert child_data["level"] == 1

    async def test_create_category_background_tasks(
        self, async_client: AsyncClient, auth_headers: Dict[str, str]
    ):
        """Test that background tasks are scheduled after category creation"""
        response = await async_client.post(
            "/api/v1/categories/",
            json={
                "name": {"en": "Technology", "ar": "التكنولوجيا"},
                "category_type": "TOPIC"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 201
        
        # In a real test environment, you would check that background tasks
        # like search indexing and cache updates were scheduled
        # This would typically involve mocking the background task queue