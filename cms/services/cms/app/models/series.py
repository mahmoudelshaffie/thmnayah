"""
Series ORM Model

This module defines the SQLAlchemy ORM models for series management
with multilingual support, episode relationships, subscription management,
and extensible metadata.
"""

import uuid
from typing import Optional, Dict, Any, List
from sqlalchemy import (
    Column, String, Text, Boolean, Integer, Enum, Float,
    ForeignKey, Index, CheckConstraint, UniqueConstraint, 
    DateTime, UUID, Table
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, validates, mapped_column
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from datetime import datetime
import enum

from .base import Base, TimestampMixin, AuditMixin


class SeriesTypeEnum(str, enum.Enum):
    """Series type enumeration"""
    EDUCATIONAL = "EDUCATIONAL"
    ENTERTAINMENT = "ENTERTAINMENT"
    NEWS = "NEWS"
    PODCAST = "PODCAST"
    DOCUMENTARY = "DOCUMENTARY"
    TUTORIAL = "TUTORIAL"
    WEBINAR = "WEBINAR"


class SeriesStatusEnum(str, enum.Enum):
    """Series status enumeration"""
    DRAFT = "DRAFT"
    PENDING_REVIEW = "PENDING_REVIEW"
    PUBLISHED = "PUBLISHED"
    COMPLETED = "COMPLETED"
    PAUSED = "PAUSED"
    CANCELLED = "CANCELLED"
    ARCHIVED = "ARCHIVED"


class SeriesVisibilityEnum(str, enum.Enum):
    """Series visibility enumeration"""
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"
    RESTRICTED = "RESTRICTED"


class SubscriptionStatusEnum(str, enum.Enum):
    """Subscription status enumeration"""
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    CANCELLED = "CANCELLED"


# Association table for series-episodes relationship
series_episodes = Table(
    'series_episodes',
    Base.metadata,
    Column('series_id', UUID(as_uuid=True), ForeignKey('series.id'), primary_key=True),
    Column('content_id', UUID(as_uuid=True), ForeignKey('content.id'), primary_key=True),
    Column('episode_number', Integer, nullable=False),
    Column('season_number', Integer, nullable=True, default=1),
    Column('is_free', Boolean, default=True),
    Column('created_at', DateTime, default=datetime.utcnow),
    Column('updated_at', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
    Index('idx_series_episodes_series', 'series_id'),
    Index('idx_series_episodes_content', 'content_id'),
    Index('idx_series_episodes_number', 'series_id', 'episode_number'),
    UniqueConstraint('series_id', 'episode_number', name='uq_series_episode_number')
)


class Series(Base, TimestampMixin, AuditMixin):
    """
    Series ORM model for managing multilingual series content.
    
    Features:
    - Multilingual title/description support via JSON fields
    - Category relationships
    - Episode management and ordering
    - Publishing workflow and status management
    - Subscription tracking
    - SEO optimization fields
    - Analytics and engagement metrics
    - Extensible metadata
    """
    
    __tablename__ = "series"
    
    # Core series fields
    title = mapped_column(
        JSONB,
        nullable=False,
        comment="Series title in multiple languages (language_code -> text)"
    )
    
    description = mapped_column(
        JSONB,
        nullable=True,
        comment="Series description in multiple languages"
    )
    
    slug = mapped_column(
        JSONB,
        nullable=True,
        comment="URL-friendly slugs in multiple languages"
    )
    
    # Series classification
    series_type = mapped_column(
        Enum(SeriesTypeEnum),
        nullable=False,
        index=True,
        comment="Type of series (educational, entertainment, etc.)"
    )
    
    # Category relationship
    primary_category_id = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id"),
        nullable=True,
        index=True,
        comment="Primary category for this series"
    )
    
    # Creator/Author information
    creator_id = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
        comment="Series creator/author user ID"
    )
    
    creator_name = mapped_column(
        JSONB,
        nullable=True,
        comment="Creator name in multiple languages"
    )
    
    # Publishing and status management
    status = mapped_column(
        Enum(SeriesStatusEnum),
        nullable=False,
        default=SeriesStatusEnum.DRAFT,
        index=True,
        comment="Series publication status"
    )
    
    visibility = mapped_column(
        Enum(SeriesVisibilityEnum),
        nullable=False,
        default=SeriesVisibilityEnum.PUBLIC,
        index=True,
        comment="Series visibility level"
    )
    
    is_featured = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        comment="Whether series is featured"
    )
    
    # Publishing dates
    published_at = mapped_column(
        DateTime,
        nullable=True,
        index=True,
        comment="When series was published"
    )
    
    scheduled_start_date = mapped_column(
        DateTime,
        nullable=True,
        comment="Scheduled series start date"
    )
    
    expected_end_date = mapped_column(
        DateTime,
        nullable=True,
        comment="Expected series completion date"
    )
    
    actual_start_date = mapped_column(
        DateTime,
        nullable=True,
        comment="Actual series start date"
    )
    
    actual_end_date = mapped_column(
        DateTime,
        nullable=True,
        comment="Actual series end date"
    )
    
    # Series structure
    expected_episode_count = mapped_column(
        Integer,
        nullable=True,
        comment="Expected total number of episodes"
    )
    
    episode_count = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Current number of episodes"
    )
    
    season_count = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="Number of seasons"
    )
    
    release_schedule = mapped_column(
        String(255),
        nullable=True,
        comment="Release schedule description (e.g., 'Weekly on Mondays')"
    )
    
    # Media information
    thumbnail_url = mapped_column(
        String(1000),
        nullable=True,
        comment="URL to series thumbnail image"
    )
    
    banner_url = mapped_column(
        String(1000),
        nullable=True,
        comment="URL to series banner image"
    )
    
    trailer_url = mapped_column(
        String(1000),
        nullable=True,
        comment="URL to series trailer video"
    )
    
    # Engagement and analytics
    subscription_count = mapped_column(
        Integer,
        nullable=False,
        default=0,
        index=True,
        comment="Total number of subscriptions"
    )
    
    view_count = mapped_column(
        Integer,
        nullable=False,
        default=0,
        index=True,
        comment="Total series views (all episodes)"
    )
    
    like_count = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Total series likes"
    )
    
    share_count = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Total series shares"
    )
    
    comment_count = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Total series comments"
    )
    
    # Rating system
    rating = mapped_column(
        Float,
        nullable=True,
        comment="Average series rating (1-5 scale)"
    )
    
    rating_count = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of ratings"
    )
    
    # SEO optimization
    seo_title = mapped_column(
        JSONB,
        nullable=True,
        comment="SEO-optimized title in multiple languages"
    )
    
    seo_description = mapped_column(
        JSONB,
        nullable=True,
        comment="SEO meta description in multiple languages"
    )
    
    seo_keywords = mapped_column(
        JSONB,
        nullable=True,
        comment="SEO keywords/tags array"
    )
    
    # Flexible tagging and categorization
    tags = mapped_column(
        JSONB,
        nullable=True,
        comment="Series tags array"
    )
    
    # Extensible metadata
    _metadata = mapped_column(
        JSONB,
        nullable=True,
        comment="Additional series metadata"
    )
    
    # Relationships
    primary_category = relationship(
        "Category",
        back_populates="series",
        foreign_keys=[primary_category_id]
    )
    
    # creator = relationship(
    #     "User",
    #     back_populates="created_series"
    # )
    
    # episodes = relationship(
    #     "Content",
    #     secondary=series_episodes,
    #     back_populates="series",
    #     order_by="asc(series_episodes.c.episode_number)"
    # )
    
    subscriptions = relationship(
        "SeriesSubscription",
        back_populates="series",
        cascade="all, delete-orphan"
    )
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_series_creator_title', 'creator_id', 'title'),
        Index('idx_series_category_status', 'primary_category_id', 'status'),
        Index('idx_series_status_visibility', 'status', 'visibility'),
        Index('idx_series_published_featured', 'published_at', 'is_featured'),
        Index('idx_series_engagement', 'subscription_count', 'view_count'),
        CheckConstraint('episode_count >= 0', name='ck_series_episode_count_positive'),
        CheckConstraint('subscription_count >= 0', name='ck_series_subscription_count_positive'),
        CheckConstraint('view_count >= 0', name='ck_series_view_count_positive'),
        CheckConstraint('like_count >= 0', name='ck_series_like_count_positive'),
        CheckConstraint('rating >= 1.0 AND rating <= 5.0 OR rating IS NULL', name='ck_series_rating_range'),
        CheckConstraint('rating_count >= 0', name='ck_series_rating_count_positive'),
    )
    
    # Validation methods
    @validates('title')
    def validate_title(self, key, title):
        """Validate title has at least one language"""
        if not title or not isinstance(title, dict) or not any(title.values()):
            raise ValueError("Series must have title in at least one language")
        return title
    
    @validates('status')
    def validate_status_transition(self, key, status):
        """Validate status transitions"""
        if hasattr(self, 'status') and self.status:
            # Add status transition validation logic here
            pass
        return status
    
    @validates('episode_count', 'subscription_count', 'view_count', 'like_count', 'rating_count')
    def validate_positive_counts(self, key, value):
        """Validate counts are non-negative"""
        if value is not None and value < 0:
            raise ValueError(f"{key} must be non-negative")
        return value
    
    @validates('rating')
    def validate_rating_range(self, key, rating):
        """Validate rating is within valid range"""
        if rating is not None and not (1.0 <= rating <= 5.0):
            raise ValueError("Rating must be between 1.0 and 5.0")
        return rating
    
    # Hybrid properties for computed fields
    @hybrid_property
    def is_completed(self):
        """Check if series is completed"""
        return self.status == SeriesStatusEnum.COMPLETED
    
    @hybrid_property
    def is_published(self):
        """Check if series is published"""
        return self.status == SeriesStatusEnum.PUBLISHED
    
    @hybrid_property
    def is_active(self):
        """Check if series is active (published or paused)"""
        return self.status in [SeriesStatusEnum.PUBLISHED, SeriesStatusEnum.PAUSED]
    
    @hybrid_property
    def completion_percentage(self):
        """Calculate completion percentage"""
        if not self.expected_episode_count or self.expected_episode_count == 0:
            return None
        return min((self.episode_count / self.expected_episode_count) * 100, 100.0)
    
    @hybrid_property
    def average_rating(self):
        """Get average rating (alias for rating field)"""
        return self.rating
    
    @hybrid_property
    def total_engagement(self):
        """Calculate total engagement score"""
        return self.view_count + (self.like_count * 2) + (self.share_count * 3) + self.subscription_count
    
    # Note: We use _metadata for the column to avoid SQLAlchemy conflicts
    # Access via the _metadata attribute directly or through ORM serialization
    
    def __repr__(self):
        """String representation"""
        title_preview = str(self.title)[:50] if self.title else "No Title"
        return f"<Series(id={self.id}, title='{title_preview}', status={self.status})>"


