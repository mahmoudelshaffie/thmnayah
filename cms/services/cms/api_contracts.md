# CMS API Contracts - FastAPI & Pydantic Design

## Overview

This document defines the REST API contracts for the thmnayah Content Management Service, designed for extensibility, multilingual support, and social content management capabilities.

**Design Principles:**
- **Multilingual First**: Native support for Arabic/English content
- **Extensible Schemas**: Easy to add new fields and content types
- **Social Content Ready**: Built for social media content patterns
- **API Versioning**: Future-proof with version support
- **Performance Optimized**: Efficient data structures and caching

---

## 🌐 Base Schema Design

### Multilingual Field Pattern
```python
from typing import Dict, Optional, Any, List, Union
from pydantic import BaseModel, Field, validator
from enum import Enum
import uuid
from datetime import datetime

class Language(str, Enum):
    ARABIC = "ar"
    ENGLISH = "en"

class MultilingualText(BaseModel):
    """Base model for multilingual text fields"""
    ar: Optional[str] = Field(None, description="Arabic text")
    en: Optional[str] = Field(None, description="English text")
    
    @validator('*')
    def validate_at_least_one_language(cls, v, values):
        if not any([values.get('ar'), values.get('en'), v]):
            raise ValueError('At least one language must be provided')
        return v
    
    def get_text(self, language: Language = Language.ARABIC) -> Optional[str]:
        """Get text in specified language with fallback"""
        return getattr(self, language.value) or getattr(self, Language.ENGLISH.value) or getattr(self, Language.ARABIC.value)
    
    def has_language(self, language: Language) -> bool:
        """Check if content exists in specified language"""
        return bool(getattr(self, language.value))

class ExtensibleMetadata(BaseModel):
    """Base model for extensible metadata"""
    custom_fields: Dict[str, Any] = Field(default_factory=dict, description="Custom extensible fields")
    tags: List[str] = Field(default_factory=list, description="Content tags")
    social_metadata: Dict[str, Any] = Field(default_factory=dict, description="Social media specific metadata")
    
    class Config:
        extra = "allow"  # Allow additional fields for future extensibility
```

---

## 📝 Content Management API Contracts

### Content Base Models
```python
class ContentType(str, Enum):
    VIDEO = "video"
    AUDIO = "audio" 
    ARTICLE = "article"
    SERIES = "series"
    EPISODE = "episode"
    LIVE_STREAM = "live_stream"
    SHORT_CLIP = "short_clip"  # Social media clips

class ContentStatus(str, Enum):
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    PUBLISHED = "published"
    SCHEDULED = "scheduled"
    ARCHIVED = "archived"
    DELETED = "deleted"

class ContentVisibility(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    UNLISTED = "unlisted"
    MEMBERS_ONLY = "members_only"

class SocialPlatform(str, Enum):
    YOUTUBE = "youtube"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    TWITTER = "twitter"
    TIKTOK = "tiktok"
    TELEGRAM = "telegram"

class MediaInfo(BaseModel):
    """Media file information"""
    url: str = Field(..., description="Media file URL")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    duration: Optional[int] = Field(None, description="Duration in seconds")
    mime_type: Optional[str] = Field(None, description="MIME type")
    resolution: Optional[str] = Field(None, description="Video resolution (e.g., 1920x1080)")
    bitrate: Optional[int] = Field(None, description="Bitrate in kbps")
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail image URL")
    
class SocialMetadata(BaseModel):
    """Social media platform specific metadata"""
    platform: SocialPlatform
    platform_id: Optional[str] = Field(None, description="Platform-specific content ID")
    platform_url: Optional[str] = Field(None, description="Direct platform URL")
    engagement_stats: Dict[str, int] = Field(default_factory=dict, description="Views, likes, shares, etc.")
    platform_metadata: Dict[str, Any] = Field(default_factory=dict, description="Platform-specific fields")
    sync_enabled: bool = Field(True, description="Enable sync with this platform")
    last_synced: Optional[datetime] = Field(None, description="Last sync timestamp")
```

