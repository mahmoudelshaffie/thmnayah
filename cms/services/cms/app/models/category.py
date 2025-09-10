"""
Category ORM Model

This module defines the SQLAlchemy ORM model for hierarchical category management
with multilingual support, path indexing, and extensible metadata.
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


class CategoryTypeEnum(str, enum.Enum):
    """Category type enumeration"""
    TOPIC = "TOPIC"
    FORMAT = "FORMAT"
    AUDIENCE = "AUDIENCE"
    LANGUAGE = "LANGUAGE"
    SERIES_TYPE = "SERIES_TYPE"


class CategoryVisibilityEnum(str, enum.Enum):
    """Category visibility enumeration"""
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"
    RESTRICTED = "RESTRICTED"


class Category(Base, TimestampMixin, AuditMixin):
    """
    Category ORM model for hierarchical content organization.
    
    Features:
    - Hierarchical structure with parent-child relationships
    - Multilingual name/description support via JSON fields
    - Path indexing for efficient tree traversal
    - Content counting and statistics
    - SEO optimization fields
    - Extensible metadata
    """
    
    __tablename__ = "categories"
    
    # Multilingual fields stored as JSON
    name = mapped_column(
        JSONB,
        nullable=False,
        comment="Category name in multiple languages (language_code -> text)"
    )
    
    description = mapped_column(
        JSONB,
        nullable=True,
        comment="Category description in multiple languages"
    )
    
    slug = mapped_column(
        JSONB,
        nullable=True,
        comment="URL-friendly slugs in multiple languages"
    )
    
    # Category classification
    category_type = mapped_column(
        Enum(CategoryTypeEnum),
        nullable=False,
        default=CategoryTypeEnum.TOPIC,
        index=True,
        comment="Type of category (topic, format, audience, etc.)"
    )
    
    # Hierarchical structure
    parent_id = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Parent category for hierarchical structure"
    )
    
    level = mapped_column(
        Integer,
        nullable=False,
        default=0,
        index=True,
        comment="Hierarchy level (0 = root)"
    )
    
    path = mapped_column(
        String(1000),
        nullable=False,
        index=True,
        comment="Full hierarchical path (e.g., /sciences/technology)"
    )
    
    # Status and visibility
    is_active = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        comment="Whether category is active and visible"
    )
    
    visibility = mapped_column(
        Enum(CategoryVisibilityEnum),
        nullable=False,
        default=CategoryVisibilityEnum.PUBLIC,
        index=True,
        comment="Category visibility level"
    )
    
    # Display customization
    icon_url = mapped_column(
        String(500),
        nullable=True,
        comment="URL to category icon image"
    )
    
    banner_url = mapped_column(
        String(500),
        nullable=True,
        comment="URL to category banner image"
    )
    
    color_scheme = mapped_column(
        String(7),  # For hex colors like #FF0000
        nullable=True,
        comment="Category theme color (hex code)"
    )
    
    sort_order = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Sort order within parent category"
    )
    
    # Content statistics (denormalized for performance)
    content_count = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of direct content items"
    )
    
    subcategory_count = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of direct subcategories"
    )
    
    total_content_count = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Total content count including subcategories"
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
    
    # Extensible metadata
    _metadata = mapped_column(
        JSONB,
        nullable=True,
        comment="Additional category metadata"
    )
    
    # Timestamps (inherited from Base)
    # created_at, updated_at
    
    # Relationships
    parent = relationship(
        "Category",
        remote_side="Category.id",
        back_populates="children"
    )
    
    children = relationship(
        "Category",
        back_populates="parent",
        cascade="all, delete-orphan",
        order_by="Category.sort_order, Category.name"
    )
    
    # Content relationship
    content = relationship(
        "Content", 
        back_populates="primary_category"
    )
    
    # Series relationship
    series = relationship(
        "Series",
        back_populates="primary_category",
        foreign_keys="Series.primary_category_id"
    )
    
    # Database constraints
    __table_args__ = (
        # Ensure no self-referencing parent
        CheckConstraint(
            'id != parent_id',
            name='check_no_self_parent'
        ),
        
        # Ensure level consistency
        CheckConstraint(
            'level >= 0',
            name='check_valid_level'
        ),
        
        # Ensure path starts with /
        CheckConstraint(
            "path LIKE '/%'",
            name='check_path_format'
        ),
        
        # Ensure color scheme format (if provided)
        CheckConstraint(
            "color_scheme IS NULL OR color_scheme ~ '^#[0-9A-Fa-f]{6}$'",
            name='check_color_scheme_format'
        ),
        
        # Unique slug per language per parent
        # Note: This would need a custom implementation due to JSON fields
        
        # Indexes for performance
        Index('idx_category_parent_level', 'parent_id', 'level'),
        Index('idx_category_type_active', 'category_type', 'is_active'),
        Index('idx_category_path_prefix', 'path', postgresql_ops={'path': 'text_pattern_ops'}),
        Index('idx_category_visibility_active', 'visibility', 'is_active'),
        
        # JSON field indexes for multilingual search (PostgreSQL specific)
        Index('idx_category_name_gin', 'name', postgresql_using='gin'),
        Index('idx_category_description_gin', 'description', postgresql_using='gin'),
    )
    
    # Validation methods
    @validates('level')
    def validate_level(self, key, level):
        """Ensure level is non-negative"""
        if level < 0:
            raise ValueError("Level must be non-negative")
        return level
    
    @validates('color_scheme')
    def validate_color_scheme(self, key, color):
        """Validate hex color format"""
        if color is not None:
            import re
            if not re.match(r'^#[0-9A-Fa-f]{6}$', color):
                raise ValueError("Color scheme must be a valid hex color (e.g., #FF0000)")
        return color
    
    @validates('path')
    def validate_path(self, key, path):
        """Ensure path format is correct"""
        if not path.startswith('/'):
            raise ValueError("Path must start with /")
        return path
    
    @validates('name')
    def validate_name(self, key, name):
        """Ensure at least one language is provided for name"""
        if not isinstance(name, dict) or not name:
            raise ValueError("Name must be a non-empty dictionary with language codes")
        # Ensure at least one language has content
        if not any(v.strip() for v in name.values() if isinstance(v, str)):
            raise ValueError("At least one language must have a non-empty name")
        return name
    
    # Hybrid properties for calculated fields
    @hybrid_property
    def is_root(self):
        """Check if this is a root category (no parent)"""
        return self.parent_id is None
    
    @hybrid_property
    def is_leaf(self):
        """Check if this is a leaf category (no children)"""
        return self.subcategory_count == 0
    
    # Helper methods
    def get_name(self, language: str = 'ar', fallback: str = 'en') -> Optional[str]:
        """
        Get category name in specified language with fallback.
        
        Args:
            language: Preferred language code
            fallback: Fallback language code
            
        Returns:
            Category name in requested language or fallback
        """
        if not self.name:
            return None
        
        # Try preferred language
        if language in self.name and self.name[language]:
            return self.name[language]
        
        # Try fallback language
        if fallback in self.name and self.name[fallback]:
            return self.name[fallback]
        
        # Return any available language
        for lang_name in self.name.values():
            if lang_name:
                return lang_name
        
        return None
    
    def get_description(self, language: str = 'ar', fallback: str = 'en') -> Optional[str]:
        """Get category description with language fallback"""
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
    
    def get_slug(self, language: str = 'ar', fallback: str = 'en') -> Optional[str]:
        """Get category slug with language fallback"""
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
    
    def build_path(self) -> str:
        """
        Build hierarchical path based on parent chain.
        This should be called when parent changes.
        """
        if self.parent is None:
            # Root category - use primary language slug or name
            slug = self.get_slug() or self.get_name()
            if slug:
                return f"/{slug.lower().replace(' ', '-')}"
            return f"/category-{self.id}"
        
        # Build path from parent path + current slug
        parent_path = self.parent.path
        current_slug = self.get_slug() or self.get_name()
        if current_slug:
            return f"{parent_path}/{current_slug.lower().replace(' ', '-')}"
        return f"{parent_path}/category-{self.id}"
    
    def update_statistics(self):
        """Update denormalized statistics (content counts, subcategory count)"""
        # This would be implemented in the service layer
        # to update content_count, subcategory_count, total_content_count
        pass
    
    def get_ancestors(self) -> List['Category']:
        """Get all ancestor categories up to root"""
        ancestors = []
        current = self.parent
        while current:
            ancestors.append(current)
            current = current.parent
        return ancestors
    
    def get_full_path_names(self, language: str = 'ar') -> List[str]:
        """Get full path as list of category names"""
        path_names = []
        for ancestor in reversed(self.get_ancestors()):
            path_names.append(ancestor.get_name(language) or str(ancestor.id))
        path_names.append(self.get_name(language) or str(self.id))
        return path_names
    
    def __repr__(self):
        name = self.get_name() if self.name else f"Category-{self.id}"
        return f"<Category(id={self.id}, name='{name}', level={self.level})>"
    
    def __str__(self):
        return self.get_name() or f"Category {self.id}"