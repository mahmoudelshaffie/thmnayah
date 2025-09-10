"""
Category Management Pydantic Models

This module contains all Pydantic models for category management operations
including hierarchical categories, multilingual support, and analytics.
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import Field, validator

from .common import BaseModel, TimestampMixin, MultilingualText, OptionalMultilingualText, PaginatedResponse


class CategoryType(str, Enum):
    """Category type enumeration"""
    TOPIC = "TOPIC"
    FORMAT = "FORMAT"
    AUDIENCE = "AUDIENCE"
    LANGUAGE = "LANGUAGE"
    SERIES_TYPE = "SERIES_TYPE"


class CategoryStatus(str, Enum):
    """Category status enumeration"""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ARCHIVED = "ARCHIVED"


class CategoryVisibility(str, Enum):
    """Category visibility enumeration"""
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"
    RESTRICTED = "RESTRICTED"


class CategoryBase(BaseModel):
    """Base category model with common fields"""
    
    name: MultilingualText = Field(
        ..., 
        description="Category name in multiple languages (language code -> text)"
    )
    description: Optional[OptionalMultilingualText] = Field(
        None,
        description="Category description in multiple languages (language code -> text)"
    )
    slug: Optional[OptionalMultilingualText] = Field(
        None,
        description="URL-friendly slug in multiple languages (auto-generated if not provided)"
    )
    category_type: CategoryType = Field(
        ...,
        description="Type of category (topic, format, audience, etc.)"
    )
    parent_id: Optional[uuid.UUID] = Field(
        None,
        description="Parent category ID for hierarchical structure"
    )
    is_active: bool = Field(
        True,
        description="Whether the category is active and visible"
    )
    visibility: CategoryVisibility = Field(
        CategoryVisibility.PUBLIC,
        description="Category visibility level"
    )
    icon_url: Optional[str] = Field(
        None,
        description="URL to category icon image",
        max_length=500,
        example="/icons/technology.svg"
    )
    banner_url: Optional[str] = Field(
        None,
        description="URL to category banner image",
        max_length=500,
        example="/banners/technology-banner.jpg"
    )
    color_scheme: Optional[str] = Field(
        None,
        description="Category theme color (hex code)",
        pattern=r'^#[0-9A-Fa-f]{6}$',
        example="#2ECC71"
    )
    sort_order: int = Field(
        0,
        description="Sort order within parent category",
        ge=0,
        example=1
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional category metadata"
    )


class CategoryCreate(CategoryBase):
    """Model for creating a new category"""
    
    # SEO fields for category creation
    seo_title: Optional[OptionalMultilingualText] = Field(
        None,
        description="SEO-optimized title for search engines in multiple languages"
    )
    seo_description: Optional[OptionalMultilingualText] = Field(
        None,
        description="SEO meta description for search engines in multiple languages"
    )
    seo_keywords: Optional[List[str]] = Field(
        None,
        description="SEO keywords/tags",
        max_items=20,
        example=["technology", "programming", "education"]
    )
    
    @validator('parent_id')
    def validate_parent_id(cls, v, values):
        """Ensure parent_id is not the same as category itself"""
        # Note: This will be enhanced with actual parent existence validation in the service layer
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": {
                    "en": "Technology",
                    "ar": "التكنولوجيا",
                    "fr": "Technologie",
                    "es": "Tecnología"
                },
                "description": {
                    "en": "Technology and programming category",
                    "ar": "فئة التكنولوجيا والبرمجة",
                    "fr": "Catégorie technologie et programmation"
                },
                "category_type": "topic",
                "parent_id": "123e4567-e89b-12d3-a456-426614174000",
                "is_active": True,
                "visibility": "public",
                "icon_url": "/icons/technology.svg",
                "color_scheme": "#2ECC71",
                "sort_order": 1,
                "seo_title": {
                    "en": "Technology - Lessons and Lectures",
                    "ar": "التكنولوجيا - دروس ومحاضرات",
                    "fr": "Technologie - Cours et Conférences"
                },
                "seo_description": {
                    "en": "Learn technology through specialized lessons and lectures",
                    "ar": "تعلم التكنولوجيا من خلال دروس ومحاضرات متخصصة"
                },
                "seo_keywords": ["technology", "programming", "education"]
            }
        }


class CategoryUpdate(BaseModel):
    """Model for updating an existing category"""
    
    name: Optional[OptionalMultilingualText] = Field(
        None,
        description="Updated category name in multiple languages"
    )
    description: Optional[OptionalMultilingualText] = Field(
        None,
        description="Updated category description in multiple languages"
    )
    slug: Optional[OptionalMultilingualText] = Field(
        None,
        description="Updated URL-friendly slug in multiple languages"
    )
    parent_id: Optional[uuid.UUID] = Field(
        None,
        description="Updated parent category ID"
    )
    is_active: Optional[bool] = Field(
        None,
        description="Updated active status"
    )
    visibility: Optional[CategoryVisibility] = Field(
        None,
        description="Updated visibility level"
    )
    icon_url: Optional[str] = Field(
        None,
        description="Updated icon URL",
        max_length=500
    )
    banner_url: Optional[str] = Field(
        None,
        description="Updated banner URL",
        max_length=500
    )
    color_scheme: Optional[str] = Field(
        None,
        description="Updated color scheme",
        pattern=r'^#[0-9A-Fa-f]{6}$'
    )
    sort_order: Optional[int] = Field(
        None,
        description="Updated sort order",
        ge=0
    )
    seo_title: Optional[OptionalMultilingualText] = Field(
        None,
        description="Updated SEO title in multiple languages"
    )
    seo_description: Optional[OptionalMultilingualText] = Field(
        None,
        description="Updated SEO description in multiple languages"
    )
    seo_keywords: Optional[List[str]] = Field(
        None,
        description="Updated SEO keywords",
        max_items=20
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Updated metadata"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": {
                    "en": "Advanced Technology",
                    "ar": "التكنولوجيا المتقدمة",
                    "fr": "Technologie Avancée"
                },
                "is_active": True,
                "color_scheme": "#3498DB"
            }
        }


class CategoryResponse(CategoryBase, TimestampMixin):
    """Complete category response model"""
    
    id: uuid.UUID = Field(
        ...,
        description="Category unique identifier"
    )
    level: int = Field(
        ...,
        description="Hierarchy level (0 = root category)",
        ge=0,
        example=1
    )
    path: str = Field(
        ...,
        description="Full hierarchical path",
        example="/sciences/technology"
    )
    content_count: int = Field(
        ...,
        description="Number of content items in this category",
        ge=0,
        example=25
    )
    subcategory_count: int = Field(
        ...,
        description="Number of direct subcategories",
        ge=0,
        example=5
    )
    total_content_count: int = Field(
        ...,
        description="Total content count including subcategories",
        ge=0,
        example=150
    )
    seo_title: Optional[OptionalMultilingualText] = Field(
        None,
        description="SEO-optimized title in multiple languages"
    )
    seo_description: Optional[OptionalMultilingualText] = Field(
        None,
        description="SEO meta description in multiple languages"
    )
    seo_keywords: Optional[List[str]] = Field(
        None,
        description="SEO keywords"
    )
    
    # Parent category information (optional)
    parent: Optional[Dict[str, Any]] = Field(
        None,
        description="Parent category basic information"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": {
                    "en": "Technology",
                    "ar": "التكنولوجيا",
                    "fr": "Technologie",
                    "de": "Technologie",
                    "zh": "技术"
                },
                "description": {
                    "en": "Technology and programming category",
                    "ar": "فئة التكنولوجيا والبرمجة",
                    "fr": "Catégorie technologie et programmation"
                },
                "slug": {
                    "en": "technology",
                    "ar": "التكنولوجيا",
                    "fr": "technologie"
                },
                "category_type": "topic",
                "parent_id": "023e4567-e89b-12d3-a456-426614174000",
                "level": 1,
                "path": "/sciences/technology",
                "is_active": True,
                "visibility": "public",
                "content_count": 25,
                "subcategory_count": 5,
                "total_content_count": 150,
                "icon_url": "/icons/technology.svg",
                "color_scheme": "#2ECC71",
                "sort_order": 1,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            }
        }


class CategoryListResponse(PaginatedResponse[CategoryResponse]):
    """Paginated list of categories"""
    
    class Config:
        json_schema_extra = {
            "example": {
                "data": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": {
                            "en": "Technology",
                            "ar": "التكنولوجيا",
                            "fr": "Technologie"
                        },
                        "category_type": "topic",
                        "level": 0,
                        "content_count": 25,
                        "is_active": True,
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-01-15T10:30:00Z"
                    }
                ],
                "pagination": {
                    "page": 1,
                    "limit": 20,
                    "total": 50,
                    "total_pages": 3,
                    "has_next": True,
                    "has_prev": False
                }
            }
        }


class CategoryTreeNode(BaseModel):
    """Category tree node for hierarchical display"""
    
    id: uuid.UUID = Field(..., description="Category ID")
    name: MultilingualText = Field(..., description="Category name")
    slug: MultilingualText = Field(..., description="Category slug")
    category_type: CategoryType = Field(..., description="Category type")
    level: int = Field(..., description="Hierarchy level", ge=0)
    path: str = Field(..., description="Full path", example="/sciences/technology")
    parent_id: Optional[uuid.UUID] = Field(None, description="Parent category ID")
    is_active: bool = Field(..., description="Active status")
    content_count: int = Field(..., description="Direct content count", ge=0)
    total_content_count: int = Field(..., description="Total content count including subcategories", ge=0)
    icon_url: Optional[str] = Field(None, description="Icon URL")
    color_scheme: Optional[str] = Field(None, description="Color scheme")
    sort_order: int = Field(..., description="Sort order", ge=0)
    
    # Nested children
    children: List['CategoryTreeNode'] = Field(
        default_factory=list,
        description="Child categories"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": {
                    "en": "Sciences",
                    "ar": "العلوم",
                    "fr": "Sciences"
                },
                "slug": {
                    "en": "sciences",
                    "ar": "العلوم",
                    "fr": "sciences"
                },
                "category_type": "topic",
                "level": 0,
                "path": "/sciences",
                "parent_id": None,
                "is_active": True,
                "content_count": 15,
                "total_content_count": 150,
                "icon_url": "/icons/sciences.svg",
                "color_scheme": "#3498DB",
                "sort_order": 1,
                "children": [
                    {
                        "id": "223e4567-e89b-12d3-a456-426614174001",
                        "name": {
                            "en": "Technology",
                            "ar": "التكنولوجيا"
                        },
                        "level": 1,
                        "path": "/sciences/technology",
                        "content_count": 25,
                        "children": []
                    }
                ]
            }
        }

# Enable forward references for self-referencing model
CategoryTreeNode.model_rebuild()


class CategoryAnalytics(BaseModel):
    """Category analytics and performance metrics"""
    
    category_id: uuid.UUID = Field(..., description="Category ID")
    category_name: MultilingualText = Field(..., description="Category name")
    
    # Content metrics
    total_content: int = Field(..., description="Total content in category", ge=0)
    published_content: int = Field(..., description="Published content count", ge=0)
    draft_content: int = Field(..., description="Draft content count", ge=0)
    
    # Engagement metrics
    total_views: int = Field(..., description="Total category views", ge=0)
    unique_visitors: int = Field(..., description="Unique visitors count", ge=0)
    avg_engagement_time: float = Field(..., description="Average engagement time in seconds", ge=0)
    
    # Time-based metrics
    views_last_7_days: int = Field(..., description="Views in last 7 days", ge=0)
    views_last_30_days: int = Field(..., description="Views in last 30 days", ge=0)
    
    # Content performance
    top_content: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Top performing content in category"
    )
    
    # Growth metrics
    growth_rate: float = Field(
        ..., 
        description="Growth rate percentage (month over month)",
        example=15.5
    )
    
    # Popular subcategories
    popular_subcategories: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Most popular subcategories"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "category_id": "123e4567-e89b-12d3-a456-426614174000",
                "category_name": {
                    "en": "Technology",
                    "ar": "التكنولوجيا",
                    "fr": "Technologie"
                },
                "total_content": 45,
                "published_content": 40,
                "draft_content": 5,
                "total_views": 15420,
                "unique_visitors": 8950,
                "avg_engagement_time": 245.5,
                "views_last_7_days": 1200,
                "views_last_30_days": 4800,
                "growth_rate": 15.5,
                "top_content": [
                    {
                        "id": "content-123",
                        "title": {"en": "Introduction to Programming", "ar": "مقدمة في البرمجة"},
                        "views": 2500
                    }
                ],
                "popular_subcategories": [
                    {
                        "name": {"en": "Programming", "ar": "البرمجة"},
                        "views": 8500
                    }
                ]
            }
        }


class CategoryContentResponse(BaseModel):
    """Response model for category content listing"""
    
    category: Dict[str, Any] = Field(..., description="Category information")
    content: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Content items in the category"
    )
    subcategories: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Subcategories in this category"
    )
    total_content: int = Field(..., description="Total content count", ge=0)
    content_types: Dict[str, int] = Field(
        default_factory=dict,
        description="Breakdown of content by type"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "category": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "name": {"ar": "التكنولوجيا", "en": "Technology"},
                    "path": "/sciences/technology"
                },
                "content": [
                    {
                        "id": "content-123",
                        "title": {"en": "Introduction to Programming", "ar": "مقدمة في البرمجة"},
                        "type": "video",
                        "status": "published",
                        "created_at": "2024-01-15T10:30:00Z"
                    }
                ],
                "subcategories": [
                    {
                        "id": "subcat-456",
                        "name": {"en": "Programming", "ar": "البرمجة"},
                        "content_count": 15
                    }
                ],
                "total_content": 25,
                "content_types": {
                    "video": 15,
                    "article": 8,
                    "audio": 2
                }
            }
        }


class CategoryBulkUpdateRequest(BaseModel):
    """Request model for bulk category updates"""
    
    category_ids: List[uuid.UUID] = Field(
        ...,
        description="List of category IDs to update",
        min_items=1,
        max_items=50
    )
    updates: Dict[str, Any] = Field(
        ...,
        description="Fields to update for all selected categories"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "category_ids": [
                    "123e4567-e89b-12d3-a456-426614174000",
                    "223e4567-e89b-12d3-a456-426614174001"
                ],
                "updates": {
                    "is_active": True,
                    "visibility": "public"
                }
            }
        }


class ContentAssignmentRequest(BaseModel):
    """Request model for assigning content to a category"""
    
    is_primary: bool = Field(
        default=False,
        description="Whether this is the primary category for the content"
    )
    
    sort_order: Optional[int] = Field(
        default=None,
        description="Sort order within the category",
        ge=0
    )
    
    tags: Optional[List[str]] = Field(
        default=None,
        description="Additional tags for this content-category relationship",
        max_items=10
    )
    
    featured: bool = Field(
        default=False,
        description="Whether to feature this content in the category"
    )
    
    featured_until: Optional[datetime] = Field(
        default=None,
        description="Date until which the content should be featured"
    )
    
    notes: Optional[str] = Field(
        default=None,
        description="Internal notes about this assignment",
        max_length=500
    )
    
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata for the assignment"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "is_primary": True,
                "sort_order": 1,
                "tags": ["featured", "trending"],
                "featured": True,
                "featured_until": "2024-12-31T23:59:59Z",
                "notes": "Featured content for homepage",
                "metadata": {
                    "promotion_type": "homepage_banner",
                    "display_priority": "high"
                }
            }
        }


class ContentAssignmentResponse(BaseModel):
    """Response model for content assignment operations"""
    
    assignment_id: uuid.UUID = Field(
        ...,
        description="Unique identifier for the assignment"
    )
    
    category_id: uuid.UUID = Field(
        ..., 
        description="ID of the category"
    )
    
    content_id: uuid.UUID = Field(
        ...,
        description="ID of the assigned content"
    )
    
    is_primary: bool = Field(
        ...,
        description="Whether this is the primary category for the content"
    )
    
    sort_order: int = Field(
        ...,
        description="Sort order within the category"
    )
    
    featured: bool = Field(
        ...,
        description="Whether the content is featured in this category"
    )
    
    featured_until: Optional[datetime] = Field(
        None,
        description="Date until which the content is featured"
    )
    
    assigned_at: datetime = Field(
        ...,
        description="When the content was assigned to the category"
    )
    
    assigned_by: uuid.UUID = Field(
        ...,
        description="ID of the user who made the assignment"
    )
    
    tags: List[str] = Field(
        default_factory=list,
        description="Tags associated with this assignment"
    )
    
    notes: Optional[str] = Field(
        None,
        description="Internal notes about the assignment"
    )
    
    # Category and content summary info
    category_summary: Dict[str, Any] = Field(
        ...,
        description="Basic category information"
    )
    
    content_summary: Dict[str, Any] = Field(
        ...,
        description="Basic content information"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "assignment_id": "456e7890-e89b-12d3-a456-426614174001",
                "category_id": "123e4567-e89b-12d3-a456-426614174000",
                "content_id": "789e1234-e89b-12d3-a456-426614174002",
                "is_primary": True,
                "sort_order": 1,
                "featured": True,
                "featured_until": "2024-12-31T23:59:59Z",
                "assigned_at": "2024-01-15T10:30:00Z",
                "assigned_by": "user-123e4567-e89b-12d3-a456-426614174000",
                "tags": ["featured", "trending"],
                "notes": "Featured content for homepage",
                "category_summary": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "name": {"en": "Technology", "ar": "التكنولوجيا"},
                    "path": "/sciences/technology"
                },
                "content_summary": {
                    "id": "789e1234-e89b-12d3-a456-426614174002",
                    "title": {"en": "AI Introduction", "ar": "مقدمة في الذكاء الاصطناعي"},
                    "type": "video",
                    "status": "published"
                }
            }
        }


class ContentUnassignmentRequest(BaseModel):
    """Request model for unassigning content from a category"""
    
    reason: Optional[str] = Field(
        default=None,
        description="Reason for unassigning the content",
        max_length=500
    )
    
    reassign_to_category_id: Optional[uuid.UUID] = Field(
        default=None,
        description="Category ID to reassign content to (if applicable)"
    )
    
    preserve_metadata: bool = Field(
        default=False,
        description="Whether to preserve assignment metadata for audit purposes"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "reason": "Content no longer relevant to this category",
                "reassign_to_category_id": "456e7890-e89b-12d3-a456-426614174001",
                "preserve_metadata": True
            }
        }