### Core Content Schema
```python
class ContentBase(BaseModel):
    """Base content model with common fields"""
    title: MultilingualText = Field(..., description="Content title in multiple languages")
    description: Optional[MultilingualText] = Field(None, description="Content description")
    slug: Dict[Language, str] = Field(..., description="URL-friendly slug for each language")
    
    # Content Classification
    content_type: ContentType = Field(..., description="Type of content")
    category_id: Optional[uuid.UUID] = Field(None, description="Primary category")
    subcategory_ids: List[uuid.UUID] = Field(default_factory=list, description="Subcategories")
    
    # Status and Visibility
    status: ContentStatus = Field(ContentStatus.DRAFT, description="Content status")
    visibility: ContentVisibility = Field(ContentVisibility.PUBLIC, description="Content visibility")
    
    # Media and Files
    primary_media: Optional[MediaInfo] = Field(None, description="Primary media file (video/audio)")
    additional_media: List[MediaInfo] = Field(default_factory=list, description="Additional media files")
    thumbnail_url: Optional[str] = Field(None, description="Custom thumbnail URL")
    
    # Social and Engagement
    social_platforms: List[SocialMetadata] = Field(default_factory=list, description="Social platform associations")
    allow_comments: bool = Field(True, description="Enable comments")
    allow_sharing: bool = Field(True, description="Enable sharing")
    
    # Content Organization
    series_id: Optional[uuid.UUID] = Field(None, description="Associated series")
    episode_number: Optional[int] = Field(None, description="Episode number within series")
    season_number: Optional[int] = Field(1, description="Season number")
    
    # Scheduling and Publishing
    published_at: Optional[datetime] = Field(None, description="Publication timestamp")
    scheduled_for: Optional[datetime] = Field(None, description="Scheduled publication time")
    expires_at: Optional[datetime] = Field(None, description="Content expiration time")
    
    # SEO and Discovery
    seo_keywords: List[str] = Field(default_factory=list, description="SEO keywords")
    search_tags: List[str] = Field(default_factory=list, description="Search optimization tags")
    featured_until: Optional[datetime] = Field(None, description="Featured content expiry")
    
    # Extensible Metadata
    metadata: ExtensibleMetadata = Field(default_factory=ExtensibleMetadata, description="Extensible metadata")
    
    # Audit Fields
    created_by: uuid.UUID = Field(..., description="Creator user ID")
    updated_by: Optional[uuid.UUID] = Field(None, description="Last updater user ID")
    version: int = Field(1, description="Content version number")

class ContentCreate(ContentBase):
    """Schema for creating new content"""
    pass

class ContentUpdate(BaseModel):
    """Schema for updating existing content - all fields optional"""
    title: Optional[MultilingualText] = None
    description: Optional[MultilingualText] = None
    slug: Optional[Dict[Language, str]] = None
    content_type: Optional[ContentType] = None
    category_id: Optional[uuid.UUID] = None
    subcategory_ids: Optional[List[uuid.UUID]] = None
    status: Optional[ContentStatus] = None
    visibility: Optional[ContentVisibility] = None
    primary_media: Optional[MediaInfo] = None
    additional_media: Optional[List[MediaInfo]] = None
    thumbnail_url: Optional[str] = None
    social_platforms: Optional[List[SocialMetadata]] = None
    allow_comments: Optional[bool] = None
    allow_sharing: Optional[bool] = None
    series_id: Optional[uuid.UUID] = None
    episode_number: Optional[int] = None
    season_number: Optional[int] = None
    scheduled_for: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    seo_keywords: Optional[List[str]] = None
    search_tags: Optional[List[str]] = None
    featured_until: Optional[datetime] = None
    metadata: Optional[ExtensibleMetadata] = None
    updated_by: Optional[uuid.UUID] = None

class ContentResponse(ContentBase):
    """Schema for content responses"""
    id: uuid.UUID = Field(..., description="Content unique identifier")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    view_count: int = Field(0, description="Total view count")
    engagement_stats: Dict[str, int] = Field(default_factory=dict, description="Engagement statistics")
    
    # Related Content (populated by API)
    category: Optional[Dict[str, Any]] = Field(None, description="Category information")
    series: Optional[Dict[str, Any]] = Field(None, description="Series information")
    creator: Optional[Dict[str, Any]] = Field(None, description="Creator information")
    
    class Config:
        from_attributes = True
```

---

## 🔍 Search and Filtering Contracts

