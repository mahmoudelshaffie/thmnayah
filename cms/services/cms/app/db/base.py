"""
Database base classes and model imports.

This module provides:
- Declarative base class for SQLAlchemy models
- Model imports for Alembic autogenerate
- Database metadata configuration
"""

from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import declarative_base

# PostgreSQL naming convention for constraints
# This ensures consistent naming across migrations
POSTGRES_NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

# Create metadata with naming convention
metadata = MetaData(naming_convention=POSTGRES_NAMING_CONVENTION)

# Create declarative base class
Base = declarative_base(metadata=metadata)

# Import all models here so Alembic can detect them for autogenerate
# This is required for Alembic to automatically generate migrations

# Import models
from models.base import AuditMixin, TimestampMixin  # noqa: E402
from models.category import Category  # noqa: E402
# from models.user import User  # noqa: E402 - uncomment when user model exists
# from models.content import Content  # noqa: E402 - uncomment when content model exists
# from models.media import Media  # noqa: E402 - uncomment when media model exists
# from models.tag import Tag  # noqa: E402 - uncomment when tag model exists

# Export for easy imports
__all__ = [
    "Base",
    "metadata",
    "Category",
    # "User",
    # "Content", 
    # "Media",
    # "Tag",
]