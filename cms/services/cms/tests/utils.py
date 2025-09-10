"""
Test utilities and helper functions

This module provides common utilities, fixtures, and helper functions
used across different test modules for category management testing.
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from sqlalchemy.orm import Session

from app.models.category import Category, CategoryTypeEnum, CategoryVisibilityEnum
from app.models.base import Base


def create_test_category(
    db: Session,
    name: Dict[str, str],
    category_type: CategoryTypeEnum = CategoryTypeEnum.TOPIC,
    description: Optional[Dict[str, str]] = None,
    slug: Optional[Dict[str, str]] = None,
    parent_id: Optional[uuid.UUID] = None,
    is_active: bool = True,
    visibility: CategoryVisibilityEnum = CategoryVisibilityEnum.PUBLIC,
    icon_url: Optional[str] = None,
    banner_url: Optional[str] = None,
    color_scheme: Optional[str] = None,
    sort_order: int = 0,
    level: int = 0,
    path: Optional[str] = None,
    content_count: int = 0,
    subcategory_count: int = 0,
    total_content_count: int = 0,
    seo_title: Optional[Dict[str, str]] = None,
    seo_description: Optional[Dict[str, str]] = None,
    seo_keywords: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Category:
    """
    Create a test category with default or specified values.
    
    Args:
        db: Database session
        name: Multilingual name dictionary
        category_type: Type of category
        description: Optional multilingual description
        slug: Optional multilingual slug
        parent_id: Optional parent category ID
        is_active: Whether category is active
        visibility: Category visibility level
        icon_url: Optional icon URL
        banner_url: Optional banner URL
        color_scheme: Optional hex color scheme
        sort_order: Sort order within parent
        level: Hierarchy level
        path: Category path (auto-generated if not provided)
        content_count: Number of direct content items
        subcategory_count: Number of direct subcategories
        total_content_count: Total content including subcategories
        seo_title: Optional SEO title
        seo_description: Optional SEO description
        seo_keywords: Optional SEO keywords list
        metadata: Optional metadata dictionary
        **kwargs: Additional fields
    
    Returns:
        Created Category instance
    """
    # Generate path if not provided
    if not path:
        if parent_id:
            parent = db.query(Category).filter(Category.id == parent_id).first()
            if parent:
                slug_key = next(iter(slug.keys())) if slug else next(iter(name.keys()))
                category_slug = slug[slug_key] if slug and slug_key in slug else name[slug_key].lower().replace(' ', '-')
                path = f"{parent.path}/{category_slug}"
            else:
                slug_key = next(iter(name.keys()))
                category_slug = slug[slug_key] if slug and slug_key in slug else name[slug_key].lower().replace(' ', '-')
                path = f"/{category_slug}"
        else:
            slug_key = next(iter(name.keys()))
            category_slug = slug[slug_key] if slug and slug_key in slug else name[slug_key].lower().replace(' ', '-')
            path = f"/{category_slug}"
    
    # Create category instance
    category = Category(
        id=uuid.uuid4(),
        name=name,
        description=description,
        slug=slug,
        category_type=category_type,
        parent_id=parent_id,
        level=level,
        path=path,
        is_active=is_active,
        visibility=visibility,
        icon_url=icon_url,
        banner_url=banner_url,
        color_scheme=color_scheme,
        sort_order=sort_order,
        content_count=content_count,
        subcategory_count=subcategory_count,
        total_content_count=total_content_count,
        seo_title=seo_title,
        seo_description=seo_description,
        seo_keywords=seo_keywords,
        _metadata=metadata,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        **kwargs
    )
    
    # Add to database
    db.add(category)
    db.commit()
    db.refresh(category)
    
    return category


def create_test_user(
    db: Session,
    email: str = "test@example.com",
    name: str = "Test User",
    is_active: bool = True,
    **kwargs
) -> Dict[str, Any]:
    """
    Create a test user for authentication purposes.
    
    Args:
        db: Database session
        email: User email
        name: User name
        is_active: Whether user is active
        **kwargs: Additional user fields
    
    Returns:
        User data dictionary
    """
    # This is a mock implementation since User model is not fully implemented
    user_data = {
        "id": uuid.uuid4(),
        "email": email,
        "name": name,
        "is_active": is_active,
        "created_at": datetime.utcnow(),
        **kwargs
    }
    
    return user_data


def get_auth_headers(user_id: Optional[uuid.UUID] = None) -> Dict[str, str]:
    """
    Generate authentication headers for testing.
    
    Args:
        user_id: Optional specific user ID to use
    
    Returns:
        Dictionary with authentication headers
    """
    if not user_id:
        user_id = uuid.uuid4()
    
    # Mock JWT token for testing
    mock_token = f"Bearer mock_jwt_token_for_{user_id}"
    
    return {
        "Authorization": mock_token,
        "Content-Type": "application/json"
    }


def assert_category_response_structure(category_data: Dict[str, Any]) -> None:
    """
    Assert that category response has the correct structure.
    
    Args:
        category_data: Category response data to validate
    
    Raises:
        AssertionError: If structure is invalid
    """
    # Required fields
    required_fields = [
        "id", "name", "category_type", "level", "path", "is_active", 
        "visibility", "content_count", "subcategory_count", 
        "total_content_count", "sort_order", "created_at", "updated_at"
    ]
    
    for field in required_fields:
        assert field in category_data, f"Missing required field: {field}"
    
    # Verify field types
    assert isinstance(category_data["id"], str)
    assert isinstance(category_data["name"], dict)
    assert isinstance(category_data["category_type"], str)
    assert isinstance(category_data["level"], int)
    assert isinstance(category_data["path"], str)
    assert isinstance(category_data["is_active"], bool)
    assert isinstance(category_data["visibility"], str)
    assert isinstance(category_data["content_count"], int)
    assert isinstance(category_data["subcategory_count"], int)
    assert isinstance(category_data["total_content_count"], int)
    assert isinstance(category_data["sort_order"], int)
    assert isinstance(category_data["created_at"], str)
    assert isinstance(category_data["updated_at"], str)
    
    # Verify ID format
    assert uuid.UUID(category_data["id"])
    
    # Verify non-negative counts
    assert category_data["content_count"] >= 0
    assert category_data["subcategory_count"] >= 0
    assert category_data["total_content_count"] >= 0
    assert category_data["sort_order"] >= 0
    assert category_data["level"] >= 0


def assert_multilingual_field(
    field_data: Dict[str, str], 
    required_languages: Optional[List[str]] = None,
    min_languages: int = 1
) -> None:
    """
    Assert that multilingual field has correct structure and content.
    
    Args:
        field_data: Multilingual field data
        required_languages: List of languages that must be present
        min_languages: Minimum number of languages required
    
    Raises:
        AssertionError: If field structure is invalid
    """
    assert isinstance(field_data, dict), "Multilingual field must be a dictionary"
    assert len(field_data) >= min_languages, f"Must have at least {min_languages} language(s)"
    
    # Check required languages if specified
    if required_languages:
        for lang in required_languages:
            assert lang in field_data, f"Missing required language: {lang}"
    
    # Verify language codes and content
    for lang_code, text in field_data.items():
        assert isinstance(lang_code, str), "Language code must be string"
        assert len(lang_code) >= 2, "Language code must be at least 2 characters"
        assert isinstance(text, str), "Language text must be string"
        assert len(text.strip()) > 0, "Language text cannot be empty"
        assert len(text) <= 1000, "Language text too long"


def assert_pagination_structure(pagination_data: Dict[str, Any]) -> None:
    """
    Assert that pagination metadata has correct structure.
    
    Args:
        pagination_data: Pagination metadata to validate
    
    Raises:
        AssertionError: If pagination structure is invalid
    """
    required_fields = ["page", "limit", "total", "total_pages", "has_next", "has_prev"]
    
    for field in required_fields:
        assert field in pagination_data, f"Missing pagination field: {field}"
    
    # Verify field types and values
    assert isinstance(pagination_data["page"], int)
    assert isinstance(pagination_data["limit"], int)
    assert isinstance(pagination_data["total"], int)
    assert isinstance(pagination_data["total_pages"], int)
    assert isinstance(pagination_data["has_next"], bool)
    assert isinstance(pagination_data["has_prev"], bool)
    
    # Verify logical consistency
    assert pagination_data["page"] >= 1
    assert pagination_data["limit"] >= 1
    assert pagination_data["total"] >= 0
    assert pagination_data["total_pages"] >= 0
    
    # Verify page consistency
    if pagination_data["total"] == 0:
        assert pagination_data["total_pages"] == 0
    else:
        expected_pages = (pagination_data["total"] + pagination_data["limit"] - 1) // pagination_data["limit"]
        assert pagination_data["total_pages"] == expected_pages
    
    # Verify navigation flags
    if pagination_data["page"] == 1:
        assert pagination_data["has_prev"] is False
    if pagination_data["page"] >= pagination_data["total_pages"]:
        assert pagination_data["has_next"] is False


def create_category_hierarchy(
    db: Session,
    levels: List[Dict[str, Any]]
) -> List[Category]:
    """
    Create a hierarchical structure of categories.
    
    Args:
        db: Database session
        levels: List of dictionaries defining each level of the hierarchy
    
    Returns:
        List of created categories in hierarchy order
    
    Example:
        levels = [
            {
                "name": {"en": "Sciences", "ar": "'D9DHE"},
                "category_type": CategoryTypeEnum.TOPIC
            },
            {
                "name": {"en": "Physics", "ar": "'DAJ2J'!"},
                "category_type": CategoryTypeEnum.TOPIC
            },
            {
                "name": {"en": "Quantum Physics", "ar": "AJ2J'! 'DCE"},
                "category_type": CategoryTypeEnum.TOPIC
            }
        ]
    """
    categories = []
    parent_id = None
    
    for level, level_data in enumerate(levels):
        category = create_test_category(
            db=db,
            parent_id=parent_id,
            level=level,
            **level_data
        )
        categories.append(category)
        parent_id = category.id
    
    return categories


def assert_category_hierarchy(categories: List[Dict[str, Any]]) -> None:
    """
    Assert that a list of categories maintains proper hierarchical structure.
    
    Args:
        categories: List of category response data
    
    Raises:
        AssertionError: If hierarchy is invalid
    """
    for i, category in enumerate(categories):
        if i == 0:
            # Root category
            assert category["parent_id"] is None
            assert category["level"] == 0
        else:
            # Child category
            parent = categories[i - 1]
            assert category["parent_id"] == parent["id"]
            assert category["level"] == parent["level"] + 1
            assert category["path"].startswith(parent["path"])


def generate_multilingual_content(
    base_text: str,
    languages: List[str] = None,
    variations: Dict[str, str] = None
) -> Dict[str, str]:
    """
    Generate multilingual content for testing.
    
    Args:
        base_text: Base text to generate variations from
        languages: List of language codes
        variations: Custom variations for specific languages
    
    Returns:
        Dictionary with language codes as keys and text as values
    """
    if languages is None:
        languages = ["en", "ar", "fr", "es"]
    
    if variations is None:
        variations = {}
    
    # Default translations (mock)
    default_translations = {
        "en": base_text,
        "ar": f"'DF5 'D91(J: {base_text}",
        "fr": f"Texte français: {base_text}",
        "es": f"Texto español: {base_text}",
        "de": f"Deutscher Text: {base_text}",
        "zh": f"-‡‡,: {base_text}",
        "ja": f"å,žÆ­¹È: {base_text}",
        "ru": f" CAA:89 B5:AB: {base_text}"
    }
    
    result = {}
    for lang in languages:
        if lang in variations:
            result[lang] = variations[lang]
        elif lang in default_translations:
            result[lang] = default_translations[lang]
        else:
            result[lang] = f"{lang.upper()}: {base_text}"
    
    return result


def cleanup_test_categories(db: Session) -> None:
    """
    Clean up all test categories from database.
    
    Args:
        db: Database session
    """
    try:
        db.query(Category).delete()
        db.commit()
    except Exception:
        db.rollback()
        raise


def create_test_content_item(
    db: Session,
    title: Dict[str, str],
    category_id: Optional[uuid.UUID] = None,
    content_type: str = "ARTICLE",
    status: str = "PUBLISHED",
    **kwargs
) -> Dict[str, Any]:
    """
    Create a test content item (mock since Content model might not be fully available).
    
    Args:
        db: Database session
        title: Multilingual title
        category_id: Optional category ID to assign to
        content_type: Type of content
        status: Content status
        **kwargs: Additional content fields
    
    Returns:
        Mock content item dictionary
    """
    content_data = {
        "id": uuid.uuid4(),
        "title": title,
        "content_type": content_type,
        "status": status,
        "primary_category_id": category_id,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        **kwargs
    }
    
    return content_data


def assert_response_time(response_time: float, max_time: float = 1.0) -> None:
    """
    Assert that response time is within acceptable limits.
    
    Args:
        response_time: Actual response time in seconds
        max_time: Maximum acceptable response time in seconds
    
    Raises:
        AssertionError: If response time exceeds limit
    """
    assert response_time <= max_time, f"Response time {response_time:.3f}s exceeds limit {max_time:.3f}s"


def mock_background_tasks() -> List[Dict[str, Any]]:
    """
    Mock background tasks queue for testing task scheduling.
    
    Returns:
        List of scheduled background tasks
    """
    return []


class CategoryTestDataBuilder:
    """
    Builder class for creating test category data with fluent interface.
    """
    
    def __init__(self):
        self.data = {
            "name": {"en": "Test Category", "ar": "A&) *,1J(J)"},
            "category_type": "TOPIC"
        }
    
    def with_name(self, name: Dict[str, str]) -> 'CategoryTestDataBuilder':
        """Set category name."""
        self.data["name"] = name
        return self
    
    def with_type(self, category_type: str) -> 'CategoryTestDataBuilder':
        """Set category type."""
        self.data["category_type"] = category_type
        return self
    
    def with_description(self, description: Dict[str, str]) -> 'CategoryTestDataBuilder':
        """Set category description."""
        self.data["description"] = description
        return self
    
    def with_parent(self, parent_id: uuid.UUID) -> 'CategoryTestDataBuilder':
        """Set parent category."""
        self.data["parent_id"] = str(parent_id)
        return self
    
    def with_visibility(self, visibility: str) -> 'CategoryTestDataBuilder':
        """Set category visibility."""
        self.data["visibility"] = visibility
        return self
    
    def with_seo(self, title: Dict[str, str], description: Dict[str, str], keywords: List[str]) -> 'CategoryTestDataBuilder':
        """Set SEO fields."""
        self.data["seo_title"] = title
        self.data["seo_description"] = description
        self.data["seo_keywords"] = keywords
        return self
    
    def with_styling(self, icon_url: str, banner_url: str, color_scheme: str) -> 'CategoryTestDataBuilder':
        """Set styling fields."""
        self.data["icon_url"] = icon_url
        self.data["banner_url"] = banner_url
        self.data["color_scheme"] = color_scheme
        return self
    
    def inactive(self) -> 'CategoryTestDataBuilder':
        """Set category as inactive."""
        self.data["is_active"] = False
        return self
    
    def private(self) -> 'CategoryTestDataBuilder':
        """Set category as private."""
        self.data["visibility"] = "PRIVATE"
        return self
    
    def build(self) -> Dict[str, Any]:
        """Build the category data."""
        return self.data.copy()