### Search Request Schema
```python
class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"

class SortBy(str, Enum):
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    PUBLISHED_AT = "published_at"
    TITLE = "title"
    VIEW_COUNT = "view_count"
    ENGAGEMENT_SCORE = "engagement_score"
    RELEVANCE = "relevance"

class ContentFilter(BaseModel):
    """Advanced content filtering options"""
    # Text Search
    query: Optional[str] = Field(None, description="Search query text")
    language: Optional[Language] = Field(None, description="Search in specific language")
    
    # Content Type Filters
    content_types: Optional[List[ContentType]] = Field(None, description="Filter by content types")
    categories: Optional[List[uuid.UUID]] = Field(None, description="Filter by categories")
    
    # Status and Visibility
    statuses: Optional[List[ContentStatus]] = Field(None, description="Filter by statuses")
    visibility: Optional[List[ContentVisibility]] = Field(None, description="Filter by visibility")
    
    # Date Ranges
    created_after: Optional[datetime] = Field(None, description="Created after date")
    created_before: Optional[datetime] = Field(None, description="Created before date")
    published_after: Optional[datetime] = Field(None, description="Published after date")
    published_before: Optional[datetime] = Field(None, description="Published before date")
    
    # Content Properties
    has_media: Optional[bool] = Field(None, description="Filter content with/without media")
    has_series: Optional[bool] = Field(None, description="Filter content with/without series")
    is_featured: Optional[bool] = Field(None, description="Filter featured content")
    
    # Social Platform Filters
    social_platforms: Optional[List[SocialPlatform]] = Field(None, description="Filter by social platforms")
    min_views: Optional[int] = Field(None, description="Minimum view count")
    max_views: Optional[int] = Field(None, description="Maximum view count")
    
    # Custom Fields
    custom_filters: Dict[str, Any] = Field(default_factory=dict, description="Custom field filters")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")

class SearchRequest(BaseModel):
    """Content search request"""
    filters: ContentFilter = Field(default_factory=ContentFilter, description="Search filters")
    
    # Pagination
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=100, description="Items per page")
    
    # Sorting
    sort_by: SortBy = Field(SortBy.CREATED_AT, description="Sort field")
    sort_order: SortOrder = Field(SortOrder.DESC, description="Sort order")
    
    # Response Options
    include_stats: bool = Field(False, description="Include engagement statistics")
    include_related: bool = Field(False, description="Include related content info")

class SearchResponse(BaseModel):
    """Content search response"""
    items: List[ContentResponse] = Field(..., description="Search results")
    total: int = Field(..., description="Total items matching query")
    page: int = Field(..., description="Current page")
    per_page: int = Field(..., description="Items per page")
    pages: int = Field(..., description="Total pages")
    has_next: bool = Field(..., description="Has next page")
    has_prev: bool = Field(..., description="Has previous page")
    
    # Search Metadata
    query_time: float = Field(..., description="Query execution time in seconds")
    facets: Dict[str, List[Dict[str, Any]]] = Field(default_factory=dict, description="Search facets")
```

---

## 🏷️ Category and Organization Contracts

### Category Management
```python
class CategoryType(str, Enum):
    TOPIC = "topic"          # Islamic topics
    FORMAT = "format"        # Video, audio, etc.
    AUDIENCE = "audience"    # Children, adults, scholars
    LANGUAGE = "language"    # Arabic, English content
    SERIES_TYPE = "series_type"  # Lecture series, courses

class Category(BaseModel):
    """Category base model"""
    name: MultilingualText = Field(..., description="Category name")
    description: Optional[MultilingualText] = Field(None, description="Category description")
    slug: Dict[Language, str] = Field(..., description="URL-friendly slug")
    
    # Hierarchy
    parent_id: Optional[uuid.UUID] = Field(None, description="Parent category ID")
    level: int = Field(0, description="Hierarchy level (0 = root)")
    path: str = Field(..., description="Full hierarchy path")
    
    # Classification
    category_type: CategoryType = Field(CategoryType.TOPIC, description="Category type")
    
    # Display Properties
    icon_url: Optional[str] = Field(None, description="Category icon URL")
    banner_url: Optional[str] = Field(None, description="Category banner image")
    color_scheme: Optional[str] = Field(None, description="UI color scheme")
    
    # Organization
    display_order: int = Field(0, description="Display order within parent")
    is_featured: bool = Field(False, description="Featured category flag")
    is_active: bool = Field(True, description="Category active status")
    
    # Content Rules
    allow_direct_content: bool = Field(True, description="Allow content directly in this category")
    content_types_allowed: List[ContentType] = Field(default_factory=list, description="Allowed content types")
    
    # SEO and Metadata
    seo_title: Optional[MultilingualText] = Field(None, description="SEO title")
    seo_description: Optional[MultilingualText] = Field(None, description="SEO description")
    metadata: ExtensibleMetadata = Field(default_factory=ExtensibleMetadata)

class CategoryCreate(Category):
    pass

class CategoryUpdate(BaseModel):
    """Category update schema - all fields optional"""
    name: Optional[MultilingualText] = None
    description: Optional[MultilingualText] = None
    slug: Optional[Dict[Language, str]] = None
    parent_id: Optional[uuid.UUID] = None
    category_type: Optional[CategoryType] = None
    icon_url: Optional[str] = None
    banner_url: Optional[str] = None
    color_scheme: Optional[str] = None
    display_order: Optional[int] = None
    is_featured: Optional[bool] = None
    is_active: Optional[bool] = None
    allow_direct_content: Optional[bool] = None
    content_types_allowed: Optional[List[ContentType]] = None
    seo_title: Optional[MultilingualText] = None
    seo_description: Optional[MultilingualText] = None
    metadata: Optional[ExtensibleMetadata] = None

class CategoryResponse(Category):
    """Category response with additional data"""
    id: uuid.UUID = Field(..., description="Category ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    # Statistics
    content_count: int = Field(0, description="Number of content items")
    subcategory_count: int = Field(0, description="Number of subcategories")
    
    # Relationships (populated by API)
    parent: Optional['CategoryResponse'] = Field(None, description="Parent category")
    children: List['CategoryResponse'] = Field(default_factory=list, description="Child categories")
    
    class Config:
        from_attributes = True

# Enable forward references
CategoryResponse.model_rebuild()
```

