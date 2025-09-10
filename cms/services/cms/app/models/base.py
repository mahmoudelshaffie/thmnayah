"""
Base SQLAlchemy models and mixins for the CMS application.

This module provides:
- Base declarative class for all models
- Timestamp mixin for created_at/updated_at fields
- Audit mixin for tracking user actions
- Common model utilities and patterns
"""

import uuid
from datetime import datetime
from typing import Any, Optional
from sqlalchemy import Column, Integer, DateTime, String, Boolean
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.orm import Session, mapped_column


class TimestampMixin:
    """
    Mixin to add timestamp fields to models.
    
    Provides:
    - created_at: Timestamp when record was created
    - updated_at: Timestamp when record was last modified
    """
    
    created_at = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        doc="Timestamp when the record was created"
    )
    
    updated_at = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        doc="Timestamp when the record was last updated"
    )


class AuditMixin:
    """
    Mixin to add audit fields to models.
    
    Provides:
    - created_by: User who created the record
    - updated_by: User who last modified the record
    - is_active: Soft delete flag
    - version: Optimistic locking version
    """
    
    created_by = mapped_column(
        PostgresUUID(as_uuid=True),
        nullable=True,  # Can be null for system-created records
        doc="ID of the user who created this record"
    )
    
    updated_by = mapped_column(
        PostgresUUID(as_uuid=True),
        nullable=True,
        doc="ID of the user who last updated this record"
    )
    
    is_active = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        doc="Soft delete flag - False means logically deleted"
    )
    
    version = mapped_column(
        Integer,
        default=1,
        nullable=False,
        doc="Version number for optimistic locking"
    )
    
    def soft_delete(self, user_id: Optional[uuid.UUID] = None):
        """
        Perform soft delete by setting is_active to False.
        
        Args:
            user_id: ID of the user performing the delete
        """
        self.is_active = False
        if user_id:
            self.updated_by = user_id
    
    def restore(self, user_id: Optional[uuid.UUID] = None):
        """
        Restore soft-deleted record by setting is_active to True.
        
        Args:
            user_id: ID of the user performing the restore
        """
        self.is_active = True
        if user_id:
            self.updated_by = user_id


@as_declarative()
class Base:
    """
    Base class for all SQLAlchemy models.
    
    Provides:
    - Automatic table naming
    - Common model utilities
    - Base fields and methods
    """

    __name__: str

    @declared_attr
    def __tablename__(cls) -> str:
        """Generate table name from class name."""
        return cls.__name__.lower()

    # Use UUID as primary key for better distributed systems support
    id = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        doc="Primary key UUID"
    )
    
    def to_dict(self, exclude: Optional[list] = None) -> dict:
        """
        Convert model instance to dictionary.
        
        Args:
            exclude: List of fields to exclude from the dictionary
            
        Returns:
            dict: Dictionary representation of the model
        """
        exclude = exclude or []
        result = {}
        
        for column in self.__table__.columns:
            if column.name not in exclude:
                value = getattr(self, column.name)
                # Handle UUID serialization
                if isinstance(value, uuid.UUID):
                    value = str(value)
                # Handle datetime serialization
                elif isinstance(value, datetime):
                    value = value.isoformat()
                result[column.name] = value
                
        return result
    
    def update_from_dict(self, data: dict, exclude: Optional[list] = None):
        """
        Update model instance from dictionary.
        
        Args:
            data: Dictionary with update data
            exclude: List of fields to exclude from update
        """
        exclude = exclude or ['id', 'created_at']  # Never update these
        
        for key, value in data.items():
            if key not in exclude and hasattr(self, key):
                setattr(self, key, value)
    
    @classmethod
    def get_by_id(cls, db: Session, model_id: uuid.UUID):
        """
        Get model instance by ID.
        
        Args:
            db: Database session
            model_id: ID to search for
            
        Returns:
            Model instance or None
        """
        return db.query(cls).filter(cls.id == model_id).first()
    
    @classmethod
    def get_active(cls, db: Session):
        """
        Get all active records (for models with AuditMixin).
        
        Args:
            db: Database session
            
        Returns:
            Query for active records
        """
        query = db.query(cls)
        if hasattr(cls, 'is_active'):
            query = query.filter(cls.is_active == True)
        return query
    
    def __repr__(self):
        """String representation of the model."""
        return f"<{self.__class__.__name__}(id={self.id})>"


# Export classes for easy importing
__all__ = [
    'Base',
    'TimestampMixin', 
    'AuditMixin'
]