class SeriesSubscription(Base, TimestampMixin):
    """
    Series subscription model for tracking user subscriptions to series.
    
    Features:
    - User subscription tracking
    - Notification preferences
    - Watch progress tracking
    - Subscription status management
    """
    
    __tablename__ = "series_subscriptions"
    
    # Core subscription fields
    user_id = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
        comment="Subscriber user ID"
    )
    
    series_id = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("series.id"),
        nullable=False,
        index=True,
        comment="Subscribed series ID"
    )
    
    status = mapped_column(
        Enum(SubscriptionStatusEnum),
        nullable=False,
        default=SubscriptionStatusEnum.ACTIVE,
        index=True,
        comment="Subscription status"
    )
    
    # Preferences
    notification_enabled = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether to send notifications for new episodes"
    )
    
    auto_download = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether to auto-download episodes"
    )
    
    # Watch progress tracking
    last_watched_episode_id = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("content.id"),
        nullable=True,
        comment="Last watched episode ID"
    )
    
    watch_progress = mapped_column(
        JSONB,
        nullable=True,
        comment="User's watch progress data (episode_id -> progress_data)"
    )
    
    # Subscription metrics
    subscription_source = mapped_column(
        String(100),
        nullable=True,
        comment="How user discovered and subscribed to series"
    )
    
    # Relationships
    # user = relationship("User", back_populates="series_subscriptions")
    series = relationship("Series", back_populates="subscriptions")
    # last_watched_episode = relationship("Content")
    
    # Table constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'series_id', name='uq_user_series_subscription'),
        Index('idx_subscription_user_status', 'user_id', 'status'),
        Index('idx_subscription_series_status', 'series_id', 'status'),
        Index('idx_subscription_notifications', 'notification_enabled', 'status'),
    )
    
    # Validation methods
    @validates('status')
    def validate_subscription_status(self, key, status):
        """Validate subscription status transitions"""
        if hasattr(self, 'status') and self.status:
            # Add status transition validation logic here
            pass
        return status
    
    def __repr__(self):
        """String representation"""
        return f"<SeriesSubscription(user_id={self.user_id}, series_id={self.series_id}, status={self.status})>"