---

## 📺 Series and Episodes Contracts

### Series Management
```python
class SeriesType(str, Enum):
    LECTURE_SERIES = "lecture_series"
    COURSE = "course"
    PODCAST = "podcast"
    DOCUMENTARY = "documentary"
    LIVE_SERIES = "live_series"
    SHORT_SERIES = "short_series"

class SeriesStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"
    CANCELLED = "cancelled"

class Series(BaseModel):
    """Series base model"""
    title: MultilingualText = Field(..., description="Series title")
    description: Optional[MultilingualText] = Field(None, description="Series description")
    slug: Dict[Language, str] = Field(..., description="URL-friendly slug")
    
    # Classification
    series_type: SeriesType = Field(..., description="Type of series")
    category_id: uuid.UUID = Field(..., description="Primary category")
    subcategory_ids: List[uuid.UUID] = Field(default_factory=list, description="Subcategories")
    
    # Status and Properties
    status: SeriesStatus = Field(SeriesStatus.ACTIVE, description="Series status")
    visibility: ContentVisibility = Field(ContentVisibility.PUBLIC, description="Series visibility")
    
    # Organization
    total_episodes: Optional[int] = Field(None, description="Total planned episodes")
    total_seasons: int = Field(1, description="Total seasons")
    episode_naming_pattern: str = Field("Episode {number}", description="Episode naming pattern")
    
    # Media and Presentation
    poster_url: Optional[str] = Field(None, description="Series poster image")
    banner_url: Optional[str] = Field(None, description="Series banner image")
    trailer_url: Optional[str] = Field(None, description="Series trailer video")
    
    # Schedule and Publishing
    publish_schedule: Optional[str] = Field(None, description="Publishing schedule (e.g., 'Weekly', 'Daily')")
    next_episode_date: Optional[datetime] = Field(None, description="Next episode release date")
    
    # Social and Engagement
    social_platforms: List[SocialMetadata] = Field(default_factory=list, description="Social platform info")
    allow_episode_comments: bool = Field(True, description="Enable comments on episodes")
    notify_subscribers: bool = Field(True, description="Notify subscribers of new episodes")
    
    # SEO and Discovery
    seo_keywords: List[str] = Field(default_factory=list, description="SEO keywords")
    featured_until: Optional[datetime] = Field(None, description="Featured series expiry")
    
    # Extensible Metadata
    metadata: ExtensibleMetadata = Field(default_factory=ExtensibleMetadata)
    
    # Audit
    created_by: uuid.UUID = Field(..., description="Creator user ID")

class SeriesCreate(Series):
    pass

class SeriesUpdate(BaseModel):
    """Series update schema"""
    title: Optional[MultilingualText] = None
    description: Optional[MultilingualText] = None
    slug: Optional[Dict[Language, str]] = None
    series_type: Optional[SeriesType] = None
    category_id: Optional[uuid.UUID] = None
    subcategory_ids: Optional[List[uuid.UUID]] = None
    status: Optional[SeriesStatus] = None
    visibility: Optional[ContentVisibility] = None
    total_episodes: Optional[int] = None
    total_seasons: Optional[int] = None
    episode_naming_pattern: Optional[str] = None
    poster_url: Optional[str] = None
    banner_url: Optional[str] = None
    trailer_url: Optional[str] = None
    publish_schedule: Optional[str] = None
    next_episode_date: Optional[datetime] = None
    social_platforms: Optional[List[SocialMetadata]] = None
    allow_episode_comments: Optional[bool] = None
    notify_subscribers: Optional[bool] = None
    seo_keywords: Optional[List[str]] = None
    featured_until: Optional[datetime] = None
    metadata: Optional[ExtensibleMetadata] = None

class SeriesResponse(Series):
    """Series response with additional data"""
    id: uuid.UUID = Field(..., description="Series ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    # Statistics
    published_episodes: int = Field(0, description="Number of published episodes")
    total_views: int = Field(0, description="Total series views")
    subscriber_count: int = Field(0, description="Number of subscribers")
    
    # Relationships (populated by API)
    category: Optional[Dict[str, Any]] = Field(None, description="Category information")
    creator: Optional[Dict[str, Any]] = Field(None, description="Creator information")
    latest_episode: Optional[ContentResponse] = Field(None, description="Latest episode")
    episodes: List[ContentResponse] = Field(default_factory=list, description="Series episodes")
    
    class Config:
        from_attributes = True
```

