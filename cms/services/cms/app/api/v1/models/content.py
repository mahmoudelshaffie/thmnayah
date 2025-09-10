"""
Content Management Pydantic Models

This module contains all Pydantic models for content management operations
including multilingual content, category relationships, and analytics.
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from enum import Enum
from pydantic import Field, validator

from .common import BaseModel, TimestampMixin, MultilingualText, OptionalMultilingualText, PaginatedResponse


class ContentType(str, Enum):
    """Content type enumeration"""
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"
    ARTICLE = "ARTICLE"
    DOCUMENT = "DOCUMENT"
    IMAGE = "IMAGE"
    LIVE_STREAM = "LIVE_STREAM"


class ContentStatus(str, Enum):
    """Content status enumeration"""
    DRAFT = "DRAFT"
    PENDING_REVIEW = "PENDING_REVIEW"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"
    DELETED = "DELETED"


class ContentVisibility(str, Enum):
    """Content visibility enumeration"""
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"
    RESTRICTED = "RESTRICTED"


class ContentBase(BaseModel):
    """Base content model with common fields"""
    
    title: MultilingualText = Field(
        ..., 
        description="Content title in multiple languages (language code -> text)"
    )
    description: Optional[OptionalMultilingualText] = Field(
        None,
        description="Content description in multiple languages (language code -> text)"
    )
    body: Optional[OptionalMultilingualText] = Field(
        None,
        description="Content body/text in multiple languages (language code -> text)"
    )
    slug: Optional[OptionalMultilingualText] = Field(
        None,
        description="URL-friendly slugs in multiple languages (language code -> text)"
    )
    content_type: ContentType = Field(
        ...,
        description="Type of content (video, audio, article, etc.)"
    )
    primary_category_id: Optional[uuid.UUID] = Field(
        None,
        description="Primary category ID for this content"
    )
    status: ContentStatus = Field(
        ContentStatus.DRAFT,
        description="Content publication status"
    )
    visibility: ContentVisibility = Field(
        ContentVisibility.PUBLIC,
        description="Content visibility level"
    )
    is_featured: bool = Field(
        False,
        description="Whether content is featured"
    )


class ContentCreate(ContentBase):
    """Content creation model"""
    
    # Publishing information
    scheduled_at: Optional[datetime] = Field(
        None,
        description="Scheduled publication timestamp"
    )
    expires_at: Optional[datetime] = Field(
        None,
        description="Content expiration timestamp"
    )
    
    # Author information (author_id will be set by service layer)
    author_name: Optional[OptionalMultilingualText] = Field(
        None,
        description="Author name in multiple languages"
    )
    
    # File and media information
    file_url: Optional[str] = Field(
        None,
        max_length=1000,
        description="URL to main content file"
    )
    thumbnail_url: Optional[str] = Field(
        None,
        max_length=1000,
        description="URL to content thumbnail image"
    )
    file_size: Optional[int] = Field(
        None,
        ge=0,
        description="File size in bytes"
    )
    file_type: Optional[str] = Field(
        None,
        max_length=100,
        description="MIME type of the content file"
    )
    duration: Optional[int] = Field(
        None,
        ge=0,
        description="Content duration in seconds (for audio/video)"
    )
    
    # SEO fields
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
        description="SEO keywords/tags array"
    )
    
    # Tags and categorization
    tags: Optional[List[str]] = Field(
        None,
        description="Content tags array"
    )
    
    # Extensible metadata
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional content metadata"
    )
    
    @validator('title')
    def validate_title(cls, v):
        if not v or not any(v.values()):
            raise ValueError('Title must have at least one language with content')
        return v
    
    @validator('file_url', 'thumbnail_url')
    def validate_urls(cls, v):
        if v and not (v.startswith('http://') or v.startswith('https://') or v.startswith('/')):
            raise ValueError('URL must be a valid HTTP/HTTPS URL or absolute path')
        return v


class ContentUpdate(BaseModel):
    """Content update model - all fields optional"""
    
    title: Optional[MultilingualText] = Field(
        None,
        description="Content title in multiple languages"
    )
    description: Optional[OptionalMultilingualText] = Field(
        None,
        description="Content description in multiple languages"
    )
    body: Optional[OptionalMultilingualText] = Field(
        None,
        description="Content body/text in multiple languages"
    )
    slug: Optional[OptionalMultilingualText] = Field(
        None,
        description="URL-friendly slugs in multiple languages"
    )
    content_type: Optional[ContentType] = Field(
        None,
        description="Type of content"
    )
    primary_category_id: Optional[uuid.UUID] = Field(
        None,
        description="Primary category ID for this content"
    )
    status: Optional[ContentStatus] = Field(
        None,
        description="Content publication status"
    )
    visibility: Optional[ContentVisibility] = Field(
        None,
        description="Content visibility level"
    )
    is_featured: Optional[bool] = Field(
        None,
        description="Whether content is featured"
    )
    scheduled_at: Optional[datetime] = Field(
        None,
        description="Scheduled publication timestamp"
    )
    expires_at: Optional[datetime] = Field(
        None,
        description="Content expiration timestamp"
    )
    author_name: Optional[OptionalMultilingualText] = Field(
        None,
        description="Author name in multiple languages"
    )
    file_url: Optional[str] = Field(
        None,
        max_length=1000,
        description="URL to main content file"
    )
    thumbnail_url: Optional[str] = Field(
        None,
        max_length=1000,
        description="URL to content thumbnail image"
    )
    file_size: Optional[int] = Field(
        None,
        ge=0,
        description="File size in bytes"
    )
    file_type: Optional[str] = Field(
        None,
        max_length=100,
        description="MIME type of the content file"
    )
    duration: Optional[int] = Field(
        None,
        ge=0,
        description="Content duration in seconds"
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
        description="SEO keywords/tags array"
    )
    tags: Optional[List[str]] = Field(
        None,
        description="Content tags array"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional content metadata"
    )


class CategorySummary(BaseModel):
    """Category summary for content responses"""
    id: uuid.UUID = Field(..., description="Category ID")
    name: MultilingualText = Field(..., description="Category name in multiple languages")
    path: str = Field(..., description="Category hierarchical path")


class ContentResponse(ContentBase, TimestampMixin):
    """Content response model with all fields"""
    
    id: uuid.UUID = Field(..., description="Content unique identifier")
    
    # Publishing information
    published_at: Optional[datetime] = Field(
        None,
        description="Content publication timestamp"
    )
    scheduled_at: Optional[datetime] = Field(
        None,
        description="Scheduled publication timestamp"
    )
    expires_at: Optional[datetime] = Field(
        None,
        description="Content expiration timestamp"
    )
    
    # Author information
    author_id: Optional[uuid.UUID] = Field(
        None,
        description="Content author user ID"
    )
    author_name: Optional[OptionalMultilingualText] = Field(
        None,
        description="Author name in multiple languages"
    )
    
    # File and media information
    file_url: Optional[str] = Field(
        None,
        description="URL to main content file"
    )
    thumbnail_url: Optional[str] = Field(
        None,
        description="URL to content thumbnail image"
    )
    file_size: Optional[int] = Field(
        None,
        description="File size in bytes"
    )
    file_type: Optional[str] = Field(
        None,
        description="MIME type of the content file"
    )
    duration: Optional[int] = Field(
        None,
        description="Content duration in seconds"
    )
    
    # Engagement metrics
    view_count: int = Field(
        0,
        description="Total number of views"
    )
    like_count: int = Field(
        0,
        description="Total number of likes"
    )
    share_count: int = Field(
        0,
        description="Total number of shares"
    )
    comment_count: int = Field(
        0,
        description="Total number of comments"
    )
    
    # Content quality and rating
    rating: Optional[int] = Field(
        None,
        ge=1,
        le=5,
        description="Content rating (1-5 scale)"
    )
    rating_count: int = Field(
        0,
        description="Number of ratings"
    )
    
    # SEO fields
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
        description="SEO keywords/tags array"
    )
    
    # Tags and categorization
    tags: Optional[List[str]] = Field(
        None,
        description="Content tags array"
    )
    
    # Extensible metadata
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional content metadata"
    )
    
    # Relationships
    primary_category: Optional[CategorySummary] = Field(
        None,
        description="Primary category information"
    )


class ContentSearchFilters(BaseModel):
    """Content search filters"""
    
    query: Optional[str] = Field(
        None,
        description="Text search query"
    )
    language: str = Field(
        "ar",
        description="Search language preference"
    )
    content_type: Optional[ContentType] = Field(
        None,
        description="Filter by content type"
    )
    status: Optional[ContentStatus] = Field(
        None,
        description="Filter by content status"
    )
    visibility: Optional[ContentVisibility] = Field(
        None,
        description="Filter by visibility"
    )
    category_id: Optional[uuid.UUID] = Field(
        None,
        description="Filter by category"
    )
    author_id: Optional[uuid.UUID] = Field(
        None,
        description="Filter by author"
    )
    is_featured: Optional[bool] = Field(
        None,
        description="Filter featured content"
    )
    published_after: Optional[datetime] = Field(
        None,
        description="Filter by publication date (after)"
    )
    published_before: Optional[datetime] = Field(
        None,
        description="Filter by publication date (before)"
    )
    min_rating: Optional[int] = Field(
        None,
        ge=1,
        le=5,
        description="Minimum rating filter"
    )
    tags: Optional[List[str]] = Field(
        None,
        description="Filter by tags"
    )
    sort_by: str = Field(
        "created_at",
        description="Sort field"
    )
    sort_order: str = Field(
        "desc",
        description="Sort direction (asc/desc)"
    )


class ContentAnalytics(BaseModel):
    """Content analytics model"""
    
    content_id: uuid.UUID = Field(..., description="Content ID")
    content_title: MultilingualText = Field(..., description="Content title")
    
    # Engagement metrics
    view_count: int = Field(0, description="Total views")
    like_count: int = Field(0, description="Total likes")
    share_count: int = Field(0, description="Total shares")
    comment_count: int = Field(0, description="Total comments")
    total_engagement: int = Field(0, description="Total engagement count")
    engagement_rate: float = Field(0.0, description="Engagement rate percentage")
    
    # Rating metrics
    rating: Optional[int] = Field(None, description="Current rating")
    rating_count: int = Field(0, description="Number of ratings")
    average_rating: Optional[float] = Field(None, description="Average rating")
    
    # Publication info
    published_at: Optional[datetime] = Field(None, description="Publication timestamp")
    
    # Category context
    category_name: Optional[MultilingualText] = Field(None, description="Category name")


class ContentListResponse(PaginatedResponse[ContentResponse]):
    """Paginated content list response"""
    pass


# Content management request/response models

class ContentPublishRequest(BaseModel):
    """Request model for publishing content"""
    
    publish_immediately: bool = Field(
        True,
        description="Whether to publish immediately or use scheduled_at"
    )
    scheduled_at: Optional[datetime] = Field(
        None,
        description="When to publish (if not immediate)"
    )


class ContentBulkUpdateRequest(BaseModel):
    """Request model for bulk content updates"""
    
    content_ids: List[uuid.UUID] = Field(
        ...,
        min_items=1,
        max_items=50,
        description="List of content IDs to update (max 50)"
    )
    updates: Dict[str, Any] = Field(
        ...,
        description="Updates to apply to all selected content"
    )


class ContentBulkDeleteRequest(BaseModel):
    """Request model for bulk content deletion"""
    
    content_ids: List[uuid.UUID] = Field(
        ...,
        min_items=1,
        max_items=20,
        description="List of content IDs to delete (max 20)"
    )
    soft_delete: bool = Field(
        True,
        description="Whether to soft delete (mark as deleted) or hard delete"
    )


class ContentScheduleRequest(BaseModel):
    """Request model for scheduling content"""
    
    scheduled_at: datetime = Field(
        ...,
        description="When to publish the content"
    )
    
    @validator('scheduled_at')
    def validate_future_date(cls, v):
        if v <= datetime.utcnow():
            raise ValueError('Scheduled time must be in the future')
        return v


class ContentEngagementRequest(BaseModel):
    """Request model for content engagement actions"""
    
    action: str = Field(
        ...,
        description="Engagement action (like, share, view)"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional engagement metadata"
    )


class ContentEngagementResponse(BaseModel):
    """Response model for content engagement actions"""
    
    success: bool = Field(..., description="Whether action was successful")
    content_id: uuid.UUID = Field(..., description="Content ID")
    action: str = Field(..., description="Action performed")
    new_count: int = Field(..., description="New count after action")
    timestamp: datetime = Field(..., description="When action was performed")


# Content search and discovery models

class ContentRecommendationRequest(BaseModel):
    """Request model for content recommendations"""
    
    user_id: Optional[uuid.UUID] = Field(
        None,
        description="User ID for personalized recommendations"
    )
    category_id: Optional[uuid.UUID] = Field(
        None,
        description="Category to base recommendations on"
    )
    content_type: Optional[ContentType] = Field(
        None,
        description="Filter recommendations by content type"
    )
    limit: int = Field(
        10,
        ge=1,
        le=50,
        description="Number of recommendations to return"
    )


class ContentRecommendationResponse(BaseModel):
    """Response model for content recommendations"""
    
    recommendations: List[ContentResponse] = Field(
        ...,
        description="List of recommended content"
    )
    recommendation_reason: str = Field(
        ...,
        description="Reason for these recommendations"
    )
    generated_at: datetime = Field(
        ...,
        description="When recommendations were generated"
    )


class ContentTrendingResponse(BaseModel):
    """Response model for trending content"""
    
    trending_content: List[ContentResponse] = Field(
        ...,
        description="List of trending content"
    )
    period: str = Field(
        ...,
        description="Time period for trending calculation"
    )
    generated_at: datetime = Field(
        ...,
        description="When trending data was generated"
    )


class ContentStatsResponse(BaseModel):
    """Response model for content statistics"""
    
    total_content: int = Field(..., description="Total content count")
    published_content: int = Field(..., description="Published content count")
    draft_content: int = Field(..., description="Draft content count")
    pending_review: int = Field(..., description="Content pending review")
    archived_content: int = Field(..., description="Archived content count")
    
    by_type: Dict[str, int] = Field(..., description="Content count by type")
    by_category: Dict[str, int] = Field(..., description="Content count by category")
    by_author: Dict[str, int] = Field(..., description="Content count by author")
    
    total_views: int = Field(..., description="Total content views")
    total_likes: int = Field(..., description="Total content likes")
    total_shares: int = Field(..., description="Total content shares")
    
    generated_at: datetime = Field(..., description="When stats were generated")