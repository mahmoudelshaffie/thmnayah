"""
Content ORM Model

This module defines the SQLAlchemy ORM model for content management
with multilingual support, category relationships, and extensible metadata.
"""

import uuid
from typing import Optional, Dict, Any, List
from sqlalchemy import (
    Column, String, Text, Boolean, Integer, Enum,
    ForeignKey, Index, CheckConstraint, UniqueConstraint, 
    DateTime, UUID
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship, validates, mapped_column
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from datetime import datetime
import enum

from .base import Base, TimestampMixin, AuditMixin


class ContentTypeEnum(str, enum.Enum):
    """Content type enumeration"""
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"
    ARTICLE = "ARTICLE"
    DOCUMENT = "DOCUMENT"
    IMAGE = "IMAGE"
    LIVE_STREAM = "LIVE_STREAM"


class ContentStatusEnum(str, enum.Enum):
    """Content status enumeration"""
    DRAFT = "DRAFT"
    PENDING_REVIEW = "PENDING_REVIEW"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"
    DELETED = "DELETED"


class ContentVisibilityEnum(str, enum.Enum):
    """Content visibility enumeration"""
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"
    RESTRICTED = "RESTRICTED"


class Content(Base, TimestampMixin, AuditMixin):
    """
    Content ORM model for managing multilingual content.
    
    Features:
    - Multilingual title/description support via JSON fields
    - Category relationships with primary/secondary categorization
    - Content metadata and file information
    - SEO optimization fields
    - Publishing workflow and status management
    - Extensible metadata
    """
    
    __tablename__ = "content"
    
    # Core content fields
    title = mapped_column(
        JSONB,
        nullable=False,
        comment="Content title in multiple languages (language_code -> text)"
    )
    
    description = mapped_column(
        JSONB,
        nullable=True,
        comment="Content description in multiple languages"
    )
    
    body = mapped_column(
        JSONB,
        nullable=True,
        comment="Content body/text in multiple languages"
    )
    
    slug = mapped_column(
        JSONB,
        nullable=True,
        comment="URL-friendly slugs in multiple languages"
    )
    
    # Content classification
    content_type = mapped_column(
        Enum(ContentTypeEnum),
        nullable=False,
        index=True,
        comment="Type of content (video, audio, article, etc.)"
    )
    
    # Category relationship
    primary_category_id = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Primary category for this content"
    )
    
    # Status and visibility
    status = mapped_column(
        Enum(ContentStatusEnum),
        nullable=False,
        default=ContentStatusEnum.DRAFT,
        index=True,
        comment="Content publication status"
    )
    
    visibility = mapped_column(
        Enum(ContentVisibilityEnum),
        nullable=False,
        default=ContentVisibilityEnum.PUBLIC,
        index=True,
        comment="Content visibility level"
    )
    
    is_featured = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        comment="Whether content is featured"
    )
    
    # Publishing information
    published_at = mapped_column(
        DateTime,
        nullable=True,
        index=True,
        comment="Content publication timestamp"
    )
    
    scheduled_at = mapped_column(
        DateTime,
        nullable=True,
        index=True,
        comment="Scheduled publication timestamp"
    )
    
    expires_at = mapped_column(
        DateTime,
        nullable=True,
        index=True,
        comment="Content expiration timestamp"
    )
    
    # Author information
    author_id = mapped_column(
        PostgresUUID(as_uuid=True),
        # ForeignKey("users.id", ondelete="SET NULL"),  # Uncomment when users table exists
        nullable=True,
        index=True,
        comment="Content author user ID"
    )
    
    author_name = mapped_column(
        JSONB,
        nullable=True,
        comment="Author name in multiple languages"
    )
    
    # File and media information
    file_url = mapped_column(
        String(1000),
        nullable=True,
        comment="URL to main content file"
    )
    
    thumbnail_url = mapped_column(
        String(1000),
        nullable=True,
        comment="URL to content thumbnail image"
    )
    
    file_size = mapped_column(
        Integer,
        nullable=True,
        comment="File size in bytes"
    )
    
    file_type = mapped_column(
        String(100),
        nullable=True,
        comment="MIME type of the content file"
    )
    
    duration = mapped_column(
        Integer,
        nullable=True,
        comment="Content duration in seconds (for audio/video)"
    )
    
    # Engagement metrics (denormalized for performance)
    view_count = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Total number of views"
    )
    
    like_count = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Total number of likes"
    )
    
    share_count = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Total number of shares"
    )
    
    comment_count = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Total number of comments"
    )
    
    # Content quality and rating
    rating = mapped_column(
        Integer,
        nullable=True,
        comment="Content rating (1-5 scale)"
    )
    
    rating_count = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of ratings"
    )
    
    # SEO fields
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
    
    # Tags and categorization
    tags = mapped_column(
        JSONB,
        nullable=True,
        comment="Content tags array"
    )
    
    # Extensible metadata
    _metadata = mapped_column(
        JSONB,
        nullable=True,
        comment="Additional content metadata"
    )
    
    # Timestamps (inherited from TimestampMixin)
    # created_at, updated_at
    
    # Relationships
    primary_category = relationship(
        "Category",
        foreign_keys=[primary_category_id],
        back_populates="content"
    )
    
    # Many-to-many relationship with categories (for secondary categories)
    # This would be implemented via an association table in a full implementation
    
    # Database constraints
    __table_args__ = (
        # Ensure valid rating range
        CheckConstraint(
            'rating IS NULL OR (rating >= 1 AND rating <= 5)',
            name='check_valid_rating'
        ),
        
        # Ensure valid duration
        CheckConstraint(
            'duration IS NULL OR duration >= 0',
            name='check_valid_duration'
        ),
        
        # Ensure valid file size
        CheckConstraint(
            'file_size IS NULL OR file_size >= 0',
            name='check_valid_file_size'
        ),
        
        # Ensure published content has published_at timestamp
        CheckConstraint(
            "status != 'PUBLISHED' OR published_at IS NOT NULL",
            name='check_published_timestamp'
        ),
        
        # Ensure valid view count
        CheckConstraint(
            'view_count >= 0',
            name='check_valid_view_count'
        ),
        
        # Indexes for performance
        Index('idx_content_status_published', 'status', 'published_at'),
        Index('idx_content_category_status', 'primary_category_id', 'status'),
        Index('idx_content_type_visibility', 'content_type', 'visibility'),
        Index('idx_content_featured_published', 'is_featured', 'published_at'),
        Index('idx_content_author_status', 'author_id', 'status'),
        
        # JSON field indexes for multilingual search (PostgreSQL specific)
        Index('idx_content_title_gin', 'title', postgresql_using='gin'),
        Index('idx_content_description_gin', 'description', postgresql_using='gin'),
        Index('idx_content_tags_gin', 'tags', postgresql_using='gin'),
    )
    
    # Validation methods
    @validates('rating')
    def validate_rating(self, key, rating):
        """Ensure rating is within valid range"""
        if rating is not None and (rating < 1 or rating > 5):
            raise ValueError("Rating must be between 1 and 5")
        return rating
    
    @validates('duration')
    def validate_duration(self, key, duration):
        """Ensure duration is non-negative"""
        if duration is not None and duration < 0:
            raise ValueError("Duration must be non-negative")
        return duration
    
    @validates('file_size')
    def validate_file_size(self, key, file_size):
        """Ensure file size is non-negative"""
        if file_size is not None and file_size < 0:
            raise ValueError("File size must be non-negative")
        return file_size
    
    @validates('title')
    def validate_title(self, key, title):
        """Ensure at least one language is provided for title"""
        if not isinstance(title, dict) or not title:
            raise ValueError("Title must be a non-empty dictionary with language codes")
        # Ensure at least one language has content
        if not any(v.strip() for v in title.values() if isinstance(v, str)):
            raise ValueError("At least one language must have a non-empty title")
        return title
    
    @validates('status')
    def validate_status_transition(self, key, status):
        """Validate status transitions"""
        if hasattr(self, 'status') and self.status:
            current_status = self.status
            
            # Define valid status transitions
            valid_transitions = {
                ContentStatusEnum.DRAFT: [ContentStatusEnum.PENDING_REVIEW, ContentStatusEnum.ARCHIVED],
                ContentStatusEnum.PENDING_REVIEW: [ContentStatusEnum.PUBLISHED, ContentStatusEnum.DRAFT],
                ContentStatusEnum.PUBLISHED: [ContentStatusEnum.ARCHIVED],
                ContentStatusEnum.ARCHIVED: [ContentStatusEnum.DRAFT, ContentStatusEnum.DELETED],
                ContentStatusEnum.DELETED: []  # No transitions from deleted
            }
            
            if status not in valid_transitions.get(current_status, []):
                raise ValueError(f"Invalid status transition from {current_status} to {status}")
        
        return status
    
    # Hybrid properties for calculated fields
    @hybrid_property
    def is_published(self):
        """Check if content is published"""
        return self.status == ContentStatusEnum.PUBLISHED
    
    @hybrid_property
    def is_scheduled(self):
        """Check if content is scheduled for future publication"""
        return (self.scheduled_at is not None and 
                self.scheduled_at > datetime.utcnow() and 
                self.status == ContentStatusEnum.DRAFT)
    
    @hybrid_property
    def is_expired(self):
        """Check if content has expired"""
        return (self.expires_at is not None and 
                self.expires_at <= datetime.utcnow())
    
    @hybrid_property
    def average_rating(self):
        """Calculate average rating"""
        if self.rating_count == 0:
            return None
        return round(self.rating / self.rating_count, 2) if self.rating else None
    
    # Helper methods
    def get_title(self, language: str = 'ar', fallback: str = 'en') -> Optional[str]:
        """
        Get content title in specified language with fallback.
        
        Args:
            language: Preferred language code
            fallback: Fallback language code
            
        Returns:
            Content title in requested language or fallback
        """
        if not self.title:
            return None
        
        # Try preferred language
        if language in self.title and self.title[language]:
            return self.title[language]
        
        # Try fallback language
        if fallback in self.title and self.title[fallback]:
            return self.title[fallback]
        
        # Return any available language
        for lang_title in self.title.values():
            if lang_title:
                return lang_title
        
        return None
    
    def get_description(self, language: str = 'ar', fallback: str = 'en') -> Optional[str]:
        """Get content description with language fallback"""
        if not self.description:
            return None
        
        if language in self.description and self.description[language]:
            return self.description[language]
        
        if fallback in self.description and self.description[fallback]:
            return self.description[fallback]
        
        for desc in self.description.values():
            if desc:
                return desc
        
        return None
    
    def get_body(self, language: str = 'ar', fallback: str = 'en') -> Optional[str]:
        """Get content body with language fallback"""
        if not self.body:
            return None
        
        if language in self.body and self.body[language]:
            return self.body[language]
        
        if fallback in self.body and self.body[fallback]:
            return self.body[fallback]
        
        for body_text in self.body.values():
            if body_text:
                return body_text
        
        return None
    
    def get_slug(self, language: str = 'ar', fallback: str = 'en') -> Optional[str]:
        """Get content slug with language fallback"""
        if not self.slug:
            return None
        
        if language in self.slug and self.slug[language]:
            return self.slug[language]
        
        if fallback in self.slug and self.slug[fallback]:
            return self.slug[fallback]
        
        for slug in self.slug.values():
            if slug:
                return slug
        
        return None
    
    def publish(self):
        """Publish the content"""
        self.status = ContentStatusEnum.PUBLISHED
        if not self.published_at:
            self.published_at = datetime.utcnow()
    
    def archive(self):
        """Archive the content"""
        self.status = ContentStatusEnum.ARCHIVED
    
    def increment_view_count(self):
        """Increment view count"""
        self.view_count += 1
    
    def add_like(self):
        """Add a like to the content"""
        self.like_count += 1
    
    def add_share(self):
        """Add a share to the content"""
        self.share_count += 1
    
    def add_rating(self, rating_value: int):
        """
        Add a rating to the content.
        
        Args:
            rating_value: Rating value (1-5)
        """
        if not (1 <= rating_value <= 5):
            raise ValueError("Rating must be between 1 and 5")
        
        # Update average rating calculation
        if self.rating_count == 0:
            self.rating = rating_value
        else:
            total_rating = (self.rating or 0) * self.rating_count + rating_value
            self.rating = total_rating // (self.rating_count + 1)
        
        self.rating_count += 1
    
    def can_be_published(self) -> bool:
        """Check if content can be published"""
        required_fields = [self.title, self.content_type]
        return all(field is not None for field in required_fields)
    
    def get_content_summary(self, language: str = 'ar') -> Dict[str, Any]:
        """Get a summary of content information"""
        return {
            "id": self.id,
            "title": self.get_title(language),
            "description": self.get_description(language),
            "content_type": self.content_type.value,
            "status": self.status.value,
            "visibility": self.visibility.value,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "author_name": self.author_name.get(language) if self.author_name else None,
            "view_count": self.view_count,
            "rating": self.average_rating,
            "is_featured": self.is_featured,
            "thumbnail_url": self.thumbnail_url,
            "duration": self.duration,
            "primary_category_id": self.primary_category_id
        }
    
    def __repr__(self):
        title = self.get_title() if self.title else f"Content-{self.id}"
        return f"<Content(id={self.id}, title='{title}', type={self.content_type})>"
    
    def __str__(self):
        return self.get_title() or f"Content {self.id}"