---

## 🔐 User and Authentication Contracts

### User Management
```python
class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    CONTENT_MANAGER = "content_manager"
    CONTENT_EDITOR = "content_editor"
    CONTENT_REVIEWER = "content_reviewer"
    SOCIAL_MANAGER = "social_manager"  # Manages social media integration
    VIEWER = "viewer"

class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"

class UserPreferences(BaseModel):
    """User preferences and settings"""
    preferred_language: Language = Field(Language.ARABIC, description="Preferred UI language")
    timezone: str = Field("UTC", description="User timezone")
    date_format: str = Field("DD/MM/YYYY", description="Preferred date format")
    
    # Content Preferences
    default_content_language: Language = Field(Language.ARABIC, description="Default content creation language")
    auto_publish_social: bool = Field(False, description="Auto-publish to social platforms")
    notification_preferences: Dict[str, bool] = Field(default_factory=dict, description="Notification settings")

class User(BaseModel):
    """User base model"""
    email: str = Field(..., description="User email")
    username: Optional[str] = Field(None, description="Username (optional)")
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    
    # Profile
    display_name: Optional[str] = Field(None, description="Public display name")
    bio: Optional[MultilingualText] = Field(None, description="User bio")
    avatar_url: Optional[str] = Field(None, description="Profile avatar URL")
    cover_url: Optional[str] = Field(None, description="Profile cover image URL")
    
    # Authorization
    role: UserRole = Field(UserRole.CONTENT_EDITOR, description="User role")
    status: UserStatus = Field(UserStatus.PENDING_VERIFICATION, description="User status")
    permissions: List[str] = Field(default_factory=list, description="Additional permissions")
    
    # Settings
    preferences: UserPreferences = Field(default_factory=UserPreferences, description="User preferences")
    
    # Social Media Accounts (for content management)
    social_accounts: Dict[SocialPlatform, Dict[str, Any]] = Field(default_factory=dict, description="Connected social accounts")
    
    # Extensible
    metadata: ExtensibleMetadata = Field(default_factory=ExtensibleMetadata)

class UserCreate(User):
    """User creation schema"""
    password: str = Field(..., min_length=8, description="User password")

class UserUpdate(BaseModel):
    """User update schema"""
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: Optional[str] = None
    bio: Optional[MultilingualText] = None
    avatar_url: Optional[str] = None
    cover_url: Optional[str] = None
    preferences: Optional[UserPreferences] = None
    social_accounts: Optional[Dict[SocialPlatform, Dict[str, Any]]] = None
    metadata: Optional[ExtensibleMetadata] = None

class UserResponse(User):
    """User response schema"""
    id: uuid.UUID = Field(..., description="User ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    
    # Statistics
    content_count: int = Field(0, description="Number of content items created")
    series_count: int = Field(0, description="Number of series created")
    
    class Config:
        from_attributes = True

# Authentication Schemas
class TokenData(BaseModel):
    """JWT token data"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token") 
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiry in seconds")
    user: UserResponse = Field(..., description="User information")

class LoginRequest(BaseModel):
    """User login request"""
    email: str = Field(..., description="User email")
    password: str = Field(..., description="User password")
    remember_me: bool = Field(False, description="Extended session")

class RefreshTokenRequest(BaseModel):
    """Token refresh request"""
    refresh_token: str = Field(..., description="Refresh token")
```

