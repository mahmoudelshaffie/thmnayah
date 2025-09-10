"""
Series Management Pydantic Models

This module contains all Pydantic models for series management operations
including multilingual series, episode relationships, and subscription management.
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from enum import Enum
from pydantic import Field, validator

from .common import BaseModel, TimestampMixin, MultilingualText, OptionalMultilingualText, PaginatedResponse


class SeriesStatus(str, Enum):
    """Series status enumeration"""
    DRAFT = "DRAFT"
    PENDING_REVIEW = "PENDING_REVIEW"
    PUBLISHED = "PUBLISHED"
    COMPLETED = "COMPLETED"
    PAUSED = "PAUSED"
    CANCELLED = "CANCELLED"
    ARCHIVED = "ARCHIVED"


class SeriesVisibility(str, Enum):
    """Series visibility enumeration"""
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"
    RESTRICTED = "RESTRICTED"


class SeriesType(str, Enum):
    """Series type enumeration"""
    EDUCATIONAL = "EDUCATIONAL"
    ENTERTAINMENT = "ENTERTAINMENT"
    NEWS = "NEWS"
    PODCAST = "PODCAST"
    DOCUMENTARY = "DOCUMENTARY"
    TUTORIAL = "TUTORIAL"
    WEBINAR = "WEBINAR"


class SubscriptionStatus(str, Enum):
    """Subscription status enumeration"""
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    CANCELLED = "CANCELLED"


class SeriesBase(BaseModel):
    """Base series model with common fields"""
    
    title: MultilingualText = Field(
        ..., 
        description="Series title in multiple languages (language code -> text)"
    )
    description: Optional[OptionalMultilingualText] = Field(
        None,
        description="Series description in multiple languages (language code -> text)"
    )
    slug: Optional[OptionalMultilingualText] = Field(
        None,
        description="URL-friendly slugs in multiple languages (language code -> text)"
    )
    series_type: SeriesType = Field(
        ...,
        description="Type of series (educational, entertainment, etc.)"
    )
    primary_category_id: Optional[uuid.UUID] = Field(
        None,
        description="Primary category ID for this series"
    )
    status: SeriesStatus = Field(
        SeriesStatus.DRAFT,
        description="Series publication status"
    )
    visibility: SeriesVisibility = Field(
        SeriesVisibility.PUBLIC,
        description="Series visibility level"
    )
    is_featured: bool = Field(
        False,
        description="Whether series is featured"
    )


class SeriesCreate(SeriesBase):
    """Series creation model"""
    
    # Publishing information
    scheduled_start_date: Optional[datetime] = Field(
        None,
        description="Scheduled series start date"
    )
    expected_end_date: Optional[datetime] = Field(
        None,
        description="Expected series completion date"
    )
    
    # Creator information (creator_id will be set by service layer)
    creator_name: Optional[OptionalMultilingualText] = Field(
        None,
        description="Creator name in multiple languages"
    )
    
    # Media information
    thumbnail_url: Optional[str] = Field(
        None,
        max_length=1000,
        description="URL to series thumbnail image"
    )
    banner_url: Optional[str] = Field(
        None,
        max_length=1000,
        description="URL to series banner image"
    )
    trailer_url: Optional[str] = Field(
        None,
        max_length=1000,
        description="URL to series trailer video"
    )
    
    # Series structure
    expected_episode_count: Optional[int] = Field(
        None,
        ge=1,
        description="Expected total number of episodes"
    )
    release_schedule: Optional[str] = Field(
        None,
        description="Release schedule description (e.g., 'Weekly on Mondays')"
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
        description="Series tags array"
    )
    
    # Extensible metadata
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional series metadata"
    )
    
    @validator('title')
    def validate_title(cls, v):
        if not v or not any(v.values()):
            raise ValueError('Title must have at least one language with content')
        return v
    
    @validator('thumbnail_url', 'banner_url', 'trailer_url')
    def validate_urls(cls, v):
        if v and not (v.startswith('http://') or v.startswith('https://') or v.startswith('/')):
            raise ValueError('URL must be a valid HTTP/HTTPS URL or absolute path')
        return v


class SeriesUpdate(BaseModel):
    """Series update model - all fields optional"""
    
    title: Optional[MultilingualText] = Field(
        None,
        description="Series title in multiple languages"
    )
    description: Optional[OptionalMultilingualText] = Field(
        None,
        description="Series description in multiple languages"
    )
    slug: Optional[OptionalMultilingualText] = Field(
        None,
        description="URL-friendly slugs in multiple languages"
    )
    series_type: Optional[SeriesType] = Field(
        None,
        description="Type of series"
    )
    primary_category_id: Optional[uuid.UUID] = Field(
        None,
        description="Primary category ID for this series"
    )
    status: Optional[SeriesStatus] = Field(
        None,
        description="Series publication status"
    )
    visibility: Optional[SeriesVisibility] = Field(
        None,
        description="Series visibility level"
    )
    is_featured: Optional[bool] = Field(
        None,
        description="Whether series is featured"
    )
    scheduled_start_date: Optional[datetime] = Field(
        None,
        description="Scheduled series start date"
    )
    expected_end_date: Optional[datetime] = Field(
        None,
        description="Expected series completion date"
    )
    creator_name: Optional[OptionalMultilingualText] = Field(
        None,
        description="Creator name in multiple languages"
    )
    thumbnail_url: Optional[str] = Field(
        None,
        max_length=1000,
        description="URL to series thumbnail image"
    )
    banner_url: Optional[str] = Field(
        None,
        max_length=1000,
        description="URL to series banner image"
    )
    trailer_url: Optional[str] = Field(
        None,
        max_length=1000,
        description="URL to series trailer video"
    )
    expected_episode_count: Optional[int] = Field(
        None,
        ge=1,
        description="Expected total number of episodes"
    )
    release_schedule: Optional[str] = Field(
        None,
        description="Release schedule description"
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
        description="Series tags array"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional series metadata"
    )


class EpisodeSummary(BaseModel):
    """Episode summary for series responses"""
    id: uuid.UUID = Field(..., description="Episode ID")
    title: MultilingualText = Field(..., description="Episode title in multiple languages")
    episode_number: int = Field(..., description="Episode number in series")
    season_number: Optional[int] = Field(None, description="Season number")
    duration: Optional[int] = Field(None, description="Episode duration in seconds")
    published_at: Optional[datetime] = Field(None, description="Episode publication date")
    is_free: bool = Field(True, description="Whether episode is free to access")


class SeriesResponse(SeriesBase, TimestampMixin):
    """Series response model with all fields"""
    
    id: uuid.UUID = Field(..., description="Series unique identifier")
    
    # Publishing information
    published_at: Optional[datetime] = Field(
        None,
        description="Series publication timestamp"
    )
    scheduled_start_date: Optional[datetime] = Field(
        None,
        description="Scheduled series start date"
    )
    expected_end_date: Optional[datetime] = Field(
        None,
        description="Expected series completion date"
    )
    actual_start_date: Optional[datetime] = Field(
        None,
        description="Actual series start date"
    )
    actual_end_date: Optional[datetime] = Field(
        None,
        description="Actual series end date"
    )
    
    # Creator information
    creator_id: Optional[uuid.UUID] = Field(
        None,
        description="Series creator user ID"
    )
    creator_name: Optional[OptionalMultilingualText] = Field(
        None,
        description="Creator name in multiple languages"
    )
    
    # Media information
    thumbnail_url: Optional[str] = Field(
        None,
        description="URL to series thumbnail image"
    )
    banner_url: Optional[str] = Field(
        None,
        description="URL to series banner image"
    )
    trailer_url: Optional[str] = Field(
        None,
        description="URL to series trailer video"
    )
    
    # Series structure
    episode_count: int = Field(
        0,
        description="Current number of episodes"
    )
    expected_episode_count: Optional[int] = Field(
        None,
        description="Expected total number of episodes"
    )
    season_count: int = Field(
        1,
        description="Number of seasons"
    )
    release_schedule: Optional[str] = Field(
        None,
        description="Release schedule description"
    )
    
    # Engagement metrics
    subscription_count: int = Field(
        0,
        description="Total number of subscriptions"
    )
    view_count: int = Field(
        0,
        description="Total series views (all episodes)"
    )
    like_count: int = Field(
        0,
        description="Total series likes"
    )
    share_count: int = Field(
        0,
        description="Total series shares"
    )
    comment_count: int = Field(
        0,
        description="Total series comments"
    )
    
    # Series quality and rating
    rating: Optional[float] = Field(
        None,
        ge=1.0,
        le=5.0,
        description="Average series rating (1-5 scale)"
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
        description="Series tags array"
    )
    
    # Extensible metadata
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional series metadata"
    )
    
    # Relationships
    primary_category: Optional[Dict[str, Any]] = Field(
        None,
        description="Primary category information"
    )
    latest_episodes: Optional[List[EpisodeSummary]] = Field(
        None,
        description="Latest episodes in the series"
    )


class SeriesSearchFilters(BaseModel):
    """Series search filters"""
    
    query: Optional[str] = Field(
        None,
        description="Text search query"
    )
    language: str = Field(
        "ar",
        description="Search language preference"
    )
    series_type: Optional[SeriesType] = Field(
        None,
        description="Filter by series type"
    )
    status: Optional[SeriesStatus] = Field(
        None,
        description="Filter by series status"
    )
    visibility: Optional[SeriesVisibility] = Field(
        None,
        description="Filter by visibility"
    )
    category_id: Optional[uuid.UUID] = Field(
        None,
        description="Filter by category"
    )
    creator_id: Optional[uuid.UUID] = Field(
        None,
        description="Filter by creator"
    )
    is_featured: Optional[bool] = Field(
        None,
        description="Filter featured series"
    )
    published_after: Optional[datetime] = Field(
        None,
        description="Filter by publication date (after)"
    )
    published_before: Optional[datetime] = Field(
        None,
        description="Filter by publication date (before)"
    )
    min_rating: Optional[float] = Field(
        None,
        ge=1.0,
        le=5.0,
        description="Minimum rating filter"
    )
    has_episodes: Optional[bool] = Field(
        None,
        description="Filter series with/without episodes"
    )
    is_complete: Optional[bool] = Field(
        None,
        description="Filter completed/ongoing series"
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


class SeriesSubscriptionCreate(BaseModel):
    """Series subscription creation model"""
    
    series_id: uuid.UUID = Field(..., description="Series ID to subscribe to")
    notification_enabled: bool = Field(
        True,
        description="Whether to send notifications for new episodes"
    )
    auto_download: bool = Field(
        False,
        description="Whether to auto-download episodes"
    )


class SeriesSubscriptionUpdate(BaseModel):
    """Series subscription update model"""
    
    status: Optional[SubscriptionStatus] = Field(
        None,
        description="Subscription status"
    )
    notification_enabled: Optional[bool] = Field(
        None,
        description="Whether to send notifications for new episodes"
    )
    auto_download: Optional[bool] = Field(
        None,
        description="Whether to auto-download episodes"
    )


class SeriesSubscriptionResponse(TimestampMixin):
    """Series subscription response model"""
    
    id: uuid.UUID = Field(..., description="Subscription ID")
    user_id: uuid.UUID = Field(..., description="Subscriber user ID")
    series_id: uuid.UUID = Field(..., description="Series ID")
    status: SubscriptionStatus = Field(..., description="Subscription status")
    notification_enabled: bool = Field(..., description="Notification preference")
    auto_download: bool = Field(..., description="Auto-download preference")
    last_watched_episode_id: Optional[uuid.UUID] = Field(
        None,
        description="Last watched episode ID"
    )
    watch_progress: Optional[Dict[str, Any]] = Field(
        None,
        description="User's watch progress data"
    )
    
    # Series information
    series: Optional[SeriesResponse] = Field(
        None,
        description="Series information"
    )


class SeriesListResponse(BaseModel):
    """Paginated series list response"""
    
    items: List[SeriesResponse] = Field(..., description="List of series for current page")
    total: int = Field(..., description="Total number of series matching the query")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Number of items per page")
    has_more: bool = Field(..., description="Whether there are more pages available")


class SeriesSubscriptionListResponse(PaginatedResponse[SeriesSubscriptionResponse]):
    """Paginated series subscription list response"""
    pass


# Series management request/response models

class SeriesPublishRequest(BaseModel):
    """Request model for publishing series"""
    
    publish_immediately: bool = Field(
        True,
        description="Whether to publish immediately or use scheduled_start_date"
    )
    scheduled_start_date: Optional[datetime] = Field(
        None,
        description="When to start the series (if not immediate)"
    )


class SeriesBulkUpdateRequest(BaseModel):
    """Request model for bulk series updates"""
    
    series_ids: List[uuid.UUID] = Field(
        ...,
        min_items=1,
        max_items=20,
        description="List of series IDs to update (max 20)"
    )
    updates: Dict[str, Any] = Field(
        ...,
        description="Updates to apply to all selected series"
    )


class SeriesAnalytics(BaseModel):
    """Series analytics model"""
    
    series_id: uuid.UUID = Field(..., description="Series ID")
    series_title: MultilingualText = Field(..., description="Series title")
    
    # Engagement metrics
    subscription_count: int = Field(0, description="Total subscriptions")
    total_views: int = Field(0, description="Total views across all episodes")
    total_likes: int = Field(0, description="Total likes")
    total_shares: int = Field(0, description="Total shares")
    total_comments: int = Field(0, description="Total comments")
    
    # Episode metrics
    episode_count: int = Field(0, description="Total episodes")
    average_episode_duration: Optional[float] = Field(None, description="Average episode duration")
    completion_rate: float = Field(0.0, description="Series completion rate percentage")
    
    # Rating metrics
    average_rating: Optional[float] = Field(None, description="Average rating")
    rating_count: int = Field(0, description="Number of ratings")
    
    # Performance metrics
    subscriber_retention_rate: float = Field(0.0, description="Subscriber retention rate")
    episode_drop_off_rate: float = Field(0.0, description="Episode drop-off rate")
    
    # Publication info
    published_at: Optional[datetime] = Field(None, description="Publication timestamp")
    
    # Category context
    category_name: Optional[MultilingualText] = Field(None, description="Category name")


class SeriesStatsResponse(BaseModel):
    """Response model for series statistics"""
    
    total_series: int = Field(..., description="Total series count")
    published_series: int = Field(..., description="Published series count")
    draft_series: int = Field(..., description="Draft series count")
    completed_series: int = Field(..., description="Completed series count")
    active_series: int = Field(..., description="Active series count")
    
    by_type: Dict[str, int] = Field(..., description="Series count by type")
    by_category: Dict[str, int] = Field(..., description="Series count by category")
    by_creator: Dict[str, int] = Field(..., description="Series count by creator")
    
    total_subscriptions: int = Field(..., description="Total subscriptions across all series")
    total_episodes: int = Field(..., description="Total episodes across all series")
    average_episodes_per_series: float = Field(..., description="Average episodes per series")
    
    generated_at: datetime = Field(..., description="When stats were generated")


class SeriesRecommendationRequest(BaseModel):
    """Request model for series recommendations"""
    
    user_id: Optional[uuid.UUID] = Field(
        None,
        description="User ID for personalized recommendations"
    )
    category_id: Optional[uuid.UUID] = Field(
        None,
        description="Category to base recommendations on"
    )
    series_type: Optional[SeriesType] = Field(
        None,
        description="Filter recommendations by series type"
    )
    exclude_subscribed: bool = Field(
        True,
        description="Exclude series user is already subscribed to"
    )
    limit: int = Field(
        10,
        ge=1,
        le=50,
        description="Number of recommendations to return"
    )


class SeriesRecommendationResponse(BaseModel):
    """Response model for series recommendations"""
    
    recommendations: List[SeriesResponse] = Field(
        ...,
        description="List of recommended series"
    )
    recommendation_reason: str = Field(
        ...,
        description="Reason for these recommendations"
    )
    generated_at: datetime = Field(
        ...,
        description="When recommendations were generated"
    )