---

## 🚀 FastAPI Route Implementation

### Content Management Routes
```python
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List
import uuid

router = APIRouter(prefix="/api/v1/content", tags=["content"])

@router.post("/", response_model=ContentResponse, status_code=status.HTTP_201_CREATED)
async def create_content(
    content: ContentCreate,
    current_user: UserResponse = Depends(get_current_user),
    content_service = Depends(get_content_service)
) -> ContentResponse:
    """
    Create new content
    
    - **title**: Content title in multiple languages
    - **content_type**: Type of content (video, audio, article, etc.)
    - **category_id**: Primary category assignment
    - **visibility**: Content visibility settings
    
    Returns created content with generated ID and timestamps.
    """
    content.created_by = current_user.id
    return await content_service.create_content(content)

@router.get("/", response_model=SearchResponse)
async def search_content(
    search_request: SearchRequest = Depends(),
    current_user: UserResponse = Depends(get_current_user)
) -> SearchResponse:
    """
    Search and filter content
    
    Supports advanced filtering by:
    - Text search across multilingual fields
    - Content type, category, status filters
    - Date range filtering
    - Social platform filtering
    - Custom field filtering
    """
    return await content_service.search_content(search_request, current_user)

@router.get("/{content_id}", response_model=ContentResponse)
async def get_content(
    content_id: uuid.UUID,
    language: Optional[Language] = Query(None, description="Preferred language"),
    include_stats: bool = Query(False, description="Include engagement statistics"),
    include_related: bool = Query(False, description="Include related content"),
    current_user: UserResponse = Depends(get_current_user)
) -> ContentResponse:
    """Get content by ID with optional language preference and additional data"""
    return await content_service.get_content(
        content_id, 
        language=language,
        include_stats=include_stats,
        include_related=include_related,
        user=current_user
    )

@router.put("/{content_id}", response_model=ContentResponse)
async def update_content(
    content_id: uuid.UUID,
    content_update: ContentUpdate,
    current_user: UserResponse = Depends(get_current_user)
) -> ContentResponse:
    """Update existing content"""
    content_update.updated_by = current_user.id
    return await content_service.update_content(content_id, content_update, current_user)

@router.delete("/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_content(
    content_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user)
):
    """Soft delete content (changes status to deleted)"""
    await content_service.delete_content(content_id, current_user)

@router.post("/{content_id}/publish", response_model=ContentResponse)
async def publish_content(
    content_id: uuid.UUID,
    scheduled_for: Optional[datetime] = None,
    publish_to_social: bool = Query(False, description="Auto-publish to connected social platforms"),
    current_user: UserResponse = Depends(get_current_user)
) -> ContentResponse:
    """Publish content immediately or schedule for later"""
    return await content_service.publish_content(
        content_id, 
        scheduled_for=scheduled_for,
        publish_to_social=publish_to_social,
        user=current_user
    )

@router.post("/{content_id}/duplicate", response_model=ContentResponse)
async def duplicate_content(
    content_id: uuid.UUID,
    title_suffix: Optional[str] = Query(" (Copy)", description="Suffix for duplicated content title"),
    current_user: UserResponse = Depends(get_current_user)
) -> ContentResponse:
    """Create a duplicate of existing content"""
    return await content_service.duplicate_content(content_id, title_suffix, current_user)

# Bulk Operations
@router.post("/bulk/update", response_model=List[ContentResponse])
async def bulk_update_content(
    content_ids: List[uuid.UUID],
    updates: ContentUpdate,
    current_user: UserResponse = Depends(get_current_user)
) -> List[ContentResponse]:
    """Update multiple content items at once"""
    return await content_service.bulk_update_content(content_ids, updates, current_user)

@router.post("/bulk/publish", response_model=List[ContentResponse])
async def bulk_publish_content(
    content_ids: List[uuid.UUID],
    scheduled_for: Optional[datetime] = None,
    current_user: UserResponse = Depends(get_current_user)
) -> List[ContentResponse]:
    """Publish multiple content items"""
    return await content_service.bulk_publish_content(content_ids, scheduled_for, current_user)

# Social Media Integration
@router.post("/{content_id}/social/sync", response_model=ContentResponse)
async def sync_to_social_platforms(
    content_id: uuid.UUID,
    platforms: List[SocialPlatform],
    current_user: UserResponse = Depends(get_current_user)
) -> ContentResponse:
    """Sync content to specified social media platforms"""
    return await social_service.sync_content_to_platforms(content_id, platforms, current_user)

@router.get("/{content_id}/social/stats", response_model=Dict[str, Any])
async def get_social_stats(
    content_id: uuid.UUID,
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get aggregated social media statistics for content"""
    return await social_service.get_content_social_stats(content_id)
```

### Series Management Routes
```python
series_router = APIRouter(prefix="/api/v1/series", tags=["series"])

@series_router.post("/", response_model=SeriesResponse, status_code=status.HTTP_201_CREATED)
async def create_series(
    series: SeriesCreate,
    current_user: UserResponse = Depends(get_current_user)
) -> SeriesResponse:
    """Create a new content series"""
    series.created_by = current_user.id
    return await series_service.create_series(series)

@series_router.get("/{series_id}", response_model=SeriesResponse)
async def get_series(
    series_id: uuid.UUID,
    include_episodes: bool = Query(False, description="Include episodes in response"),
    language: Optional[Language] = Query(None, description="Preferred language"),
    current_user: UserResponse = Depends(get_current_user)
) -> SeriesResponse:
    """Get series details with optional episodes"""
    return await series_service.get_series(
        series_id, 
        include_episodes=include_episodes,
        language=language
    )

@series_router.post("/{series_id}/episodes", response_model=ContentResponse)
async def add_episode_to_series(
    series_id: uuid.UUID,
    content_id: uuid.UUID,
    episode_number: Optional[int] = None,
    season_number: int = 1,
    current_user: UserResponse = Depends(get_current_user)
) -> ContentResponse:
    """Add existing content as episode to series"""
    return await series_service.add_episode(
        series_id, 
        content_id, 
        episode_number=episode_number,
        season_number=season_number,
        user=current_user
    )

@series_router.get("/{series_id}/episodes", response_model=List[ContentResponse])
async def get_series_episodes(
    series_id: uuid.UUID,
    season: Optional[int] = Query(None, description="Filter by season"),
    status: Optional[ContentStatus] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: UserResponse = Depends(get_current_user)
) -> List[ContentResponse]:
    """Get series episodes with filtering and pagination"""
    return await series_service.get_series_episodes(
        series_id,
        season=season,
        status=status,
        page=page,
        per_page=per_page
    )
```

### Category Management Routes  
```python
category_router = APIRouter(prefix="/api/v1/categories", tags=["categories"])

@category_router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category: CategoryCreate,
    current_user: UserResponse = Depends(get_current_user)
) -> CategoryResponse:
    """Create a new category"""
    return await category_service.create_category(category, current_user)

@category_router.get("/", response_model=List[CategoryResponse])
async def get_categories(
    parent_id: Optional[uuid.UUID] = Query(None, description="Filter by parent category"),
    category_type: Optional[CategoryType] = Query(None, description="Filter by category type"),
    include_inactive: bool = Query(False, description="Include inactive categories"),
    language: Optional[Language] = Query(None, description="Preferred language"),
    current_user: UserResponse = Depends(get_current_user)
) -> List[CategoryResponse]:
    """Get categories with hierarchical structure"""
    return await category_service.get_categories(
        parent_id=parent_id,
        category_type=category_type,
        include_inactive=include_inactive,
        language=language
    )

@category_router.get("/tree", response_model=List[CategoryResponse])
async def get_category_tree(
    language: Optional[Language] = Query(Language.ARABIC, description="Preferred language"),
    max_depth: int = Query(5, ge=1, le=10, description="Maximum tree depth"),
    current_user: UserResponse = Depends(get_current_user)
) -> List[CategoryResponse]:
    """Get complete category tree structure"""
    return await category_service.get_category_tree(language=language, max_depth=max_depth)

@category_router.get("/{category_id}/content", response_model=SearchResponse)
async def get_category_content(
    category_id: uuid.UUID,
    include_subcategories: bool = Query(True, description="Include content from subcategories"),
    content_type: Optional[ContentType] = Query(None, description="Filter by content type"),
    status: Optional[ContentStatus] = Query(ContentStatus.PUBLISHED, description="Filter by status"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: UserResponse = Depends(get_current_user)
) -> SearchResponse:
    """Get content within category"""
    search_request = SearchRequest(
        filters=ContentFilter(
            categories=[category_id],
            content_types=[content_type] if content_type else None,
            statuses=[status] if status else None
        ),
        page=page,
        per_page=per_page
    )
    return await content_service.search_content(search_request, current_user)
```

---

## 🔧 Implementation Guidelines

### Extensibility Patterns
```python
# 1. Custom Field Extensions
class ExtensibleContent(ContentBase):
    """Example of extending content with custom fields"""
    # Islamic content specific fields
    islamic_topics: List[str] = Field(default_factory=list, description="Islamic topic tags")
    hadith_references: List[str] = Field(default_factory=list, description="Hadith references")
    quran_references: List[str] = Field(default_factory=list, description="Quran verse references")
    scholar_tags: List[str] = Field(default_factory=list, description="Scholar/speaker tags")
    
    # Social content extensions
    hashtags: List[str] = Field(default_factory=list, description="Social media hashtags")
    target_audience: List[str] = Field(default_factory=list, description="Target audience tags")
    content_warnings: List[str] = Field(default_factory=list, description="Content warnings")

# 2. Platform-Specific Extensions
class YouTubeMetadata(BaseModel):
    video_id: str
    channel_id: str
    playlist_ids: List[str] = Field(default_factory=list)
    thumbnail_urls: Dict[str, str] = Field(default_factory=dict)  # quality -> url
    captions_available: List[str] = Field(default_factory=list)  # languages

class InstagramMetadata(BaseModel):
    post_id: str
    post_type: str  # photo, video, carousel, reel, story
    media_urls: List[str] = Field(default_factory=list)
    story_highlights: List[str] = Field(default_factory=list)

# 3. Future AI Extensions (Phase 2 ready)
class AIMetadata(BaseModel):
    """AI-generated metadata (Phase 2)"""
    auto_tags: List[str] = Field(default_factory=list, description="AI-generated tags")
    content_summary: Optional[MultilingualText] = Field(None, description="AI-generated summary")
    sentiment_score: Optional[float] = Field(None, description="Content sentiment analysis")
    topics_detected: List[str] = Field(default_factory=list, description="AI-detected topics")
    language_confidence: Dict[Language, float] = Field(default_factory=dict, description="Language detection confidence")
    embedding_version: Optional[str] = Field(None, description="Embedding model version")
```

### Validation and Business Rules
```python
from pydantic import validator, root_validator

class ContentCreateWithValidation(ContentCreate):
    """Content creation with business rule validation"""
    
    @validator('slug')
    def validate_slug_uniqueness(cls, v, values):
        """Ensure slug is unique across languages"""
        # This would typically check database uniqueness
        return v
    
    @root_validator
    def validate_series_episode_logic(cls, values):
        """Validate series and episode relationship"""
        series_id = values.get('series_id')
        episode_number = values.get('episode_number')
        
        if series_id and not episode_number:
            raise ValueError('Episode number required when assigning to series')
        
        if episode_number and not series_id:
            raise ValueError('Series ID required when setting episode number')
            
        return values
    
    @validator('social_platforms')
    def validate_social_platform_data(cls, v):
        """Validate social platform metadata"""
        for platform_data in v:
            if platform_data.sync_enabled and not platform_data.platform_id:
                raise ValueError(f'Platform ID required for {platform_data.platform} when sync is enabled')
        return v
    
    @validator('scheduled_for')
    def validate_future_schedule(cls, v):
        """Ensure scheduled time is in the future"""
        if v and v <= datetime.utcnow():
            raise ValueError('Scheduled time must be in the future')
        return v
```

This comprehensive API contract design provides:

✅ **Multilingual Support** - Native Arabic/English support with fallback mechanisms  
✅ **Social Content Ready** - Built-in social platform metadata and sync capabilities  
✅ **Highly Extensible** - Custom fields, platform-specific extensions, future AI integration  
✅ **Performance Optimized** - Efficient pagination, filtering, and optional data loading  
✅ **Business Rule Validation** - Comprehensive validation with clear error messages  
✅ **Future-Proof** - Ready for Phase 2 AI enhancements and Phase 3 advanced features

The schemas support all user stories while maintaining flexibility for future requirements and social media management needs.

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"content": "Design REST API contracts with FastAPI and Pydantic", "status": "completed", "activeForm": "Designing REST API contracts with FastAPI and Pydantic"}, {"content": "Implement multilingual content support", "status": "completed", "activeForm": "Implementing multilingual content support"}, {"content": "Create extensible schema design", "status": "completed", "activeForm": "Creating extensible schema design"}]